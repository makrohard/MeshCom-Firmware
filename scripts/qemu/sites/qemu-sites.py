#!/usr/bin/env python3
"""PR1 per-site proof under stock Espressif QEMU: every transmission site that PR1 changed from
save_settings() to save_msgid() is fired on its own, and for each one:

  (a) persistence  node_msgid in the flash file (NVS) equals the counter after that TX. The flash file
                   is QEMU's persistent medium, so what is in it survives a hard power-off; the run
                   ends with a SIGKILL and a final read to show it.
  (b) discriminator, two independent ones:
      FLUSH  timing-free. Before the site fires, the virtual GPS moves the node to a fresh latitude.
             The GPS fix changes meshcom_settings.node_lat in RAM only (stock has no save on that path;
             PR1's save_position() fires once per 15 min, and each window is kept clear of that boundary).
             stock's full save_settings() at the TX flushes the new latitude into NVS; PR1's
             save_msgid() does not.
      GAP    INSTRUMENT_ENABLED loop-gap lines ([INSTR-LOOP];gap;ms;N;in;S, threshold 250 ms) inside
             the window: stock blocks the loop at the TX, PR1 does not. Load-sensitive, secondary.

Every window is attributed by the external-radio bridge this harness plays: the firmware's own TX
frames are captured (TX_REQUEST), and a window counts only if exactly the expected frame and no other
TX appeared in it. The node's 10.0.2.2:7000 bridge endpoint is redirected by a QEMU guestfwd to this
harness (the slirp host alias is moved to 10.0.2.5), so the guest never reaches a real bridge on the
host's port 7000.

  qemu-sites.py IMAGE TAG [site ...] [--slot N]

sites: message position ping pong ack hey telemetry injpos apppos   (default: all)
Logs: /home/makro/claude/meshcom-prs-evidence/all-envs/qemu/sites/TAG/
"""
import json, os, random, re, shutil, socket, struct, subprocess, sys, threading, time

ALL = ["message", "position", "ping", "pong", "ack", "injpos", "hey", "telemetry", "apppos"]
args = [a for a in sys.argv[1:]]
SLOT = 0
if "--slot" in args:
    i = args.index("--slot"); SLOT = int(args[i + 1]); del args[i:i + 2]
IMG, TAG = args[0], args[1]
SITES = args[2:] or ALL
EV = "/home/makro/claude/meshcom-prs-evidence/all-envs/qemu/sites"
QEMU = "/home/makro/claude/qemu-cache-pr/b-up/qemu-system-xtensa"   # stock Espressif QEMU build, read-only
NVSDUMP = "/home/makro/claude/agent5-allenvs/qemu/nvsdump.py"
CON, BR, KISS = [(22341, 22342, 22343), (22345, 22346, 22347), (22344, 22348, 22349)][SLOT]   # ports 22341..22349 only
MYCALL, PEER = "TE5T-1", "DL1PEE-1"
W = f"{EV}/{TAG}"
shutil.rmtree(W, ignore_errors=True); os.makedirs(W)
FLASH = f"{W}/flash.bin"; shutil.copy(IMG, FLASH)
UART = f"{W}/uart.log"
SOCK = f"/tmp/claude-1000/qs{SLOT}-{os.getpid()}.sock"
LOG = open(f"{W}/sites.log", "w")
BLOG = open(f"{W}/bridge.log", "w")
T0 = time.time()


def log(m):
    l = time.strftime("%H:%M:%S ") + f"[{time.time() - T0:7.1f}] " + m
    print(l, flush=True); LOG.write(l + "\n"); LOG.flush()


def blog(m):
    BLOG.write(time.strftime("%H:%M:%S ") + f"[{time.time() - T0:7.1f}] " + m + "\n"); BLOG.flush()


def uart():
    try: return open(UART, "rb").read().decode("utf-8", "replace")
    except FileNotFoundError: return ""


def console(cmd, wait=4.0, port=None):
    try: s = socket.create_connection(("127.0.0.1", port or CON), timeout=3)
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


