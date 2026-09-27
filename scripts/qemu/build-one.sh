#!/bin/bash
# build-one.sh <tree> <variant>: one QEMU image from branch a5-<tree> of agent5-allenvs/base
t=$1; v=$2; [ "$v" = plain ] && vv="" || vv=$v
case $t in pr3|merge|pr13|pr23) export NCETH=1 ;; esac
L=$t-$v; LOG=~/claude/meshcom-prs-evidence/all-envs/qemu/build-$L.log
bash ~/claude/agent5-allenvs/qemu/build-image-ci2.sh $L a5-$t $vv > $LOG 2>&1; echo "[$L] rc=$? NCETH=${NCETH:-0} $(tail -1 $LOG)"
