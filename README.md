# agent5-evidence: all-envs build and QEMU function proof of MeshCom PRs #1164 / #1165 / #1166

Evidence bundle for `report/ALL-ENVS-REPORT.md`. It is an orphan branch, with no history shared with any firmware
branch. The three PRs on icssw-org/MeshCom-Firmware are not touched by this branch.

- `report/ALL-ENVS-REPORT.md`: the report (v2). Its "path map" says where each path it names lives here.
- `scripts/ci/`: the upstream-CI reproduction (Containerfile, ci-job.sh, run-ci.sh), the flag builds (run-pio.sh),
  the deterministic object rebuilds (det-obj*.sh, flag-obj.sh) and the analysis (analyse.py, whose `_norm()` is the
  layout-only classifier; layout_audit.py, the strict re-check of every layout-only section; relax_check.py;
  flagdiff.py; safeboot_proof.sh).
- `scripts/qemu/`: the image build (build-image-ci2.sh with its variants), the harness scripts (proof.py, qemu-*.py,
  sites/qemu-sites.py) and the TEST-ONLY scaffolding (testhack-*.py, drop-*.py, and xml-testhook-7ba919cb.patch,
  never part of a PR).
- `evidence/builds/`: every build log; `INVALID-*` files are kept for transparency and are explained in the report.
- `evidence/analysis/`: object-diff outputs, flag diffs, sizes, warnings, the env × change table, working notes.
  v3 additions: the strict re-check of every LAYOUT-ONLY section (`layout-only-audit.txt`, raw before/after
  disassembly in `layout-only-raw-diffs.txt`, checker self-test `layout-selftest.txt`, branch-relaxation proof
  `layout-relaxation-check.txt`), the raw safeboot proof (`safeboot-proof.txt`) and the heltec_t114 size ledger
  (`t114-size-ledger.txt`).
- `evidence/objects/`: sha256 of every `src/**/*.o`, the ELF and the firmware file per env and tree, plus one digest
  over all objects of each env build.
- `evidence/qemu/`: image build logs + the image sha256 manifest (`images/`), the counting run on the idle PC
  (`idle/`), the per-site harness runs (`sites/`, table in `results-idle.md`).
- `evidence/controls/`: the old-PR1 control for the `{SET}` regression (patches, image build log, image hash).

Firmware images are not included; they are identified by sha256 in `evidence/qemu/images/manifest-sha256.txt`.
Paths inside logs are the author's local paths at run time.
