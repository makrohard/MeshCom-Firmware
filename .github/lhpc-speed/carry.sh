#!/bin/bash
# carry.sh: bring the lhpc-speed carry branch up to icssw-org dev by a MERGE (forward only).
# lhpc-speed is never rewritten: LHPC and its release bot pin commits on it, and a rebase would make
# a pinned commit fall off the branch. The merge result stays LOCAL as branch "candidate"; the workflow
# pushes it (fast-forward only) after the build and the QEMU proof passed.
# Output (GITHUB_OUTPUT or stdout): state=merged|unchanged|retire|conflict, head, base, old_head.
set -euo pipefail
UPSTREAM_URL="${UPSTREAM_URL:-https://github.com/icssw-org/MeshCom-Firmware.git}"
CARRY_BRANCH="${CARRY_BRANCH:-lhpc-speed}"
out() { echo "$1" | tee -a "${GITHUB_OUTPUT:-/dev/null}"; }

git remote get-url upstream >/dev/null 2>&1 || git remote add upstream "$UPSTREAM_URL"
git fetch -q upstream dev
git fetch -q origin "$CARRY_BRANCH"
old_head=$(git rev-parse "origin/$CARRY_BRANCH")
base=$(git rev-parse upstream/dev)
git checkout -q -B candidate "origin/$CARRY_BRANCH"

state=""
if git merge-base --is-ancestor upstream/dev candidate; then
    state=unchanged                           # nothing new upstream
elif ! git -c user.name=lhpc-speed-bot -c user.email=lhpc-speed-bot@users.noreply.github.com \
        merge -q --no-ff --no-edit -m "Merge icssw-org dev ${base:0:8} into $CARRY_BRANCH" upstream/dev; then
    git merge --abort || true
    state=conflict                            # a person decides; nothing is pushed
fi
# Retire: the carried changes are all upstream when the merged tree equals upstream dev's tree.
if [ "$state" != conflict ] && git diff --quiet upstream/dev candidate; then
    state=retire
fi
[ -n "$state" ] || state=merged
head=$(git rev-parse candidate)
out "state=$state"; out "head=$head"; out "base=$base"; out "old_head=$old_head"
git diff --stat upstream/dev candidate || true
