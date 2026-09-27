#!/usr/bin/env python3
"""drop-workaround.py PATCH batt|ble : remove ONE QEMU workaround from the overlay patch, in place (TEST ONLY).

batt  the ADC stub in src/batt_function_old.cpp (QEMU has no ADC; read_batt() would hang) and the
      "#ifndef QEMU_HEADLESS" guard around init_batt() in esp32setup()
ble   the three esp32setup() hunks that skip BLE/NimBLE (QEMU has no BT controller): the "#ifndef QEMU_HEADLESS"
      opener, the "#else ... BLE/NimBLE disabled ... #endif" hunk right after it, and the "No BLE backend" hunk
Prints the dropped hunks; fails unless exactly the expected number is dropped.
"""
import re, sys
path, which = sys.argv[1], sys.argv[2]
text = open(path).read()
sections = re.split(r"(?m)^(?=diff --git )", text)
out, dropped = [], []
for sec in sections:
    if not sec.startswith("diff --git "):
        out.append(sec); continue
    f = sec.split("\n", 1)[0].split(" b/")[-1]
    head, *hunks = re.split(r"(?m)^(?=@@ )", sec)
    added = ["\n".join(l for l in h.split("\n")[1:] if l.startswith("+")) for h in hunks]
    drop = set()
    for i, a in enumerate(added):
        if which == "batt" and f == "src/batt_function_old.cpp" and "adc1_get_raw" in a:
            drop.add(i)
        if which == "batt" and f == "src/esp32/esp32_main.cpp" and "init_batt();" in hunks[i] \
                and [l[1:].strip() for l in a.split("\n")] == ["#ifndef QEMU_HEADLESS", "#endif"]:
            drop.add(i)
        if which == "ble" and f == "src/esp32/esp32_main.cpp":
            if "BLE/NimBLE disabled" in a:
                drop.add(i)
                assert i > 0 and added[i - 1].strip() == "+#ifndef QEMU_HEADLESS", "opener"
                drop.add(i - 1)
            if "No BLE backend in QEMU" in a:
                drop.add(i)
    for i in sorted(drop):
        dropped.append(f"{f}: {added[i][:90]!r}")
    kept = [h for i, h in enumerate(hunks) if i not in drop]
    if kept:
        out.append(head + "".join(kept))
    else:
        dropped.append(f"(whole file {f})")
expect = {"batt": 3, "ble": 3}[which]      # batt: two hunks, and the batt file section becomes empty
assert len(dropped) == expect, dropped
open(path, "w").write("".join(out))
print("\n".join("dropped " + d for d in dropped))
