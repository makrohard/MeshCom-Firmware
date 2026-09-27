#!/bin/bash
# run-rows.sh: functional QEMU rows (not the loop-gap timing), one queue per script (a fixed port each), queues in parallel.
Q=~/claude/agent5-allenvs/qemu; EQ=/home/makro/claude/meshcom-prs-evidence/all-envs/qemu; cd $Q
export QEMU=/home/makro/claude/qemu-cache-pr/b-up/qemu-system-xtensa RELAY=/home/makro/claude/meshcom-qemu-raspi/scripts/gps-relay.py FIX=/home/makro/claude/meshcom-qemu-raspi/fixtures/gps/valid_fix.nmea
pp() { m=$1; shift; for t in "$@"; do WORK=$EQ/proof-$t python3 proof.py $m flash-$t.bin > $EQ/proof-$m-$t.log 2>&1; echo "proof $m $t rc=$? $(grep -c PASS $EQ/proof-$m-$t.log) PASS $(grep -c FAIL $EQ/proof-$m-$t.log) FAIL"; done; }
sc() { s=$1; shift; for t in "$@"; do python3 $s flash-$t.bin $t > $EQ/${s%.py}-$t.out 2>&1; echo "$s $t rc=$?"; done; }
pp p1 base-plain pr1-plain merge-plain &
pp setcall base-short pr2-short merge-short &
sc qemu-xml.py base-xml pr1-xml merge-xml &
sc qemu-sethop.py base-instr pr1-instr merge-instr &
sc qemu-netconsole.py base-eth base-all pr3-all merge-plain pr3-drop3 merge-drop3 &
sc qemu-measure.py base-plain base-nobatt base-nobatt-flag base-noble base-noble-flag base-all pr3-all merge-plain pr3-drop3 pr3-drop3-batt pr3-drop3-ble merge-drop3 merge-drop3-batt merge-drop3-ble &
wait; echo ALL-ROWS-DONE
