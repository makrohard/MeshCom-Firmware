#!/usr/bin/env python3
"""lhpc-speed carry proof under QEMU: the two speed PRs still behave as proven.

  proof.py p1       IMAGE   PR1: counter, GPS fix and --aprsmc survive a hard power-off
  proof.py setcall  IMAGE   PR2 (image built with testhack-short.py): unchanged --setcall

Environment: QEMU (qemu-system-xtensa), RELAY (meshcom-qemu-raspi scripts/gps-relay.py),
FIX (fixtures/gps/valid_fix.nmea), WORK (scratch dir). Prints PASS/FAIL lines, exits 1 on any FAIL.
"""
import os, shutil, socket, subprocess, sys, tempfile, time

MODE, IMG = sys.argv[1], sys.argv[2]
QEMU, RELAY, FIX = os.environ["QEMU"], os.environ["RELAY"], os.environ["FIX"]
W = os.path.join(os.environ.get("WORK", "/tmp/lhpc-speed-proof"), MODE)
HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 22330
shutil.rmtree(W, ignore_errors=True); os.makedirs(W)
FLASH = f"{W}/flash.bin"; shutil.copy(IMG, FLASH)
SOCK = os.path.join(tempfile.mkdtemp(prefix="lhpc-"), "gps.sock")     # UNIX socket paths are limited to 107 bytes
fails = []


def log(m): print(time.strftime("%H:%M:%S ") + m, flush=True)


def check(ok, what):
    log(("PASS " if ok else "FAIL ") + what)
    if not ok: fails.append(what)


def uart(p):
    try: return open(p, "rb").read().decode("utf-8", "replace")
    except FileNotFoundError: return ""


def console(cmd, wait=5.0):
    try: s = socket.create_connection(("127.0.0.1", PORT), timeout=3)
    except OSError: return ""
    s.sendall((cmd + "\r\n").encode()); s.settimeout(0.5); buf, end = b"", time.time() + wait
    while time.time() < end:
        try:
            c = s.recv(4096)
            if not c: break
            buf += c
        except socket.timeout: pass
        except OSError: break
    s.close(); return buf.decode("utf-8", "replace")


def nvs(*keys):
    out = subprocess.run([sys.executable, f"{HERE}/nvsdump.py", FLASH, *keys], capture_output=True, text=True).stdout
    return dict(l.split("=", 1) for l in out.split())


def boot(n, gps):
    u = f"{W}/uart-{n}.log"
    if os.path.exists(SOCK): os.unlink(SOCK)
    q = subprocess.Popen([QEMU, "-nographic", "-machine", "esp32", "-m", "4M",
        "-drive", f"file={FLASH},if=mtd,format=raw",
        "-nic", f"user,model=open_eth,hostfwd=tcp:127.0.0.1:{PORT}-:2323",
        "-global", "driver=timer.esp32.timg,property=wdt_disable,value=true",
        "-serial", f"file:{u}",
        "-chardev", f"socket,id=gps1,path={SOCK},server=on,wait=off", "-serial", "chardev:gps1",
        "-serial", "null", "-monitor", "none"],
        stdin=subprocess.DEVNULL, stdout=open(f"{W}/qemu-{n}.log", "wb"), stderr=subprocess.STDOUT)
    r = None
    if gps:
        time.sleep(2)
        r = subprocess.Popen([sys.executable, RELAY, "--mode", "fixture", "--uart", SOCK, "--fixture", FIX, "--loop"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time(); up = False
    while time.time() - t0 < 600 and q.poll() is None:
        if "MeshCom" in console("--info", 3): up = True; break
        time.sleep(3)
    log(f"boot {n}: console {'up after %.0f s' % (time.time() - t0) if up else 'NOT up'}")
    if not up:
        log("QEMU: " + open(f"{W}/qemu-{n}.log", errors="replace").read()[-500:])
        stop(q, r); log(f"RESULT {MODE}: FAIL (boot {n})"); sys.exit(1)
    return q, r, u, up


def stop(q, r):
    if r: r.terminate()
    q.kill(); q.wait()          # hard power-off


if MODE == "p1":
    q, r, u, up = boot(1, True); check(up, "boot 1 console answers")
    console("--setcall TE5T-1", 5); time.sleep(40)
    pos, t0 = "", time.time()
    while time.time() - t0 < 300:
        pos = console("--pos", 5)
        if "LAT: 48.0000" in pos: break
        time.sleep(5)
    check("LAT: 48.0000" in pos, "GPS fix reaches RAM")
    time.sleep(5)
    check(nvs("node_lat").get("node_lat") == "48.0", "GPS fix saved to flash before any transmission")
    for i in (1, 2, 3):
        console(f"::carry text {i}", 5); time.sleep(15)
    console("--aprsmc DL0ABC", 3); time.sleep(3)
    stop(q, r)
    a = nvs("node_msgid", "node_aprsmc")
    check(a.get("node_aprsmc") == "DL0ABC", "--aprsmc survives a hard power-off right after the command")
    q, r, u, up = boot(2, False); check(up, "boot 2 console answers")
    pos = console("--pos", 5)
    check("LAT: 48.0000" in pos, "boot 2 (no GPS) starts from the saved fix")
    console("::carry text 4", 5); time.sleep(15)
    stop(q, r)
    b = nvs("node_msgid")
    check(int(b.get("node_msgid", "-1")) > int(a.get("node_msgid", "0")) > 0,
          f"message counter persisted and keeps counting ({a.get('node_msgid')} -> {b.get('node_msgid')})")

elif MODE == "setcall":
    MARK = "auto-reboot suppressed"

    def setcall(u):
        before = uart(u).count(MARK)
        console("--setcall TE5T-1", 5); time.sleep(40)
        return uart(u).count(MARK) > before

    q, r, u, up = boot(1, False); check(up, "boot 1 console answers")
    check(setcall(u), "new callsign: saved and reboot scheduled")
    stop(q, r)
    q, r, u, up = boot(2, False); check(up, "boot 2 console answers")
    check(nvs("node_short").get("node_short") == "CUST5", "test step left a custom short in flash")
    check(setcall(u), "same callsign, custom short in flash: saved and reboot scheduled")
    check(not setcall(u), "same callsign again (no-op): no reboot")
    stop(q, r)
    check(nvs("node_short").get("node_short") == "E5T40", "derived short saved")

log(f"RESULT {MODE}: {'FAIL' if fails else 'PASS'} ({len(fails)} failed)")
sys.exit(1 if fails else 0)
