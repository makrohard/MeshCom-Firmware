#!/usr/bin/env python3
"""PR3a A/B under stock Espressif QEMU: does the net console open on a non-WiFi IP network?

  qemu-netconsole.py IMAGE TAG

The emulator has no WiFi; the overlay brings up OpenETH and sets node_hasIPaddress. The images
are built WITHOUT the overlay's own net-console hunk, so upstream's gate decides alone.
Pass = the console answers --info; also scans the UART for panics/asserts.
"""
import os, shutil, socket, subprocess, sys, time

IMG, TAG = sys.argv[1], sys.argv[2]
EV = "/home/makro/claude/meshcom-prs-evidence/all-envs/qemu"
QEMU = "/home/makro/claude/qemu-cache-pr/b-up/qemu-system-xtensa"   # claude-aa's stock build, read-only
W = f"{EV}/qemu-nc-{TAG}"; PORT = 22354
shutil.rmtree(W, ignore_errors=True); os.makedirs(W)
FLASH = f"{W}/flash.bin"; shutil.copy(IMG, FLASH); UART = f"{W}/uart.log"
LOG = open(f"{W}/proof.log", "w")


def log(m):
    l = time.strftime("%H:%M:%S ") + m; print(l, flush=True); LOG.write(l + "\n"); LOG.flush()


def uart():
    try: return open(UART, "rb").read().decode("utf-8", "replace")
    except FileNotFoundError: return ""


def console(cmd, wait=4.0):
    try: s = socket.create_connection(("127.0.0.1", PORT), timeout=3)
    except OSError as e: return None
    s.sendall((cmd + "\r\n").encode()); s.settimeout(0.5); buf, end = b"", time.time() + wait
    while time.time() < end:
        try:
            c = s.recv(4096)
            if not c: break
            buf += c
        except socket.timeout: pass
        except OSError: break          # reset by peer = no listener in the guest
    s.close(); return buf.decode("utf-8", "replace")


q = subprocess.Popen([QEMU, "-nographic", "-machine", "esp32", "-m", "4M",
    "-drive", f"file={FLASH},if=mtd,format=raw",
    "-nic", f"user,model=open_eth,host=10.0.2.5,guestfwd=tcp:10.0.2.2:7000-cmd:true,hostfwd=tcp:127.0.0.1:{PORT}-:2323",
    "-global", "driver=timer.esp32.timg,property=wdt_disable,value=true",
    "-serial", f"file:{UART}", "-serial", "null", "-serial", "null", "-monitor", "none"],
    stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
log(f"{TAG}: qemu pid {q.pid}, image {IMG}")
try:
    t0 = time.time()
    while time.time() - t0 < 240 and "OpenETH connect OK" not in uart():
        time.sleep(1)
    log(f"network up: {'OpenETH connect OK' in uart()} after {time.time()-t0:.0f} s; "
        f"console init line: {'HMAC console init' in uart()}")
    answered, t1 = None, time.time()
    while time.time() - t1 < 180:
        r = console("--info")
        if r and "MeshCom" in r:
            answered = time.time() - t1; break
        time.sleep(5)
    log(f"console --info answered: {'yes after %.0f s' % answered if answered is not None else 'NO within 180 s'}")
    bad = [l for l in uart().splitlines() if "Guru Meditation" in l or "assert" in l.lower() or "abort()" in l]
    log(f"panic/assert lines in UART: {len(bad)} {bad[:2]}")
finally:
    q.terminate()
    try: q.wait(10)
    except subprocess.TimeoutExpired: q.kill()
    log(f"qemu pid {q.pid} stopped")
