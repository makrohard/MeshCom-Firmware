#!/usr/bin/env python3
"""PR1 proof under stock Espressif QEMU (virtual GPS fed from the start).

  qemu-p1.py IMAGE TAG

boot 1 (GPS on): set callsign; wait for the GPS fix; send 3 texts (measure the loop gap after each);
                 then --aprsmc DL0ABC and power off at once (no transmission in between).
                 Read NVS: counter, position, aprsmc.
boot 2 (no GPS): position the node starts with (--pos); send 1 text; power off; counter must continue.
"""
import os, re, shutil, socket, subprocess, sys, time

IMG, TAG = sys.argv[1], sys.argv[2]
EV = "/home/makro/claude/meshcom-prs-evidence/all-envs/qemu"
QEMU = "/home/makro/claude/qemu-cache-pr/b-up/qemu-system-xtensa"   # claude-aa's stock build, read-only
RELAY = "/home/makro/claude/meshcom-qemu-raspi/scripts/gps-relay.py"
FIX = "/home/makro/claude/meshcom-qemu-raspi/fixtures/gps/valid_fix.nmea"
W = f"{EV}/qemu-p1-{TAG}"; PORT = 22357
shutil.rmtree(W, ignore_errors=True); os.makedirs(f"{W}/.run")
FLASH = f"{W}/flash.bin"; shutil.copy(IMG, FLASH); SOCK = f"{W}/.run/gps-uart1.sock"
LOG = open(f"{W}/proof.log", "w")


def log(m):
    l = time.strftime("%H:%M:%S ") + m; print(l, flush=True); LOG.write(l + "\n"); LOG.flush()


def uart(p):
    try: return open(p, "rb").read().decode("utf-8", "replace")
    except FileNotFoundError: return ""


def console(cmd, wait=5.0):
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


def nvs(*keys):
    return subprocess.run(["python3", "/home/makro/claude/agent5-allenvs/qemu/nvsdump.py", FLASH, *keys], capture_output=True, text=True).stdout.split()


def boot(n, gps):
    u = f"{W}/uart-{n}.log"
    if os.path.exists(SOCK): os.unlink(SOCK)
    q = subprocess.Popen([QEMU, "-nographic", "-machine", "esp32", "-m", "4M",
        "-drive", f"file={FLASH},if=mtd,format=raw",
        "-nic", f"user,model=open_eth,host=10.0.2.5,guestfwd=tcp:10.0.2.2:7000-cmd:true,hostfwd=tcp:127.0.0.1:{PORT}-:2323",
        "-global", "driver=timer.esp32.timg,property=wdt_disable,value=true",
        "-serial", f"file:{u}",
        "-chardev", f"socket,id=gps1,path={SOCK},server=on,wait=off", "-serial", "chardev:gps1",
        "-serial", "null", "-monitor", "none"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    r = None
    if gps:
        time.sleep(2)
        r = subprocess.Popen(["python3", RELAY, "--mode", "fixture", "--uart", SOCK, "--fixture", FIX, "--loop"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    while time.time() - t0 < 300:
        x = console("--info", 3)
        if x and "MeshCom" in x: break
        time.sleep(3)
    log(f"boot {n} (gps={gps}): console up after {time.time()-t0:.0f} s")
    return q, r, u


def stop(q, r):
    if r: r.terminate()
    q.kill(); q.wait()          # hard power-off: no shutdown path


def gaps_after(u, start):
    g = [int(x) for x in re.findall(r"gap ms (\d+)", uart(u)[start:])]
    return max(g) if g else 0


q, r, u = boot(1, True)
console("--setcall TE5T-1", 5); time.sleep(20)
t0 = time.time(); pos = ""
while time.time() - t0 < 120:
    pos = console("--pos", 5) or ""
    if "LAT: 48.0000" in pos: break
    time.sleep(5)
log("GPS fix in RAM: " + " ".join(l.strip() for l in pos.splitlines() if "LAT" in l)[:60])
time.sleep(5)
log("NVS right after the fix (before any text): " + " ".join(nvs("node_lat", "node_msgid")))
for i in (1, 2, 3):
    mark = len(uart(u)); console(f"::p1 text {i}", 5); time.sleep(15)
    log(f"text {i}: largest loop gap after it: {gaps_after(u, mark)} ms")
console("--aprsmc DL0ABC", 3); time.sleep(3)
stop(q, r)
log("NVS after hard power-off (aprsmc set 3 s before): " + " ".join(nvs("node_msgid", "node_lat", "node_lon", "node_aprsmc")))

q, r, u = boot(2, False)
pos = console("--pos", 5) or ""
log("boot 2 start position (no GPS): " + " ".join(l.strip() for l in pos.splitlines() if "LAT" in l)[:60])
console("::p1 text 4", 5); time.sleep(15)
stop(q, r)
log("NVS after boot 2: " + " ".join(nvs("node_msgid", "node_lat", "node_aprsmc")))
log("done")
