#!/usr/bin/env python3
"""results.md from the qemu-sites.py runs: report.py COL=TAG[,TAG...] ...  (first tag with a fired window wins)"""
import json, os, re, sys

EV = "/home/makro/claude/meshcom-prs-evidence/all-envs/qemu/sites"
COLS = {}
for a in sys.argv[1:]:
    c, ts = a.split("="); COLS[c] = [t for t in ts.split(",") if os.path.exists(f"{EV}/{t}/results.json")]
RAW = {t: json.load(open(f"{EV}/{t}/results.json")) for ts in COLS.values() for t in ts}
R, SRC = {}, {}
for c, ts in COLS.items():
    R[c], SRC[c] = {}, {}
    for t in ts:
        for k, v in RAW[t].items():
            if k.startswith("_"): continue
            if k not in R[c] or (R[c][k].get("status") != "fired" and v.get("status") == "fired"):
                R[c][k] = v; SRC[c][k] = t
SITES = [("ping", "sendPing :3344"), ("pong", "SendPong :3446"), ("message", "sendMessage :4099"),
         ("injpos", "sendInjectedPosition :4284"), ("position", "sendPosition :4859"),
         ("apppos", "sendAPPPosition :4946"), ("ack", "SendAckMessage :5016"), ("hey", "sendHey :5108"),
         ("telemetry", "sendTelemetry :5447")]


def ctr(desc):
    m = re.search(r"ctr (\d+)", desc); return int(m.group(1)) if m else None


def clean(a):
    """clean window: latitude not flushed before the trigger, and every other frame in the window is a
    retransmission of an older frame (counter below the site's frame: no send function ran for it)."""
    if a.get("status") != "fired": return False
    others = [f for f in a["frames"] if ctr(f) is not None and ctr(f) > a["ctr_in_frame"]]
    return a["pre_clean"] and not others


def pick(r):
    atts = r.get("earlier_attempts", []) + [r]
    ok = [a for a in atts if clean(a)]
    return (ok[-1] if ok else atts[-1]), len(atts)


def cell(t, site):
    r = R[t].get(site)
    if r is None: return "not run", None
    if r["status"] != "fired":
        return r["status"] + (": " + r.get("note", "") if r.get("note") else ""), None
    a, n = pick(r)
    frame = [f for f in a["frames"] if ctr(f) == a["ctr_in_frame"]][0]
    txt = (f"frame `{frame}`; NVS node_msgid {a['nvs_before']['node_msgid']} -> {a['nvs_after']['node_msgid']} "
           f"(expected {a['msgid_expected']}: {'OK' if a['a_persisted'] else 'MISMATCH'}); "
           f"latitude set {a['lat_set']}, NVS node_lat {a['nvs_before']['node_lat']} -> {a['nvs_after']['node_lat']} "
           f"(**{'FLUSHED' if a['flushed'] else 'not flushed'}**); max loop gap "
           f"{'n/a (xml image, no INSTRUMENT)' if SRC[t][site].endswith('-xml') else str(a['max_gap_ms']) + ' ms'}; "
           f"load {a['load'][0]} (under load); window {'clean' if clean(a) else 'NOT clean'}; attempts {n}; "
           f"log `{SRC[t][site]}/`")
    return txt, a


def verdict(site):
    cells = {t: cell(t, site)[1] for t in R}
    base = [t for t in R if t == "stock"]
    new = [t for t in R if t != "stock"]
    if any(c is None for c in cells.values()): return None
    okb = all(clean(cells[t]) and cells[t]["a_persisted"] and cells[t]["flushed"] for t in base)
    okn = all(clean(cells[t]) and cells[t]["a_persisted"] and not cells[t]["flushed"] for t in new)
    return "PASS" if okb and okn else "FAIL/INCONCLUSIVE"


