#!/usr/bin/env python3
"""Gate-2 F1 regression under QEMU: is a text hop limit received in {SET} kept across a hard power-off?

  qemu-sethop.py IMAGE TAG

The {SET} text goes through the real handler: --injectmsg (upstream test hook; the console command exists only in
INSTRUMENT_ENABLED builds, command_functions.cpp `#if INSTRUMENT_ENABLED` at line 5025, so use the `instr` images) queues it into the same deferred display path a received LoRa text takes, which reaches sendDisplayText().
Phase A (no transmission in between): out-of-range {SET}44 and unchanged {SET}4 leave the value alone;
{SET}2 sets it; hard power-off; NVS and the value after reboot.
Phase B (the auditor's case, fresh flash): {SET}2, one text transmission, hard power-off, NVS.
Logs to meshcom-prs-evidence/qemu-sethop-TAG/.
"""
import os, re, shutil, socket, subprocess, sys, tempfile, time

IMG, TAG = sys.argv[1], sys.argv[2]
EV = "/home/makro/claude/meshcom-prs-evidence/all-envs/qemu"
QEMU = "/home/makro/claude/qemu-cache-pr/b-up/qemu-system-xtensa"   # claude-aa's stock build, read-only
NVS = "/home/makro/claude/agent5-allenvs/qemu/nvsdump-ci.py"
W = f"{EV}/qemu-sethop-{TAG}"; PORT = 22361
shutil.rmtree(W, ignore_errors=True); os.makedirs(W)
LOG = open(f"{W}/proof.log", "w")
SOCK = os.path.join(tempfile.mkdtemp(prefix="sh-"), "gps.sock")


def log(m):
    l = time.strftime("%H:%M:%S ") + m; print(l, flush=True); LOG.write(l + "\n"); LOG.flush()


def uart(u):
    try: return open(u, "rb").read().decode("utf-8", "replace")
    except FileNotFoundError: return ""


def console(cmd, wait=4.0):
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


def nvs(flash, *keys):
    out = subprocess.run([sys.executable, NVS, flash, *keys], capture_output=True, text=True).stdout
    return dict(l.split("=", 1) for l in out.split())


def boot(flash, u):
    if os.path.exists(SOCK): os.unlink(SOCK)
    q = subprocess.Popen([QEMU, "-nographic", "-machine", "esp32", "-m", "4M",
        "-drive", f"file={flash},if=mtd,format=raw",
        "-nic", f"user,model=open_eth,host=10.0.2.5,guestfwd=tcp:10.0.2.2:7000-cmd:true,hostfwd=tcp:127.0.0.1:{PORT}-:2323",
        "-global", "driver=timer.esp32.timg,property=wdt_disable,value=true",
        "-serial", f"file:{u}", "-chardev", f"socket,id=gps1,path={SOCK},server=on,wait=off",
        "-serial", "chardev:gps1", "-serial", "null", "-monitor", "none"],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    t0 = time.time()
    while time.time() - t0 < 300 and q.poll() is None:
        if "MeshCom" in console("--info", 3):
            log(f"  console up after {time.time() - t0:.0f} s"); return q
        time.sleep(3)
    log("  console NOT up"); q.kill(); q.wait(); sys.exit(1)


def maxhop(u):
    before = len(uart(u)); console("--maxhop", 3); time.sleep(1)
    m = re.findall(r"\[MAXHOP\];text;(-?\d+);pos;(-?\d+)", uart(u)[before:])
    return m[-1][0] if m else "?"


def inject(u, text):
    r = console(f"--injectmsg TE5T-1 {text}", 3); time.sleep(4)
    err = re.findall(r"\[INJECT\];err;[^\r\n]*", uart(u))
    if err: log(f"  inject errors so far: {err[-1]}")


def fresh(name):
    f = f"{W}/flash-{name}.bin"; shutil.copy(IMG, f); return f


# Phase A: no transmission between {SET} and the power-off
log("PHASE A: {SET} then hard power-off, no transmission in between")
fa = fresh("A"); ua = f"{W}/uart-A1.log"
q = boot(fa, ua)
console("--setcall TE5T-1", 4); time.sleep(40)
h0 = maxhop(ua); log(f"  initial text hop limit: {h0}")
inject(ua, "{SET}44;2;"); log(f"  after {{SET}}44 (out of range): {maxhop(ua)}")
inject(ua, "{SET}" + h0 + ";2;"); log(f"  after {{SET}}{h0} (unchanged): {maxhop(ua)}")
inject(ua, "{SET}2;2;"); ram = maxhop(ua); log(f"  after {{SET}}2: {ram}")
time.sleep(5); q.kill(); q.wait()
na = nvs(fa, "max_hop_text", "node_msgid"); log(f"  NVS after hard power-off: {na}")
ub = f"{W}/uart-A2.log"; q = boot(fa, ub); a2 = maxhop(ub); log(f"  after reboot: text hop limit {a2}")
q.kill(); q.wait()

# Phase B: {SET}, then one text transmission, then the power-off (the auditor's sequence)
log("PHASE B: {SET}, one text transmission, hard power-off")
fb = fresh("B"); uc = f"{W}/uart-B1.log"
q = boot(fb, uc)
console("--setcall TE5T-1", 4); time.sleep(40)
inject(uc, "{SET}2;2;"); log(f"  after {{SET}}2: {maxhop(uc)}")
m0 = nvs(fb, "node_msgid").get("node_msgid")
console("::sethop test text", 4); time.sleep(15)
q.kill(); q.wait()
nb = nvs(fb, "max_hop_text", "node_msgid"); log(f"  NVS after TX + hard power-off: {nb} (msgid before the text: {m0})")
log(f"RESULT {TAG}: A ram={ram} nvs={na.get('max_hop_text', 'absent')} reboot={a2} | B nvs={nb.get('max_hop_text', 'absent')}")