def cmd(c, expect=None, timeout=60):
    """Send a console command and wait until the UART shows it was handled (expect regex), keeping the
    connection open meanwhile: the net console echoes and parses slowly on the loaded emulator."""
    u0 = len(uart()); t = time.time()
    try: s = socket.create_connection(("127.0.0.1", CON), timeout=5)
    except OSError: log(f"  console connect failed for {c!r}"); return None
    s.sendall((c + "\r\n").encode()); s.settimeout(0.5)
    m = None
    while time.time() - t < timeout:
        try: s.recv(4096)
        except socket.timeout: pass
        except OSError: break
        tx = uart()[u0:]
        if expect is None:
            flat = re.sub(r"\[\s*\d+\]\[E\]\[WiFiUdp[^\n]*\n?", "", tx).replace("\r", "").replace("\n", "")
            if time.time() - t > 2 and c in flat: break
        else:
            m = re.search(expect, tx)
            if m: break
    time.sleep(1); s.close(); return m


def setting(c, key, val, timeout=90):
    """A saving console command, confirmed by the value appearing in NVS."""
    cmd(c, None, 20); t = time.time()
    while time.time() - t < timeout:
        if nvs(key).get(key) == val: return True
        time.sleep(2)
    log(f"  setting {c!r}: NVS {key} != {val!r} ({nvs(key)})"); return False


def nvs(*keys):
    out = subprocess.run([sys.executable, NVSDUMP, FLASH, *keys], capture_output=True, text=True).stdout
    return dict(l.split("=", 1) for l in out.split())


# ---------------------------------------------------------------- external-radio bridge (XR v1)
def xr(typ, seq=0, payload=b""):
    return b"XR\x01" + bytes([typ]) + struct.pack(">HH", len(payload), seq) + payload


class Bridge:
    """Plays meshcom-loraham-bridge in open mode: HELLO_ACK, AUTH_RESULT ok, echoes CONFIGURE,
    answers every TX_REQUEST with TX_RESULT success and records the frame, injects RX_PACKETs."""
    def __init__(self):
        self.tx = []            # (host time, frame bytes)
        self.lock = threading.Lock()
        self.conn = None
        self.ready = False
        self.srv = socket.socket(); self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv.bind(("127.0.0.1", BR)); self.srv.listen(4)
        threading.Thread(target=self.accept_loop, daemon=True).start()

    def accept_loop(self):
        while True:
            c, _ = self.srv.accept()
            blog("bridge: firmware connected"); self.conn = c; self.ready = False
            threading.Thread(target=self.serve, args=(c,), daemon=True).start()

    def send(self, b):
        try: self.conn.sendall(b); return True
        except (OSError, AttributeError): return False

    def serve(self, c):
        buf = b""
        while True:
            try: d = c.recv(4096)
            except OSError: d = b""
            if not d:
                blog("bridge: firmware disconnected"); self.ready = False; return
            buf += d
            while len(buf) >= 8:
                if buf[:3] != b"XR\x01": blog("bridge: bad magic " + buf[:8].hex()); c.close(); return
                typ = buf[3]; ln, seq = struct.unpack(">HH", buf[4:8])
                if len(buf) < 8 + ln: break
                p = buf[8:8 + ln]; buf = buf[8 + ln:]
                if typ == 0x01:
                    blog("bridge: HELLO"); c.sendall(xr(0x02, 0, b"\x01") + xr(0x05, 0, b"\x00"))
                elif typ == 0x06:
                    f, bw, sf, cr, sw, pre, pw, crc, ldro = struct.unpack(">IIBBHHbBB", p)
                    blog(f"bridge: CONFIGURE freq {f} bw {bw} sf {sf} cr 4/{cr} sync {sw:#x} pre {pre} pwr {pw} crc {crc} ldro {ldro}")
                    c.sendall(xr(0x07, 0, b"\x00" + p)); self.ready = True
                elif typ == 0x09:
                    with self.lock: self.tx.append((time.time(), p))
                    blog(f"TX seq {seq} len {len(p)} {describe(p)} hex {p.hex()}")
                    c.sendall(xr(0x0A, seq, b"\x00"))
                elif typ == 0x0C:
                    pass
                else:
                    blog(f"bridge: type {typ:#x} len {ln}")

    def inject(self, frame, rssi=-6000, snr=900):
        blog(f"RX-INJECT len {len(frame)} {describe(frame)} hex {frame.hex()}")
        return self.send(xr(0x08, 0, struct.pack(">hhH", rssi, snr, len(frame)) + frame))

    def frames_since(self, t):
        with self.lock: return [f for (ts, f) in self.tx if ts >= t]


