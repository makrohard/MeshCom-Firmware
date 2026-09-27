#!/bin/bash
# idle re-run of the 9-site harness (the counting run): one QEMU at a time, slot 0.
cd ~/claude/agent5-allenvs/qemu/sites; O=~/claude/meshcom-prs-evidence/all-envs/qemu/sites/idle-run.out
for t in base pr1 merge; do
  python3 qemu-sites.py ../flash-$t-instr.bin idle-$t-instr message position ping pong ack hey injpos apppos --slot 0 > /dev/null 2>&1; rc=$?; echo "$(date -u +%T) $t-instr rc=$rc load=$(cut -d' ' -f1 /proc/loadavg)" >> $O
  python3 qemu-sites.py ../flash-$t-xml.bin idle-$t-xml telemetry --slot 0 > /dev/null 2>&1; rc=$?; echo "$(date -u +%T) $t-xml rc=$rc load=$(cut -d' ' -f1 /proc/loadavg)" >> $O
done; echo "$(date -u +%T) SITES-IDLE-DONE" >> $O
