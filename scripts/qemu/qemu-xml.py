#!/usr/bin/env python3
"""PR1 XML UTC-offset proof under stock Espressif QEMU.

  qemu-xml.py IMAGE TAG

Images carry TEST-ONLY scaffolding (never in a PR): console command "--xmltz <+HH:MM>" feeds Kurt's own
(commented-out upstream) station XML with that timezone into the real decodeTinyXML(); built with
-D ENABLE_XML (the only upstream board with it is E22_XML-DevKitC) and a stub testTinyXML().
Sequence: boot, read node_utcof; --xmltz +03:30; hard power-off 3 s later (no transmission);
read NVS; boot again and read --info (UTC-OFF).
"""
import os, re, shutil, socket, subprocess, sys, time

IMG, TAG = sys.argv[1], sys.argv[2]
EV = "/home/makro/claude/meshcom-prs-evidence/all-envs/qemu"
QEMU = "/home/makro/claude/qemu-cache-pr/b-up/qemu-system-xtensa"
W = f"{EV}/qemu-xml-{TAG}"; PORT = 22358
shutil.rmtree(W, ignore_errors=True); os.makedirs(W)
FLASH = f"{W}/flash.bin"; shutil.copy(IMG, FLASH)
LOG = open(f"{W}/proof.log", "w")


def log(m):
    l = time.strftime("%H:%M:%S ") + m; print(l, flush=True); LOG.write(l + "\n"); LOG.flush()


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


def nvs():
    return " ".join(subprocess.run(["python3", "/home/makro/claude/agent5-allenvs/qemu/nvsdump.py", FLASH, "node_utcof", "node_msgid"],
                                   capture_output=True, text=True).stdout.split())


def boot(n):
    q = subprocess.Popen([QEMU, "-nographic", "-machine", "esp32", "-m", "4M",
        "-drive", f"file={FLASH},if=mtd,format=raw",
        "-nic", f"user,model=open_eth,host=10.0.2.5,guestfwd=tcp:10.0.2.2:7000-cmd:true,hostfwd=tcp:127.0.0.1:{PORT}-:2323",
        "-global", "driver=timer.esp32.timg,property=wdt_disable,value=true",
        "-serial", f"file:{W}/uart-{n}.log", "-serial", "null", "-serial", "null", "-monitor", "none"],
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    t0 = time.time()
    while time.time() - t0 < 300:
        r = console("--info", 3)
        if r and "MeshCom" in r:
            log(f"boot {n}: console up after {time.time()-t0:.0f} s; UTC-OFF " +
                (re.search(r"UTC-OFF ([-0-9.]+)", r).group(1) if re.search(r"UTC-OFF ([-0-9.]+)", r) else "?"))
            return q
        time.sleep(3)
    log(f"boot {n}: console not up"); return q


q = boot(1)
r = console("--xmltz +03:30", 6) or ""
log("xmltz reply: " + " ".join(l.strip() for l in r.splitlines() if "[TEST]" in l))
time.sleep(3)
q.kill(); q.wait()
log("NVS after hard power-off 3 s later: " + nvs())
q = boot(2)
q.kill(); q.wait()
log("done")
