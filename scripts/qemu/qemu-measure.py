#!/usr/bin/env python3
"""Step-1 measurement for PR3b-e: boot one emulator image for SECONDS and report what works.

  qemu-measure.py IMAGE TAG [SECONDS]

Virtual GPS: valid_fix.nmea is fed into UART1 from the start (as the LHPC harness does).
Reports: setup finished (CLIENT STARTED), network (OpenETH connect OK), console --info, GPS detected,
panic/assert lines, and the last UART lines (to locate a hang).
"""
import os, shutil, socket, subprocess, sys, time

IMG, TAG = sys.argv[1], sys.argv[2]; SECS = int(sys.argv[3]) if len(sys.argv) > 3 else 150
EV = "/home/makro/claude/meshcom-prs-evidence/all-envs/qemu"
QEMU = "/home/makro/claude/qemu-cache-pr/b-up/qemu-system-xtensa"   # claude-aa's stock build, read-only
RELAY = "/home/makro/claude/meshcom-qemu-raspi/scripts/gps-relay.py"
FIX = "/home/makro/claude/meshcom-qemu-raspi/fixtures/gps/valid_fix.nmea"
W = f"{EV}/qemu-m-{TAG}"; PORT = 22356
shutil.rmtree(W, ignore_errors=True); os.makedirs(f"{W}/.run")
FLASH = f"{W}/flash.bin"; shutil.copy(IMG, FLASH); UART = f"{W}/uart.log"; SOCK = f"{W}/.run/gps-uart1.sock"


def uart():
    try: return open(UART, "rb").read().decode("utf-8", "replace")
    except FileNotFoundError: return ""


def console(cmd, wait=4.0):
    try: s = socket.create_connection(("127.0.0.1", PORT), timeout=3)
    except OSError: return None
    s.sendall((cmd + "\r\n").encode()); s.settimeout(0.5); buf, end = b"", time.time() + wait
    while time.time() < end:
        try:
            c = s.recv(4096)
            if not c: break
            buf += c
        except socket.timeout: pass
        except OSError: break
    s.close(); return buf.decode("utf-8", "replace")


q = subprocess.Popen([QEMU, "-nographic", "-machine", "esp32", "-m", "4M",
    "-drive", f"file={FLASH},if=mtd,format=raw",
    "-nic", f"user,model=open_eth,host=10.0.2.5,guestfwd=tcp:10.0.2.2:7000-cmd:true,hostfwd=tcp:127.0.0.1:{PORT}-:2323",
    "-global", "driver=timer.esp32.timg,property=wdt_disable,value=true",
    "-serial", f"file:{UART}",
    "-chardev", f"socket,id=gps1,path={SOCK},server=on,wait=off", "-serial", "chardev:gps1",
    "-serial", "null", "-monitor", "none"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
time.sleep(2)
relay = subprocess.Popen(["python3", RELAY, "--mode", "fixture", "--uart", SOCK, "--fixture", FIX, "--loop"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
t0 = time.time(); answered = None
try:
    while time.time() - t0 < SECS:
        if answered is None and "CLIENT STARTED" in uart():
            r = console("--info")
            if r and "MeshCom" in r: answered = time.time() - t0
        time.sleep(3)
    u = uart(); lines = [l for l in u.splitlines() if l.strip()]
    pos = console("--pos") or ""
    rep = {
        "setup finished": "CLIENT STARTED" in u,
        "network up": "OpenETH connect OK" in u,
        "console answered": f"after {answered:.0f} s" if answered is not None else "NO",
        "GPS lines": [l[:80] for l in lines if l.startswith("[GPS")][:3],
        "position via --pos": " ".join(l.strip() for l in pos.splitlines() if "LAT" in l)[:60],
        "panic/assert": [l[:90] for l in lines if "Guru" in l or "assert" in l.lower() or "abort()" in l or "Backtrace" in l][:3],
        "reboots (rst:)": u.count("rst:"),
        "last lines": [l[:100] for l in lines[-4:]],
    }
    with open(f"{W}/result.txt", "w") as f:
        for k, v in rep.items(): f.write(f"{k}: {v}\n")
    print(f"=== {TAG}"); print(open(f"{W}/result.txt").read())
finally:
    relay.terminate(); q.terminate()
    try: q.wait(10)
    except subprocess.TimeoutExpired: q.kill()
