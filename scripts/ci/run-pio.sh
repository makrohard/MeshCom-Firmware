#!/bin/bash
# run-pio.sh <tree> <flags|-> [cpus] [envs...]: plain `pio run` (all default_envs, or the given -e envs) in the CI image,
# with PLATFORMIO_BUILD_FLAGS=<flags> (- = none). Log: all-envs/pio-<tree>.log (or pio-<tree>-<env>.log for one env).
L=$1; F=$2; CPUS=${3:-6}; shift 3; T=~/claude/agent5-allenvs/$L; E=~/claude/meshcom-prs-evidence/all-envs
[ "$F" = - ] && F=""
ARGS=""; for e in "$@"; do ARGS="$ARGS -e $e"; done
if [ $# -gt 1 ]; then LOG=$E/pio-$L-${LBL:-envs$#}.log; else LOG=$E/pio-$L${1:+-$1}.log; fi
[ -z "$(git -C $T status --porcelain --untracked-files=no -- . ':!safeboot.bin' ':!safeboot-s3.bin')" ] || { echo "tree $L dirty" >&2; exit 2; }
{ echo "# pio run$ARGS on $L: HEAD $(git -C $T rev-parse HEAD) tree $(git -C $T rev-parse HEAD^{tree}) PLATFORMIO_BUILD_FLAGS='$F' image $(podman image inspect -f '{{.Id}}' a5-meshcom-ci:1 | cut -c1-12) cpus=$CPUS start $(date -u +%FT%TZ)"
  podman run --rm --name a5-pio-$L-$RANDOM --cpus $CPUS --security-opt label=disable --network none -v a5-piohome:/root/.platformio -e PLATFORMIO_BUILD_FLAGS="$F" -v $T:/ws a5-meshcom-ci:1 bash -c "cd /ws && python --version && pio --version && pio run$ARGS"
  echo "# exit $? end $(date -u +%FT%TZ)"; } > $LOG 2>&1
