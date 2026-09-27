#!/bin/bash
# build-image-ci.sh <label> <commit> [short|xml|eth|instr|nobatt[-flag]|noble[-flag]|all] : MeshCom tree at <commit> + meshcom-qemu-raspi at 113ff40b, built like
# the lhpc-speed CI (qemu-headless-extradio-gpsd). The optional TEST-ONLY scaffolding (never part of any PR):
#   short  custom shortname stored at boot (testhack-short.py), for the PR2 setcall proof
#   xml    --xmltz console command + testTinyXML stub (commit 7ba919cb's diff), soft-serial globals, tinyxml2, -D ENABLE_XML
#   eth    overlay WITHOUT its own net_console.cpp hunk + testhack-eth.py (HAS_ETHERNET, netmode 1), for the PR3a A/B
#   instr  -D INSTRUMENT_ENABLED=1 (upstream's loop-gap instrumentation), for the PR1 loop-gap A/B
#   nobatt[-flag]  overlay WITHOUT its ADC workaround (drop-workaround.py batt) [+ -D DISABLE_BATTERY], PR3c A/B
#   noble[-flag]   overlay WITHOUT its BLE workaround (drop-workaround.py ble) [+ -D DISABLE_BLE], PR3d A/B
#   all    PR3 combined: overlay WITHOUT its net-console, battery and BLE workarounds; testhack-eth.py;
#          -D DISABLE_BATTERY -D DISABLE_BLE (the three PR3 features replace the three workarounds)
set -eo pipefail
L=$1; C=$2; V=$3; S=~/claude/agent5-allenvs/qemu; R=$S/repo-$L; MQR=113ff40b70168c62e4ca971a4f3b028d404cf6bb
rm -rf $R; mkdir -p $R; git -C ~/claude/mqr-docs-wording archive $MQR | tar -x -C $R
git clone -q --no-checkout ~/claude/agent5-allenvs/base $R/.work/MeshCom-Firmware
git -C $R/.work/MeshCom-Firmware checkout -q $C
git -C $R/.work/MeshCom-Firmware log -1 --format="[$L] tree at %h %s"
cd $R
export PIO=~/claude/.venv-pio/bin/pio XR_HOST=10.0.2.2 XR_PORT=7000 XR_PASSWORD=""
# NCETH=1 (agent 5): on trees that contain PR3, the overlay's net_console hunk AND its battery and BLE workarounds
# (esp32_main.cpp) do not apply, because PR3 replaces exactly those three. Every image of such a tree therefore drops all
# three and uses testhack-eth.py (HAS_ETHERNET, netmode 1), like the `all` variant. The flags are
# -D DISABLE_BATTERY -D DISABLE_BLE, except for variants drop3 (no flag), drop3-batt (DISABLE_BATTERY only) and
# drop3-ble (DISABLE_BLE only), which are informative controls.
if [ "$V" = eth ] || [ "$V" = all ] || [ -n "$NCETH" ]; then
    P=overlay/patches/meshcom-qemu-headless.patch
    python3 $S/drop-hunks.py $P $P.new file:src/net_console.cpp && mv $P.new $P
fi
case "$V" in nobatt*) python3 $S/drop-workaround.py overlay/patches/meshcom-qemu-headless.patch batt ;;
             noble*)  python3 $S/drop-workaround.py overlay/patches/meshcom-qemu-headless.patch ble ;;
             all|drop3*) for w in batt ble; do python3 $S/drop-workaround.py overlay/patches/meshcom-qemu-headless.patch $w; done ;;
             *) [ -n "$NCETH" ] && for w in batt ble; do python3 $S/drop-workaround.py overlay/patches/meshcom-qemu-headless.patch $w; done ;; esac
scripts/apply-overlay.sh 2>&1 | tail -2
scripts/prepare-openeth.sh 2>&1 | tail -1
W=.work/MeshCom-Firmware
case "$V" in
  short) python3 $S/testhack-short.py $W ;;
  eth)   python3 $S/testhack-eth.py $W ;;
  all)   python3 $S/testhack-eth.py $W; export PLATFORMIO_BUILD_FLAGS="-D DISABLE_BATTERY -D DISABLE_BLE" ;;
  xml)
    git -C ~/claude/meshcom-prs show 7ba919cb --format= | git -C $W apply
    python3 - $W <<'EOF'
import sys, pathlib
w = pathlib.Path(sys.argv[1])
f = w / "src/tinyxml_functions.cpp"; s = f.read_text(); a = "void testTinyXML() {}"
assert s.count(a) == 1
f.write_text(s.replace(a, '#if !defined(ENABLE_SOFTSER)   // TEST ONLY: the soft-serial module normally defines these\n'
    'String strTELE_PARM=""; String strTELE_UNIT=""; String strTELE_VALUES=""; String strTELE_DATETIME="";\n'
    'String strTELE_CH_ID=""; String strTELE_UTCOFF=""; unsigned long lTELE_TIMER=0;\n#endif\n' + a, 1))
v = w / "variants/qemu-headless/platformio.ini"; t = v.read_text(); b = "lib_deps ="
assert t.count(b) == 1, "lib_deps"
v.write_text(t.replace(b, b + "\n\thttps://github.com/leethomason/tinyxml2   ; TEST ONLY (XML proof)", 1))
EOF
    export PLATFORMIO_BUILD_FLAGS="-D ENABLE_XML" ;;
  instr)       export PLATFORMIO_BUILD_FLAGS="-D INSTRUMENT_ENABLED=1" ;;
  nobatt-flag) export PLATFORMIO_BUILD_FLAGS="-D DISABLE_BATTERY" ;;
  noble-flag)  export PLATFORMIO_BUILD_FLAGS="-D DISABLE_BLE" ;;
esac
if [ -n "$NCETH" ]; then
    [ "$V" != eth ] && [ "$V" != all ] && python3 $S/testhack-eth.py $W
    case "$V" in drop3) F3="" ;; drop3-batt) F3="-D DISABLE_BATTERY" ;; drop3-ble) F3="-D DISABLE_BLE" ;; all) F3="" ;;
                 *) F3="-D DISABLE_BATTERY -D DISABLE_BLE" ;; esac
    export PLATFORMIO_BUILD_FLAGS="$PLATFORMIO_BUILD_FLAGS $F3"
fi
echo "[$L] PLATFORMIO_BUILD_FLAGS='$PLATFORMIO_BUILD_FLAGS'"
[ -n "$V$NCETH" ] && git -C $W diff --stat | tail -1
scripts/build.sh --env qemu-headless-extradio-gpsd 2>&1 | tail -3
cp $W/.pio/build/qemu-headless-extradio-gpsd/flash.bin $S/flash-$L.bin
sha256sum $S/flash-$L.bin
echo "[$L] BUILD DONE"