def describe(p):
    """MeshCom LoRa frame -> short text (type, msg id, low-10-bit counter, header, payload)."""
    if len(p) < 7 or p[0] not in (0x3A, 0x21, 0x40):
        return f"type {p[:1].hex()} (not a mesh text/pos/hey frame)"
    mid = struct.unpack("<I", p[1:5])[0]
    body = p[6:].split(b"\x00", 1)[0].decode("latin-1")
    return f"'{chr(p[0])}' id {mid:08X} ctr {mid & 0x3FF} hop {p[5]:#04x} [{body}]"


def frame_ctr(p): return struct.unpack("<I", p[1:5])[0] & 0x3FF


def encode(ptype, mid, hop, src, dst, payload, tail):
    """encodeAPRS() (aprs_functions.cpp) in Python. tail = (hw, mod, fw, lasthw, sub) bytes."""
    hw, mod, fw, lasthw, sub = tail
    b = bytes([ord(ptype)]) + struct.pack("<I", mid) + bytes([hop & 0x0F])
    b += f"{src}>{dst}{ptype}".encode() + payload.encode() + b"\x00" + bytes([hw, mod])
    fcs = sum(b)
    return b + bytes([(fcs >> 8) & 0xFF, fcs & 0xFF, fw, lasthw, sub, 0x7E])


def tail_of(p):
    """(hw, mod, fw, lasthw, sub) and hop nibble of a captured own frame."""
    z = p.index(b"\x00", 6)
    return (p[z + 1], p[z + 2], p[z + 5], p[z + 6], p[z + 7]), p[5] & 0x0F


# ---------------------------------------------------------------- virtual GPS (UART1)
class Gps:
    def __init__(self):
        self.lat_min = 0.0        # minutes north of 48 00.0000 N
        threading.Thread(target=self.run, daemon=True).start()

    @staticmethod
    def cs(s):
        x = 0
        for ch in s: x ^= ord(ch)
        return f"${s}*{x:02X}\r\n"

    def run(self):
        s = None
        while True:
            if s is None:
                try:
                    s = socket.socket(socket.AF_UNIX); s.connect(SOCK)
                except OSError:
                    s = None; time.sleep(1); continue
            g = time.gmtime(); hms = time.strftime("%H%M%S.00", g); dmy = time.strftime("%d%m%y", g)
            lat = f"48{self.lat_min:07.4f}"
            out = self.cs(f"GPGGA,{hms},{lat},N,01200.0000,E,1,07,1.2,540.0,M,46.9,M,,") + \
                  self.cs(f"GPRMC,{hms},A,{lat},N,01200.0000,E,0.0,54.7,{dmy},,,A")
            try: s.sendall(out.encode())
            except OSError: s = None
            time.sleep(1)

    def set_deg(self, deg):      # deg = 48.xxxx
        self.lat_min = round((deg - 48.0) * 60.0, 4)


# ---------------------------------------------------------------- QEMU
def boot():
    if os.path.exists(SOCK): os.unlink(SOCK)
    nic = (f"user,model=open_eth,net=10.0.2.0/24,host=10.0.2.5,"
           f"hostfwd=tcp:127.0.0.1:{CON}-:2323,hostfwd=tcp:127.0.0.1:{KISS}-:8001,"
           f"guestfwd=tcp:10.0.2.2:7000-cmd:socat - TCP:127.0.0.1:{BR}")
    q = subprocess.Popen([QEMU, "-nographic", "-machine", "esp32", "-m", "4M",
        "-drive", f"file={FLASH},if=mtd,format=raw", "-nic", nic,
        "-global", "driver=timer.esp32.timg,property=wdt_disable,value=true",
        "-serial", f"file:{UART}", "-chardev", f"socket,id=gps1,path={SOCK},server=on,wait=off",
        "-serial", "chardev:gps1", "-serial", "null", "-monitor", "none"],
        stdin=subprocess.DEVNULL, stdout=open(f"{W}/qemu.out", "w"), stderr=subprocess.STDOUT)
    t = time.time()
    while time.time() - t < 400 and q.poll() is None:
        if "MeshCom" in console("--info", 3):
            log(f"console up after {time.time() - t:.0f} s"); return q
        time.sleep(3)
    log(f"console NOT up (qemu rc {q.poll()})"); q.kill(); q.wait(); sys.exit(2)


def uptime_s():
    """firmware millis()/1000 from the newest [INSTR...] or timestamp-free guess: host time since boot."""
    return time.time() - BOOT_T


def ram_lat():
    m = cmd("--pos", r"LAT: (\d+\.\d+) ([NS])", 30)
    return float(m.group(1)) if m else None


