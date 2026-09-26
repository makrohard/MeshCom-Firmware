# lhpc-speed: temporary carry of the MeshCom speed PRs for LHPC

`lhpc-speed` = icssw-org `dev` + two changes that make MeshCom fast under QEMU (the LHPC MeshCom stack):

- save settings where they change, and after a transmission save only the message counter;
- `--setcall` with the unchanged callsign saves nothing and does not reboot.

LHPC and its release bot pin commits on `lhpc-speed` until icssw-org has merged both changes.
Retire tracking: issue #1.

## Weekly run (`.github/workflows/lhpc-speed.yml`, Mondays 03:17 UTC, or by hand)

1. `carry.sh` merges icssw-org `dev` into `lhpc-speed` locally. The branch only ever moves
   **forward**: it is never rebased, because a rewrite would make a pinned commit fall off it.
2. The candidate is built for 11 boards and checked under QEMU (`proof.py`). QEMU is Espressif's
   `esp-develop` tag plus the downstream patches in `makrohard/meshcom-qemu-raspi` `patches/qemu`,
   built in CI and cached. The emulator image uses the meshcom-qemu-raspi overlay.
3. Outcomes:
   - **green**: `lhpc-speed` is fast-forwarded (never forced);
   - **red or merge conflict**: an issue labelled `lhpc-speed-red`, nothing pushed;
   - **retire**: after the merge nothing is left to carry (tree equals icssw-org `dev`), so a comment on
     issue #1.

The QEMU proof checks, on a hard power-off: the GPS fix is saved before any transmission,
`--aprsmc` survives, the message counter keeps counting, the node restarts from the saved fix; and
for `--setcall`: a new callsign or a changed shortname still saves and reboots, an unchanged one does not.
`testhack-short.py` adds a test-only step to the emulator image (it stores a custom shortname, as the
server CONF path does); it is never part of the firmware.

## Retire (when issue #1 says so)

1. LHPC: point the MeshCom source back to icssw-org at a commit containing the changes (manifest and
   release-bot policy), release, with a changelog note that releases pinned to this fork must update
   before a MeshCom source rebuild.
2. Remove this directory and the workflow.
3. Delete the `lhpc-speed` branch.
4. Delete the fork only when no other fork-only branch or PR is still needed (the PR branches until
   icssw-org has merged or declined them). Releases pinned to the fork are covered by step 1's note.

A RETIRE comment starts step 1; it is not by itself permission to delete the fork.
