#!/bin/bash
# sched.sh: runs queue.txt through run-pio.sh, at most MAX containers named a5-* at 4 CPUs each (sum <= 24).
# A line's tree must be idle: for the six ci-job trees, its ci-<tree>.log has "# exit"; no other job of that tree runs.
MAX=6; E=~/claude/meshcom-prs-evidence/all-envs; cd ~/claude/agent5-allenvs/ci
declare -A busy
mapfile -t Q < queue2.txt; done_=()
while :; do
  left=0
  for i in "${!Q[@]}"; do
    [ -z "${Q[$i]}" ] && continue; left=1
    set -- ${Q[$i]}; t=$1; f=${2//_/ }; e=$3
    n=$(podman ps --format '{{.Names}}' | grep -c '^a5-'); [ $n -ge $MAX ] && break
    [ -f $E/ci-$t.log ] && ! grep -q '^# exit' $E/ci-$t.log && continue
    pgrep -f "run-pio.sh $t " >/dev/null && continue
    echo "$(date -u +%T) start: ${Q[$i]}"; nohup ./run-pio.sh $t "$f" 4 $e >/dev/null 2>&1 & Q[$i]=""; sleep 30
  done
  [ $left = 0 ] && break; sleep 30
done
wait; echo "$(date -u +%T) queue done"
