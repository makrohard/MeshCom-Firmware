#!/bin/bash
# run-ci.sh <label> [cpus]: upstream CI job on tree ~/claude/agent5-allenvs/<label> in a fresh container.
L=$1; CPUS=${2:-6}; T=~/claude/agent5-allenvs/$L; E=~/claude/meshcom-prs-evidence/all-envs; LOG=$E/ci-$L.log
[ -z "$(git -C $T status --porcelain --untracked-files=no)" ] || { echo "tree $L dirty" >&2; exit 2; }
rm -rf $T/.pio $T/uf2conv.py* $T/uf2families.json*
{ echo "# ci-job on $L: HEAD $(git -C $T rev-parse HEAD) tree $(git -C $T rev-parse HEAD^{tree}) image $(podman image inspect -f '{{.Id}}' a5-meshcom-ci:1 | cut -c1-12) cpus=$CPUS start $(date -u +%FT%TZ)"
  podman run --rm --name a5-ci-$L --cpus $CPUS --security-opt label=disable -v $T:/ws -v $PWD/ci-job.sh:/ci-job.sh:ro a5-meshcom-ci:1 bash /ci-job.sh
  echo "# exit $? end $(date -u +%FT%TZ)"; } > $LOG 2>&1