def gaps(text):
    return [(int(a), b) for a, b in re.findall(r"\[INSTR-LOOP\][; ]gap[; ]ms[; ](\d+)[; ]in[; ]([^; \r\n]+)", text)]


# ---------------------------------------------------------------- site triggers
# Each returns (description of the trigger, predicate on a captured frame that identifies the site's TX).
def src_is_me(p): return p[6:6 + len(MYCALL) + 1] == f"{MYCALL}>".encode()


def is_text_from_me(p): return p[0] == 0x3A and src_is_me(p)


SITE_INFO = {}
results = {}
state = {"lat_k": 0, "fix_t": None, "tail": None}


def next_lat():
    state["lat_k"] += 1
    return round(48.0 + 0.0011 * state["lat_k"], 4)


def avoid_possave_boundary(margin=100):
    """PR1: save_position() fires on the first fix and then every 15 min; keep windows clear of it."""
    if state["fix_t"] is None: return
    while True:
        ph = (time.time() - state["fix_t"]) % 900
        if ph < 900 - margin and ph > 30: return
        log(f"  waiting out the 15-min save_position boundary (phase {ph:.0f} s)"); time.sleep(10)


def window(site, trigger, match, wait_frame=40, settle=8, pre=None, tries=3):
    """Up to `tries` windows until one is clean (exactly the site's frame, latitude not flushed before)."""
    att = []
    for i in range(tries):
        r = window1(site, trigger, match, wait_frame, settle, pre)
        att.append(r)
        if r.get("status") != "fired" or (r["only_frame"] and r["pre_clean"]): break
        log(f"  {site}: window not clean (only_frame {r['only_frame']}, pre_clean {r['pre_clean']}), retry in 35 s")
        time.sleep(35)
    r = dict(att[-1]); r["attempts"] = len(att)
    if len(att) > 1: r["earlier_attempts"] = att[:-1]
    return r


def window1(site, trigger, match, wait_frame=40, settle=8, pre=None):
    """One measured window. trigger() fires the site; match(frame) identifies its TX."""
    avoid_possave_boundary()
    if pre: pre()
    lat = next_lat(); GPS.set_deg(lat)
    t = time.time()
    while time.time() - t < 30:
        if ram_lat() == lat: break
        time.sleep(2)
    rl = ram_lat()
    if rl != lat:
        log(f"  {site}: RAM latitude did not follow the GPS ({rl} != {lat})"); return {"site": site, "status": "setup-failed"}
    time.sleep(4)
    n0 = nvs("node_lat", "node_msgid")
    u0 = len(uart()); t0 = time.time(); load = os.getloadavg()
    how = trigger()
    got = None; t1 = time.time()
    while time.time() - t1 < wait_frame:
        fr = BR_.frames_since(t0)
        if any(match(f) for f in fr): got = [f for f in fr if match(f)][0]; break
        time.sleep(0.5)
    time.sleep(settle)
    fr = BR_.frames_since(t0); txt = uart()[u0:]
    n1 = nvs("node_lat", "node_msgid")
    g = gaps(txt)
    r = {"site": site, "trigger": how, "lat_set": lat, "nvs_before": n0, "nvs_after": n1,
         "frames": [describe(f) for f in fr], "gaps": g, "load": [round(x, 1) for x in load],
         "window_s": round(time.time() - t0, 1)}
    if got is None:
        r["status"] = "unreached"
    else:
        ctr = frame_ctr(got); exp = (ctr + 1) % 1000
        r["ctr_in_frame"] = ctr; r["msgid_expected"] = exp
        r["a_persisted"] = n1.get("node_msgid") == str(exp)
        r["flushed"] = abs(float(n1.get("node_lat", "0")) - lat) < 1e-6
        r["pre_clean"] = abs(float(n0.get("node_lat", "0")) - lat) > 1e-6
        # retransmissions (the ring re-sends a frame with an id seen before) do not run a send
        # function and do not touch node_msgid; any OTHER new frame spoils the attribution
        seen = {f[1:5] for (ts, f) in BR_.tx if ts < t0}
        others = [f for f in fr if f is not got and f[1:5] not in seen and f[1:5] != got[1:5]]
        r["retransmissions"] = [describe(f) for f in fr if f is not got and (f[1:5] in seen or f[1:5] == got[1:5])]
        r["only_frame"] = not others
        r["max_gap_ms"] = max([x for x, _ in g], default=0)
        r["status"] = "fired"
    log(f"  {site}: {json.dumps(r)}")
    return r


