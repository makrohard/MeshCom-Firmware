#!/bin/bash
# run-idle.sh: the counting QEMU runs (idle PC, no build lanes). Two queues at a time, each a fixed-port script.
# Output: all-envs/qemu/idle/<script>-<image>.log; manifest.txt with the image sha256 and the QEMU binary.
set -u
Q=~/claude/agent5-allenvs/qemu; EQ=~/claude/meshcom-prs-evidence/all-envs/qemu/idle; mkdir -p $EQ; cd $Q
export QEMU=/home/makro/claude/qemu-cache-pr/b-up/qemu-system-xtensa RELAY=/home/makro/claude/meshcom-qemu-raspi/scripts/gps-relay.py FIX=/home/makro/claude/meshcom-qemu-raspi/fixtures/gps/valid_fix.nmea
{ echo "# idle QEMU run $(date -u +%FT%TZ) on $(hostname)"; echo "QEMU $QEMU sha256 $(sha256sum < $QEMU | cut -c1-16) $($QEMU --version | head -1)"
  for f in flash-*.bin; do echo "$f $(sha256sum < $f | cut -c1-16)"; done; } > $EQ/manifest.txt
busy() { ps -eo args | grep -c '[a]5-pio\|[a]5-ci\|[a]5-det'; }
pp() { m=$1; shift; for t in "$@"; do rm -rf $EQ/proof-$t; WORK=$EQ/proof-$t python3 proof.py $m flash-$t.bin > $EQ/proof-$m-$t.log 2>&1; echo "$(date -u +%T) proof $m $t rc=$? load=$(cut -d' ' -f1 /proc/loadavg)"; done; }
sc() { s=$1; shift; for t in "$@"; do python3 $s flash-$t.bin idle-$t > $EQ/${s%.py}-$t.log 2>&1; echo "$(date -u +%T) $s $t rc=$? load=$(cut -d' ' -f1 /proc/loadavg)"; done; }
# queue A (PR1 + PR2 rows)          queue B (PR3 rows)
( pp p1 base-plain pr1-plain merge-plain
  sc qemu-xml.py base-xml pr1-xml merge-xml
  sc qemu-sethop.py base-instr pr1-instr merge-instr
  pp setcall base-short pr2-short merge-short
  sc qemu-p1.py base-instr pr1-instr merge-instr ) > $EQ/queueA.out 2>&1 &
( sc qemu-netconsole.py base-eth base-all pr3-all merge-plain pr3-drop3 merge-drop3
  sc qemu-measure.py base-plain base-nobatt base-nobatt-flag base-noble base-noble-flag base-all pr3-all merge-plain pr3-drop3 pr3-drop3-batt pr3-drop3-ble merge-drop3 merge-drop3-batt merge-drop3-ble ) > $EQ/queueB.out 2>&1 &
wait; echo "$(date -u +%T) IDLE-RUN-DONE" >> $EQ/queueA.out