out = ["# PR1 per-site QEMU proof (save_settings -> save_msgid at the nine TX sites)", "",
       "Harness: `/home/makro/claude/agent5-allenvs/qemu/sites/qemu-sites.py IMAGE TAG` (stock Espressif QEMU, "
       "INSTRUMENT_ENABLED images, env qemu-headless-extradio-gpsd). Per site one window: the virtual GPS first moves "
       "the node to a fresh latitude (RAM only), the site is fired, the node's own TX frame is captured by the "
       "harness's external-radio bridge (guestfwd of 10.0.2.2:7000; the guest never reaches the host's real bridge), "
       "then NVS is read from the flash file.", "",
       "- (a) persistence: NVS node_msgid == counter after the site's frame (frame id low 10 bits + 1). The flash file "
       "is QEMU's persistent medium; each run ends with SIGKILL and a final read (`_final`).",
       "- (b) timing-free discriminator: stock's full save flushes the RAM-only latitude (FLUSHED), PR1's save_msgid() "
       "does not (not flushed). PR1's own save_position() fires only on the first fix and every 15 min after; the "
       "harness keeps windows clear of that boundary. Secondary, load-sensitive: max INSTRUMENT loop gap in the window "
       "(stock blocks at the save; threshold 250 ms, so 0 = no gap line at all).",
       "- Clean window: latitude not in NVS before the trigger, and no other new TX in the window (retransmissions of "
       "older frames, which run no send function and do not touch the counter, are allowed).", "",
       "**All results are UNDER LOAD (provisional)**: the PC ran parallel CI compiles and, for the instr runs, three "
       "QEMUs at once (1-min load average 40..111, given per window). The FLUSH discriminator does not depend on timing; "
       "the loop-gap column does (stock gaps of 3.6..25 s instead of the ~2 s expected on an idle PC). Per the handler's "
       "rule a FAIL or odd timing must be re-run on an idle PC before it counts; there is no FAIL here.", "",
       "Columns: stock = base (cf215b5d) images, pr1 = PR1-only images, merge = all three PRs (Ethernet mode via "
       "testhack-eth). The *-instr images (INSTRUMENT_ENABLED) carry eight sites; sendTelemetry is reachable only on the "
       "*-xml TEST-ONLY images (see Triggers), which have no INSTRUMENT, hence no gap data for it.", ""]
out.append("| site (merge-tree line) | " + " | ".join(R) + " | verdict |")
out.append("|---|" + "---|" * (len(R) + 1))
for site, name in SITES:
    cells = [cell(t, site)[0] for t in R]
    v = verdict(site)
    if v is None:
        st = {R[t].get(site, {}).get("status") for t in R}
        v = "DEAD CODE (skipped)" if st == {"dead-code"} else ("UNREACHED" if "unreached" in st else "incomplete")
    out.append(f"| {name} | " + " | ".join(c.replace("|", "/") for c in cells) + f" | {v} |")
out += ["", "## Triggers", ""]
for site, name in SITES:
    trig = next((R[t][site].get("trigger") for t in R if site in R[t] and R[t][site].get("trigger")), None)
    out.append(f"- **{name}**: {trig or R[next(iter(R))].get(site, {}).get('note', '')}")
out += ["", "## Notes", "",
        "- Unreached, not passed: sendInjectedPosition (KISS/TCP listener is WiFi-gated, the emulated node has only "
        "OpenETH; `--kiss on`/`--kiss tx on` were given and no `[KISS]...server started` line appears; a host connect to "
        "the forwarded guest port 8001 is reset). sendAPPPosition has no caller at all (dead code).",
        "- Also reachable on hardware but not exercised here: SendAckMessage via KISS (kiss_functions.cpp:439) and via "
        "the gateway UDP path (udp_functions.cpp:477); the same function was proven through the LoRa RX path.",
        "- Retried windows: a window was repeated (35 s later) when it was not clean, e.g. a broadcast text's ring "
        "retransmission landed in it (early harness version) or a scheduled ping/trickle HEY fired inside it. Every "
        "attempt of every image is in results.json; no attempt of pr1 or merge ever flushed the latitude and no "
        "attempt of stock failed to flush it (the stock ping/hey attempts that were retried had the latitude flushed "
        "before the trigger by a neighbouring TX, which is the stock behaviour).",
        "- In pr1/merge the NVS node_lat stays at the value written by the node's own save paths (first-fix "
        "save_position(), --pingtime/--pingcall saves), never at a window's latitude.",
        "- Telemetry: the esp32_main timer calls sendTelemetry(SOFTSER_APP_ID=1), which returns early unless "
        "node_parm_1 is set; only decodeTinyXML() sets it (soft-serial app, or the TEST-ONLY --xmltz hook in the xml "
        "images). The first telemetry (PARM, right after --ptime 5) is unmeasured; the window is the next one (UNIT).",
        ""]
out += ["## Hard power-off at the end of each run", ""]
for t in RAW:
    f = RAW[t].get("_final", {})
    out.append(f"- {t}: NVS after SIGKILL {f.get('nvs_after_kill')}, counter after the last own TX "
               f"{f.get('counter_after_last_tx')}: {'match' if f.get('match') else 'MISMATCH'}")
out += ["", "## Logs", ""]
for t in RAW:
    out.append(f"- {t}: `{EV}/{t}/` (sites.log harness, bridge.log every TX/RX frame in hex, uart.log console UART, "
               "results.json all windows incl. retried ones, flash.bin after the kill)")
open(f"{EV}/results.md", "w").write("\n".join(out) + "\n")
print("\n".join(out))