def trig_message():
    cmd(f"::sites text {state['lat_k']}", None, 20); return "console '::sites text N' (sendMessage)"


def trig_position():
    cmd("--sendpos", None, 20); return "console '--sendpos' (sendPosition 0x9999)"


def trig_hey():
    cmd("--sendhey", None, 20); return "console '--sendhey' (sendHeyShot -> sendHey)"


def rx_frame(payload):
    tail, hop = state["tail"]
    return encode(":", random.getrandbits(31) | 0x40000000, 2, PEER, MYCALL, payload, tail)


def trig_pong():
    BR_.inject(rx_frame("{ping}")); return f"bridge RX_PACKET: text {PEER}>{MYCALL} '{{ping}}' (lora_functions OnRxDone -> SendPong)"


def trig_ack():
    n = random.randint(100, 999); state["acknum"] = n
    BR_.inject(rx_frame(f"sites dm{{{n}")); return f"bridge RX_PACKET: DM {PEER}>{MYCALL} 'sites dm{{{n}' (OnRxDone -> SendAckMessage)"


def run():
    global GPS, BR_, BOOT_T
    BR_ = Bridge(); GPS = Gps(); GPS.set_deg(48.0)
    log(f"image {IMG} sha256 {subprocess.run(['sha256sum', IMG], capture_output=True, text=True).stdout.split()[0]}")
    log(f"sites {SITES}; ports console {CON} bridge {BR} kiss {KISS}; load {os.getloadavg()}")
    q = boot(); BOOT_T = time.time()
    setting(f"--setcall {MYCALL}", "node_call", MYCALL)
    cmd("--setinfo on", None, 20)
    # --pingcall sets node_pingtime > 0, which makes sendHey() return early: no trickle HEY in the windows.
    setting(f"--pingcall {PEER}", "node_pingcall", PEER)
    t = time.time()
    while time.time() - t < 120 and not BR_.ready: time.sleep(2)
    log(f"bridge operational: {BR_.ready}")
    t = time.time()
    while time.time() - t < 180:
        if ram_lat() == 48.0: break
        time.sleep(3)
    state["fix_t"] = time.time()
    log(f"GPS fix in RAM: {ram_lat()} ; NVS {nvs('node_lat', 'node_msgid')}")
    # boot transmissions (bPosFirst at 100..130 s uptime, boot HEY) must be over before the first window
    while time.time() - BOOT_T < 160: time.sleep(5)
    log("boot TX so far: " + " | ".join(describe(f) for f in BR_.frames_since(0)))
    own = BR_.frames_since(0)
    if not own:
        cmd("::sites tail probe", None, 20); time.sleep(15); own = BR_.frames_since(0)
    state["tail"] = tail_of(own[-1]) if own else None
    log(f"frame tail from own TX: {state['tail']}")

    for site in SITES:
        log(f"SITE {site}")
        if site == "message":
            results[site] = window(site, trig_message, lambda p: is_text_from_me(p) and b"sites text" in p)
        elif site == "position":
            results[site] = window(site, trig_position, lambda p: p[0] == 0x21 and src_is_me(p))
        elif site == "ping":
            # --ping start saves (save_settings) and the first ping fires at once; measure the SECOND ping,
            # 30 s later, then stop (--ping stop does not save).
            setting("--pingtime 30", "node_pingtime", "30")
            u0 = len(uart()); cmd("--ping start", None, 20)
            t = time.time()
            while time.time() - t < 40 and "[PING]...send" not in uart()[u0:]: time.sleep(1)
            log("  first ping (after --ping start): " + " ".join(re.findall(r"\[PING\]\.\.\.[^\r\n]*", uart()[u0:]))[:120])
            def trig_ping(): return "--pingcall/--pingtime 30/--ping start, measuring the 2nd scheduled ping (esp32_main -> sendPing)"
            results[site] = window(site, trig_ping, lambda p: is_text_from_me(p) and b"{ping}" in p, wait_frame=45)
            cmd("--ping stop", None, 20)
        elif site == "pong":
            results[site] = window(site, trig_pong, lambda p: is_text_from_me(p) and b"{pong}" in p)
        elif site == "ack":
            results[site] = window(site, trig_ack, lambda p: is_text_from_me(p) and b":ack" in p)
        elif site == "hey":
            setting("--pingcall none", "node_pingtime", "0")     # else sendHey() returns early
            results[site] = window(site, trig_hey, lambda p: p[0] == 0x40)
        elif site == "telemetry":
            results[site] = telemetry_site()
        elif site == "injpos":
            results[site] = injpos_site()
        elif site == "apppos":
            results[site] = {"site": site, "status": "dead-code",
                             "note": "sendAPPPosition() has no caller in the tree (only its definition and the prototype in loop_functions.h)"}
            log("  apppos: dead code, skipped")
    # final: hard power-off and read the counter from the flash file
    last = BR_.frames_since(0)
    ram_ctr = (frame_ctr([f for f in last if f[0] in (0x3A, 0x21, 0x40)][-1]) + 1) % 1000 if last else None
    q.kill(); q.wait()
    fin = nvs("node_msgid", "node_lat")
    log(f"HARD POWER-OFF: NVS after kill {fin}; counter after the last own TX {ram_ctr}")
    results["_final"] = {"nvs_after_kill": fin, "counter_after_last_tx": ram_ctr,
                         "match": fin.get("node_msgid") == str(ram_ctr)}
    json.dump(results, open(f"{W}/results.json", "w"), indent=1)
    log("done")


