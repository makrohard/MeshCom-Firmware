# Agent 5 plan: all MeshCom envs × our three PRs (build + function proof)

Brief: `../AGENT5-BRIEF.md`. Report: `../ALL-ENVS-REPORT.md`. Working logs: this directory.
Build trees and container caches: `~/claude/agent5-allenvs/`. They live on /home because /tmp is tmpfs with 15 G free.

## Trees (five, each a clean clone of ~/claude/meshcom-prs at a fixed SHA, checked before every build)

| label | commit | what |
|---|---|---|
| base | cf215b5d | plain upstream dev (the stock baseline; upstream/dev re-checked at start and end) |
| pr1 | 3f936a63 | PR1 #1164 alone |
| pr2 | 84e6e308 | PR2 #1165 alone |
| pr3 | 9d8cbdbb | PR3 #1166 alone |
| merge | a7957f7a (tree 58d99cd9) | base + PR1 + PR2 + PR3 |

## Steps

0. **Setup, about 45 min.**
   - Create the trees and check their SHAs and trees.
   - Check that all 6 merge orders of PR1/PR2/PR3 merge cleanly (`git merge-tree`, all ending in tree 58d99cd9).
   - Read-only `gh pr view --json mergeable,mergeStateStatus` for #1164–#1166.
   - Build one container image: ubuntu:24.04 + Python 3.11 + `pip install --upgrade platformio intelhex`
     + `pio platform install nordicnrf52 espressif32` + the T-Beam Supreme board json, all as in `meshcom-ci.yml`.
     Record the platform and toolchain versions.
1. **Upstream's CI job, verbatim, in the container, about 2–3 h.** Plain `pio run` (all 32 default_envs), then the
   three UF2 steps, then the rename step, then a check that every release-action artifact exists. Runs on base and on
   merge; they are 2 parallel builds, which is the PC limit.
   - PASS means the merge is green wherever base is green.
   - Environment failures are fixed in the container, never in the firmware tree, and both trees are then re-run.
2. **Each PR alone, about 3 h.** The same container image and `pio run`, on pr1, pr2 and pr3.
   - `t5_epaper` (commented out upstream) is built by `pio run -e t5_epaper` on all five trees, reported separately.
3. **Analysis, about 1.5 h.**
   - Per env, per tree: flash/RAM and the headroom to the partition or linker limit.
   - The compiler-warning diff against base; a NEW warning on a line we touched is a finding.
   - A preprocessor-derived table of which of our hunks are active per env.
   - Compile-level proof from the ELF and map files: symbols (`save_msgid`, the call sites) and strings
     ("disabled (DISABLE_BLE)", the unchanged-setcall text, the Ethernet net-console gate), present where active and
     absent where not.
4. **Flag variants, about 2 h.** `-D DISABLE_BATTERY` and `-D DISABLE_BLE`, each alone, on pr3 and merge, for every env.
   - nRF52 (heltec_t114, t_echo, wiscore_rak4631) and E22_XML-DevKitC get extra care: a symbol-level check that each
     flag does what is claimed (or nothing, where it is not meant for the board).
   - Base is also built with the flags, to show they are new.
5. **QEMU function proof, about 3–4 h, on an idle PC (no parallel builds).**
   - Every change row (F1–F3, D1–D3, G1/G2, the nine PR1 sites, PR2, PR3 a/c/d including the `eth` image) runs on
     each PR alone and on the merge, with the stock base as the negative control.
   - Tools: `build-image-ci.sh` variants, `proof.py p1` / `setcall`, `qemu-p1.py`, `qemu-xml.py`, `qemu-sethop.py`,
     `qemu-netconsole.py`. I use them as copies in my own directory, so agent 1's `qemu-images-pr12/` is not
     touched.
   - Rows the emulator cannot reach (T-Deck / Pro UI, nRF52, S3-only) name why and point to the existing hardware
     evidence; any other such row is an open gap. No hardware without a slot.
6. **Table, review and report, about 1.5 h.**
   - The env × change table goes to agent 1 for review, then `ALL-ENVS-REPORT.md` is written and self-audited.
   - The short summary goes to the handler.

Estimate: 13–15 h wall clock.

**IMMEDIATE PING** to voice-pinned-source-fix for any OURS "does not compile / does not work": env, PR, step, first
error lines and log path. Nothing gets fixed.
