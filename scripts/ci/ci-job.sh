#!/bin/bash
# Runs INSIDE a5-meshcom-ci:1 with the tree at /ws. Steps after "Add T-Beam Supreme board" in meshcom-ci.yml,
# verbatim (GitHub runs each step with bash -e). The release-action is replaced by an artifact-existence check.
cd /ws
step() { echo "=== STEP: $1 ($(date -u +%T))"; bash -e -c "$2"; rc=$?; echo "=== RESULT: $1 rc=$rc ($(date -u +%T))"; return $rc; }
python --version; pio --version
step "Build all Projects" "cd /ws && pio run" || exit 10
step "Convert RAK to UF2" "wget -q https://raw.githubusercontent.com/microsoft/uf2/refs/heads/master/utils/uf2conv.py && wget -q https://raw.githubusercontent.com/microsoft/uf2/refs/heads/master/utils/uf2families.json && python3 uf2conv.py .pio/build/wiscore_rak4631/firmware.hex -c -o .pio/build/wiscore_rak4631/wiscore_rak4631.uf2 -f 0xADA52840" || exit 11
step "Convert HELTEC_T114 to UF2" "wget -q https://raw.githubusercontent.com/microsoft/uf2/refs/heads/master/utils/uf2conv.py && wget -q https://raw.githubusercontent.com/microsoft/uf2/refs/heads/master/utils/uf2families.json && python3 uf2conv.py .pio/build/heltec_t114/firmware.hex -c -o .pio/build/heltec_t114/heltec_t114.uf2 -f 0xADA52840" || exit 12
step "Convert T_ECHO to UF2" "wget -q https://raw.githubusercontent.com/microsoft/uf2/refs/heads/master/utils/uf2conv.py && wget -q https://raw.githubusercontent.com/microsoft/uf2/refs/heads/master/utils/uf2families.json && python3 uf2conv.py .pio/build/t_echo/firmware.hex -c -o .pio/build/t_echo/t_echo.uf2 -f 0xADA52840" || exit 13
# save the ELFs/maps/bins before the rename step moves the firmware files
step "Rename Files" "$(python3 - <<'PY'
import re
s=open('/ws/.github/workflows/meshcom-ci.yml').read()
m=re.search(r'- name: Rename Files\n\s+run: "(.*?)"\n', s, re.S)
print(m.group(1))
PY
); wait" || exit 14
echo "=== STEP: artifact check"
python3 - <<'PY'
import re,os
s=open('/ws/.github/workflows/meshcom-ci.yml').read()
a=re.search(r'artifacts: "(.*?)"', s, re.S).group(1)
miss=0
for p in [x.strip() for x in a.split(',') if x.strip()]:
    ok=os.path.exists(p); miss+= not ok
    print(("OK      " if ok else "MISSING ")+p)
print(f"=== RESULT: artifact check missing={miss}")
PY