def telemetry_site():
    # The only live telemetry caller in this build, esp32_main.cpp's timer, calls sendTelemetry(SOFTSER_APP_ID=1),
    # which returns early unless node_parm_1 is set. node_parm_1 is written only by decodeTinyXML()
    # (tinyxml_functions.cpp), reached from the soft-serial app (ENABLE_SOFTSER, not in this build) or, in the
    # TEST-ONLY "xml" images, from the console hook --xmltz. So the site is reachable only on the xml images.
    m = cmd("--xmltz +01:00", r"\[TEST\] xml timezone|\[APP\]\.\.\.Error parsing", 60)
    if not m or "TEST" not in m.group(0):
        log("  telemetry: no --xmltz hook in this image (not an xml build)")
        return {"site": "telemetry", "status": "unreached",
                "note": "sendTelemetry(1) from the esp32_main timer returns early without node_parm_1, which only "
                        "decodeTinyXML() sets (soft-serial app, not in this build; --xmltz exists only in the xml test images)"}
    t0 = time.time()
    setting("--ptime 5", "node_ptime", "5")        # timer = node_parm_time minutes (5 is the minimum)
    t = time.time()
    while time.time() - t < 400 and not any(b"PARM." in f for f in BR_.frames_since(t0)): time.sleep(2)
    first = [describe(f) for f in BR_.frames_since(t0) if b"PARM." in f]
    log(f"  telemetry: first (unmeasured) telemetry after --xmltz/--ptime: {first}")
    def trig(): return ("--xmltz +01:00 (TEST-ONLY hook -> decodeTinyXML sets node_parm_1) and --ptime 5; the esp32_main "
                        "5-min timer then calls sendTelemetry(1); the 2nd telemetry is measured")
    return window("telemetry", trig, lambda p: is_text_from_me(p) and (b"UNIT." in p or b"EQNS." in p or b"T#" in p or b"PARM." in p or b"BITS." in p), wait_frame=360)


def injpos_site():
    # sendInjectedPosition() is called only from kiss_functions.cpp (KISS TX of an APRS position).
    cmd("--kiss on", None, 20); cmd("--kiss tx on", None, 20); time.sleep(10)
    u = uart()
    started = "[KISS]...server started" in u
    try:
        s = socket.create_connection(("127.0.0.1", KISS), timeout=3); s.settimeout(3)
        s.sendall(b"\xc0\x00" + b"\xc0"); time.sleep(2)
        try: d = s.recv(64)
        except OSError as e: d = repr(e).encode()
        s.close(); conn = f"host connect ok, reply {d!r}"
    except OSError as e:
        conn = f"host connect failed: {e!r}"
    log(f"  injpos: KISS server started line in UART: {started}; {conn}")
    r = {"site": "injpos", "kiss_server_started": started, "connect": conn}
    if not started:
        r["status"] = "unreached"
        r["note"] = ("kissLoop()/kissSetup() open the KISS/TCP listener only when WiFi.status() == WL_CONNECTED "
                     "(kiss_functions.cpp); the QEMU node is on OpenETH, so the listener never opens and "
                     "sendInjectedPosition() (only caller: kiss_functions.cpp:476) cannot be reached")
    return r


if __name__ == "__main__":
    run()
