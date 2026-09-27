# MeshCom PRs #1164 / #1165 / #1166: every default env built, and every change row proven in the emulator

Author: agent 5 (session claude-a2). Supervisor: agent 1 (claude-1e). Reports to: the masterplan handler.

# AUDIT NOW — for Audit Agent 5

## Audit instructions (read first)

You are a fresh, independent auditor. Your input is ONE file: this one. Audit only this top section "AUDIT NOW".

- **Read-only.** Change nothing, push nothing, post nothing anywhere.
- **Do not touch the pull requests.** #1164, #1165 and #1166 on icssw-org/MeshCom-Firmware are already posted
  upstream. No comment, review, label, or push to their branches.
- **What to judge, per item below:**
  1. Correctness: does the evidence show what the sentence claims, and nothing more?
  2. Evidence: is every claim backed by a command, a log and a pinned link? Is any sentence stronger than its
     evidence?
  3. Completeness: if you have to search for something, that is a finding.
  4. Negative controls: is "ours" separated from pre-existing upstream behaviour everywhere?
- **Your answer:**
  - Verdict per item: **GREEN** / **GREEN with notes** / **RED** (blocker).
  - Findings numbered, each with file:line or link, why it matters, and the smallest fix.
  - Say explicitly what you did NOT check.
- **Project context in three lines:**
  - Three PRs were offered to the MeshCom firmware maintainer (Kurt, icssw-org): PR1 `save_msgid()` instead of a
    full `save_settings()` after every transmission, plus the saves that the old per-TX full save used to cover;
    PR2 an unchanged `--setcall` saves nothing and does not reboot; PR3 (three commits) Ethernet net console,
    `-D DISABLE_BATTERY`, `-D DISABLE_BLE`.
  - They were posted after building only 11 of 32 default envs. This report is the build proof on ALL envs and the
    function proof in QEMU.

## v2: answers to Audit Agent 5 (verdict RED on the evidence package; no code defect found)

| finding | status | where |
|---|---|---|
| F1: primary evidence not in the package | fixed: one pinned bundle with every script, log, table and manifest | "Pinned inputs" → this branch + path map |
| F2: the LAYOUT-ONLY classifier cannot be reviewed | fixed: `scripts/ci/analyse.py` (the classifier is `_norm()`), `det-obj*.sh`, raw object hashes `evidence/objects/`, the raw diff `evidence/analysis/funcs-all.txt` | bundle |
| F3: the stock flag control covered only `esp32_main.cpp.o` | fixed with data: an all-object comparison (framework + libraries + src), 0 code sections differ on 30/30 app envs; the wording narrowed where it concerns one object | item 6 |
| F4: the `{SET}` old-PR1 control was outside this package | fixed: old PR1 `c4f508b3` re-run on the idle PC in this evidence set (value lost: NVS 4, reboot 4, after TX 4); patches, build log and image hash included | item 9 ②, `evidence/controls/` |
| F5: QEMU harness / test hooks not inspectable | fixed: `scripts/qemu/` (all harness scripts, `testhack-*.py`, `drop-*.py`, the `--xmltz` hook patch), image build logs and the sha256 manifest | bundle |
| F6: "reproduced CI" wording | fixed: "upstream CI workflow steps, reproduced in a controlled container" | item 2 |
| F7: "any new warning" wording | fixed: "any warning emitted under upstream's enabled warning flags" (ESP32 vs nRF52 sets named) | item 3 |

The audit input is now this report **plus** the pinned bundle it links. Both are read-only for the auditor.

## Pinned inputs

| what | pin | link |
|---|---|---|
| upstream base (`dev`, the PRs' base) | `cf215b5d669a94e1c66c86bae21c76f4dff04061` | https://github.com/icssw-org/MeshCom-Firmware/tree/cf215b5d669a94e1c66c86bae21c76f4dff04061 |
| upstream CI workflow (the reference job) | same | https://github.com/icssw-org/MeshCom-Firmware/blob/cf215b5d669a94e1c66c86bae21c76f4dff04061/.github/workflows/meshcom-ci.yml |
| default_envs (32 active; `t5_epaper` commented out) | same | https://github.com/icssw-org/MeshCom-Firmware/blob/cf215b5d669a94e1c66c86bae21c76f4dff04061/platformio.ini#L16-L58 |
| PR1 #1164 head `pr1-persist` | `3f936a638cc58799c9aa8e439a666a68173d65d2` | https://github.com/icssw-org/MeshCom-Firmware/pull/1164 · https://github.com/makrohard/MeshCom-Firmware/commit/3f936a638cc58799c9aa8e439a666a68173d65d2 |
| PR2 #1165 head `pr2-setcall-unchanged` | `84e6e3083fb0db847150845d408655864551d4c5` | https://github.com/icssw-org/MeshCom-Firmware/pull/1165 · https://github.com/makrohard/MeshCom-Firmware/commit/84e6e3083fb0db847150845d408655864551d4c5 |
| PR3 #1166 head `pr3` (3 commits) | `9d8cbdbbc7f887e5689d0b704f6dfd255846ce5b` | https://github.com/icssw-org/MeshCom-Firmware/pull/1166 · https://github.com/makrohard/MeshCom-Firmware/commit/9d8cbdbbc7f887e5689d0b704f6dfd255846ce5b |

- **The PR heads sit on `f7f1fe9c`.** `cf215b5d` = `f7f1fe9c` plus one docs file (`docs/wiederholungen.md`).
- **"PR alone" therefore means a local merge commit of `cf215b5d` + that PR head**, which is exactly what GitHub
  would produce. The scratch merge commits (never pushed) are:

  | tree | commit | tree sha |
  |---|---|---|
  | base | `cf215b5d` | `3e2c9de6` |
  | pr1 | `e6e8c95d` | `4f1c0e80` |
  | pr2 | `97fa8df1` | `8f693de4` |
  | pr3 | `eacd07b3` | `f8294acd` |
  | pr12 (PR1+PR2) | `d3087d9e` | `e4288d45` |
  | merge (all three) | `a7957f7a` | `58d99cd9` |

- `upstream/dev` was re-checked at the start: `cf215b5d` (unchanged).
- The trees are clean clones: `/home/makro/claude/agent5-allenvs/<tree>`.
- **All evidence is in ONE pinned bundle** (v2, audit F1/F2/F5): the orphan branch `agent5-evidence` on
  makrohard/MeshCom-Firmware at commit (this branch; the commit SHA is given in the copy of this report outside the bundle). It contains every
  script, log, table, manifest and object hash this report names. There are no firmware images: they are pinned by
  sha256 in `evidence/qemu/images/manifest-sha256.txt`.
- **Path map** (a path in this report → a path in the bundle):

  | in this report | in the bundle |
  |---|---|
  | `ci-*.log`, `pio-*.log`, `det-*.log`, `flagobj-*.log`, `INVALID-*` | `evidence/builds/` |
  | `funcs-*.txt`, `flagdiff.txt`, `sizes*`, `warnings.txt`, `env-change-table.md`, `NOTES.md`, `PLAN.md`, `envs*.txt` | `evidence/analysis/` |
  | `../hunk-env-map.md` (agent 1's prediction) | `evidence/analysis/hunk-env-map-agent1-prediction.md` |
  | `qemu/idle/…`, `qemu/qemu-*-idle-*/`, `qemu/qemu-m-idle-*/`, `qemu/qemu-nc-idle-*/` | `evidence/qemu/idle/` |
  | `qemu/sites/idle-*/`, `sites/…` (logs) | `evidence/qemu/sites/` (per-site table: `results-idle.md`) |
  | image build logs `qemu/build-*.log`, image hashes `manifest.txt` | `evidence/qemu/images/` |
  | object hashes (F2) | `evidence/objects/<tree>.sha256` (every `src/**/*.o` + ELF/bin + one digest over ALL objects per env) |
  | the old-PR1 control (F4) | `evidence/controls/` |
  | scripts `ci/…` | `scripts/ci/` |
  | scripts `qemu/*.sh`, `qemu/*.py`, the xml test hook | `scripts/qemu/` (`xml-testhook-7ba919cb.patch` = the TEST-ONLY `--xmltz` hook, never in a PR) |
  | scripts `qemu/sites/*.py` | `scripts/qemu/sites/` |
- **Scripts:** `/home/makro/claude/agent5-allenvs/ci/` (run-ci.sh, ci-job.sh, run-pio.sh, det-obj.sh, flag-obj.sh,
  analyse.py, flagdiff.py) and `/home/makro/claude/agent5-allenvs/qemu/` (build-image-ci2.sh, build-one.sh,
  run-idle.sh, sites/qemu-sites.py).

## Item 1 — Merge orders and mergeability

- All **6 merge orders** of PR1/PR2/PR3 onto `cf215b5d` merge without conflict (real `git merge-tree` +
  `commit-tree` chains) and all produce the same tree **`58d99cd9`**.
- **Pairs:** only PR1 and PR2 share a source file (`src/command_functions.cpp`). PR1+PR3 and PR2+PR3 share no
  source file, so of the pairs only PR1+PR2 was built (tree `pr12`, handler's instruction). PR1+PR2 and PR2+PR1
  give the same tree `e4288d45`.
- **GitHub (read-only `gh pr view --json mergeable,mergeStateStatus`):** #1164/#1165/#1166 are `MERGEABLE`, state
  `BLOCKED` (awaiting review).
- Evidence: `NOTES.md` section "Trees".

## Item 2 — Upstream CI workflow steps, reproduced in a controlled container, on six trees: ALL GREEN

**Method (`ci/run-ci.sh` + `ci/ci-job.sh`):**
- Container image `a5-meshcom-ci:1` (`ci/Containerfile`): ubuntu:24.04, Python **3.11.16** (deadsnakes; the workflow
  pins `3.11`), then as in the workflow: `pip install --upgrade platformio` (→ PlatformIO Core **6.2.0**),
  `pip install --upgrade intelhex`, `pio platform install nordicnrf52` (11.0.0) and `espressif32` (7.1.3), and the
  T-Beam Supreme board json downloaded into `~/.platformio/platforms/espressif32/boards/`.
- Then, verbatim from the workflow: `pio run` (all default_envs), the three UF2 conversion steps (uf2conv.py fetched
  as in the workflow), and the "Rename Files" step (its `run:` string extracted from the workflow file itself).
- The release-action step is replaced by an **existence check of every artifact the release-action lists**.
  This check is the real evidence for the rename step: upstream's "Rename Files" joins its `mv`s with `&`, so the
  step's rc would stay 0 even if an `mv` failed.
- The envs pin their own platforms: espressif32 6.13.0 / 6.6.0 / 6.5.0, nordicnrf52 10.12.0, and Tasmota
  2026.02.30 for the two safeboots. They were installed by `pio run` exactly as in CI.

| tree | log | `pio run` | UF2 ×3 | Rename | artifacts missing |
|---|---|---|---|---|---|
| base `cf215b5d` | `ci-base.log` | 32/32 SUCCESS | rc 0 | rc 0 | 0 |
| pr1 | `ci-pr1.log` | 32/32 SUCCESS | rc 0 | rc 0 | 0 |
| pr2 | `ci-pr2.log` | 32/32 SUCCESS | rc 0 | rc 0 | 0 |
| pr3 | `ci-pr3.log` | 32/32 SUCCESS | rc 0 | rc 0 | 0 |
| pr12 | `ci-pr12.log` | 32/32 SUCCESS | rc 0 | rc 0 | 0 |
| merge `58d99cd9` | `ci-merge.log` | 32/32 SUCCESS | rc 0 | rc 0 | 0 |

- Each log's first line records the HEAD, tree sha and image id. `grep -c '\[SUCCESS\]' ci-<tree>.log` gives 32;
  `grep '=== RESULT' ci-<tree>.log` gives the step results.
- **Both safeboot envs build** on every tree. The earlier local failures (intelhex, Tasmota penv/uv,
  package-postinstall) were local-venv problems (Python 3.14) and do not occur in the CI container.
- **Note (pre-existing upstream behaviour, not ours):** the safeboot post-script (`tools/safeboot.py`) rewrites the
  tracked `safeboot.bin` / `safeboot-s3.bin` in the tree on every build, base included.

## Item 3 — Compiler warnings: no new warning anywhere

- `ci/analyse.py warn` diffs the warning lines per env: tree vs base, keyed on file + the source line's text + the
  message, so line shifts from our hunks don't count as new.
- **Result: 0 NEW and 0 GONE warning lines on all 32 envs × 5 trees** (`warnings.txt`: `grep -c 'NEW x'` = 0).
- **Stronger than a diff:** upstream builds `src/` with `-Werror` and `-Wformat=2`:
  - `[esp32]` `build_src_flags`, platformio.ini:238-242
    (https://github.com/icssw-org/MeshCom-Firmware/blob/cf215b5d669a94e1c66c86bae21c76f4dff04061/platformio.ini#L238-L242);
  - `[nrf52_base]`, platformio.ini:132-135
    (https://github.com/icssw-org/MeshCom-Firmware/blob/cf215b5d669a94e1c66c86bae21c76f4dff04061/platformio.ini#L132-L135).

  Any warning emitted under upstream's enabled warning flags would have failed these builds:
  - ESP32 `[esp32]`-derived envs: `-Wall -Wextra -Wformat=2 -Werror`;
  - nRF52: `-Wformat=2 -Werror`, without `-Wall/-Wextra`.

  The three nRF52 envs (heltec_t114, t_echo, wiscore_rak4631) are green on every tree.

## Item 4 — Sizes and headroom

`sizes.tsv` / `sizes-table.md` hold the flash and RAM of every env × tree, from pio's own
`RAM:` / `Flash: … used N bytes from M bytes`. The limit is pio's maximum program size (the app partition).

- **Merge vs base: flash +0 … +448 B, RAM +0 or +8 B.**
- **Lowest headroom after the merge:**

  | env | flash free after merge | cost of the merge |
  |---|---|---|
  | wiscore_rak4631 | 146184 B (17.93 %) | +32 B |
  | t_echo | 188788 B (23.16 %) | +112 B |
  | heltec_t114 | 217992 B (26.74 %) | +448 B |

  Every other env has ≥ 47 % free. No env's headroom becomes critical.
- **heltec_t114 +448 B, explained** (`nm -S` of the ELFs, base vs pr2):
  - `commandAction()` is +124 B (the PR2 code).
  - +368 B are an ArduinoJson template instance (a weak symbol, `StringPool::add<RamString>`) that the compiler
    instantiates differently once `commandAction()` changes. This is a code-generation side effect in library
    code, not new logic.
  - RAK4631 and t_echo don't show it (commandAction +4 / +100 B).
- **Build-date noise:** trees without any code change on an env (e.g. pr3 on RAK4631, t_deck_plus) show ±16 B. CI
  builds are not deterministic, because `__DATE__`/`__TIME__` is compiled in (`command_functions.cpp:136-141` and
  five other files). Item 5's deterministic object diff is the authoritative "no code change" evidence.

## Item 5 — Object diff per PR: every PR changes exactly its intended functions, per board family

**Method:**
- The objects that embed the build date were rebuilt with `SOURCE_DATE_EPOCH=1790000000` in the same container
  (`ci/det-obj.sh`): command_functions, esp32_main, tdeck_main, web_functions, rtc_functions, nrf52_functions.
  Reproducibility was checked: two rebuilds are byte-identical.
- Then `ci/analyse.py funcs` compares every code section of every `src/**/*.o`, per env, tree vs base, using the
  right objdump (esp32 / esp32s3 / arm-none-eabi, chosen from the ELF header).
- It classifies each difference as NEW / GONE / CHANGED, or as LAYOUT-ONLY: branch offsets, alignment padding,
  narrow/wide Xtensa encodings, compiler-numbered labels such as `CSWTCH.N`, whitespace.
- Scope: 30 app envs (the two safeboots are item 7). Full output: `funcs-all.txt`; grouped: `funcs-summary.txt`.

| tree | what changes (non-layout) |
|---|---|
| **PR1** | ESP32 (27 envs): the 9 TX-site functions (sendPing, SendPong, sendMessage, sendInjectedPosition, sendPosition, sendAPPPosition, SendAckMessage, sendHey, sendTelemetry), `sendDisplayText` (`{SET}` save), `commandAction` (`--aprsmc` save), NEW `save_msgid` + `save_position`, and `WZ_GPS_Loop` on every ESP32 env with ENABLE_GPS (not wireless-paper); `decodeTinyXML` only on E22_XML-DevKitC; `tab_kbl_button_event_cb` / `tab_standby_button_event_cb` / `keypad_read` only on t_deck + t_deck_plus; `keypad_loop` only on t_deck_pro. **nRF52 (3 envs): only `commandAction` + `sendDisplayText`.** The 9 sites are code-identical there, as intended: on nRF52 `save_msgid()` is `#define`d to `save_settings()` (`src/nrf52/WisBlock-API.h:616` in the merge). |
| **PR2** | `commandAction` only, on all 30. On heltec_t114 also the ArduinoJson template instance from item 4. |
| **PR3** (no flags) | `loopNetConsole` only, and only on the two `HAS_ETHERNET` boards (T-ETH-ELITE_1262, LilyGo_T_Connect_Pro). On the other 28 app envs PR3 is **code-identical to base**, `esp32_main` included. |
| **PR1+PR2**, **merge** | exactly the union of the above (checked env by env in `funcs-summary.txt`) |

**Env × change table** (verified from the objects, merge vs base; `env-change-table.md`):
- Y = the code changes in the binary.
- ≡ = compiled, but the machine code is identical (by design).
- – = not compiled for this env.

| env | PR1 9 TX sites | PR1 {SET} | commandAction (PR1 --aprsmc / PR2) | PR1 save_msgid+save_position | PR1 GPS save | PR1 XML utcoff | PR1 T-Deck UI | PR1 T-Deck Pro keys | PR3a net console | PR3c/d flags (when set) |
|---|---|---|---|---|---|---|---|---|---|---|
| E22_1262-DevKitC, E22-DevKitC, E22_1268_S3, E22_1262_S3, heltec V2/V3/V4, wireless_stick, wireless_tracker, vision-master-e290/e213, T-Beam-1W, T3_S3_V1_3, ttgo-lora32-v21, ttgo_tbeam (+SX1262/SX1268/supreme), esp32-loraprs-e22/ra01 | Y (9/9) | Y | Y/Y | Y | Y | – | – | – | ≡ | Y |
| E22_XML-DevKitC | Y (9/9) | Y | Y/Y | Y | Y | **Y** | – | – | – (guarded out: `-D DISABLE_NET_CONSOLE`, variants/E22_XML-DevKitC/platformio.ini:34) | Y |
| wireless-paper | Y (9/9) | Y | Y/Y | Y | – (no ENABLE_GPS) | – | – | – | ≡ | Y |
| T-ETH-ELITE_1262, LilyGo_T_Connect_Pro | Y (9/9) | Y | Y/Y | Y | Y | – | – | – | **Y** | Y |
| t_deck, t_deck_plus | Y (9/9) | Y | Y/Y | Y | Y | – | **Y** | – | ≡ | Y |
| t_deck_pro | Y (9/9) | Y | Y/Y | Y | Y | – | – | **Y** | ≡ | Y |
| heltec_t114, t_echo, wiscore_rak4631 (nRF52) | ≡ (macro) | Y | Y/Y | – | – | – | – | – | – (`#if defined(ESP32)`) | – (esp32/* excluded) |
| esp32-safeboot, esp32-S3-safeboot | – | – | – | compiled in the object, linked out (no caller); image identical in code and data, differs only in the embedded ELF SHA-256 + digest (item 7) | – | – | – | – | – (not compiled) | – (esp32_main.cpp not compiled) |
| t5_epaper (commented out upstream) | not buildable on base (`variants/t5_epaper` has no `configuration.h`); no evidence possible; pre-existing (item 8) | | | | | | | | | |

- **Agent 1's prediction** (`../hunk-env-map.md`, from the pio config + `#if` guards) matches on every cell;
  agent 1 reviewed this table.
- **One refinement:** "PR3a compiled, guard active" on the non-Ethernet ESP32 boards is ≡ in the binary. The
  restructured `WiFi.status()` test compiles to identical code without `HAS_ETHERNET`. This turns a claim of the
  posted commit into evidence: a12fbcc6's message says "Boards without HAS_ETHERNET compile to the same code as
  before" (https://github.com/makrohard/MeshCom-Firmware/commit/a12fbcc6), and the object diff proves it on all
  24 non-Ethernet ESP32 app envs where the hunk compiles (27 ESP32 app envs − 2 Ethernet boards − E22_XML, which
  sets `DISABLE_NET_CONSOLE`; the nRF52 envs set it too).
- **Default behaviour unchanged by PR3c/d:**
  - The merge WITHOUT any flag has **no code change in `esp32_main.cpp.o` on any of the 27 ESP32 app envs**.
  - The 3 missing app envs are the nRF52 ones, where `esp32/*` is excluded from the build, so no `esp32_main.cpp.o`
    exists there.
  - The flags only act when set (item 6).
- **Comment-only and declaration hunks** (`src/udp_functions.cpp:611`, `src/nrf52/nrf_eth.cpp:766`,
  `src/esp32/esp32_flash.h`, `src/nrf52/WisBlock-API.h`) are object-identical where compiled:
  - no function of `udp_functions.cpp.o` or `nrf_eth.cpp.o` changes in any tree on any env (`funcs-all.txt`);
  - the declarations only add the prototypes of the NEW functions, and the macro is shown by the nRF52 "≡" column.
- **Each PR alone gives exactly its own subset of these cells, and nothing else.** Checked per env
  programmatically from the per-tree diffs (0 exceptions on 30 envs):
  - merge = pr1 ∪ pr2 ∪ pr3;
  - pr12 = pr1 ∪ pr2;
  - pr1 = the PR1 columns plus `commandAction`, pr2 = `commandAction` (+ the t114 template instance), pr3 = the
    PR3a column.

## Item 6 — Flag variants `-D DISABLE_BATTERY` / `-D DISABLE_BLE`

**Builds** (plain `pio run` of the 30 app envs in the same image, offline, `ci/run-pio.sh`,
`PLATFORMIO_BUILD_FLAGS=…`):

| tree + flags | log | result |
|---|---|---|
| merge + `-D DISABLE_BATTERY` | `pio-merge-fbatt-app30.log` | 30/30 SUCCESS |
| merge + `-D DISABLE_BLE` | `pio-merge-fble-app30.log` | 30/30 SUCCESS |
| merge + both | `pio-merge-fboth-app30.log` | 30/30 SUCCESS |
| pr3 + `-D DISABLE_BATTERY` | `pio-pr3-fbatt-app30.log` | 30/30 SUCCESS |
| pr3 + `-D DISABLE_BLE` | `pio-pr3-fble-app30.log` | 30/30 SUCCESS |
| **base + both (control)** | `pio-base-fboth-app30.log` | 30/30 SUCCESS |

- The safeboots are excluded: their `build_src_filter` is `+<safeboot/*>` + `esp32_flash.{h,cpp}` only, so the flags
  cannot reach them (platformio.ini:287-288, 330-331).
- **The flags occur only in `src/esp32/esp32_main.cpp`** (`grep` on the merge tree). nRF52 excludes `esp32/*`
  (platformio.ini:108ff), so there the flags are no-ops and the nRF52 builds are green.
- **Object proof** (`flagdiff.txt`, `ci/flagdiff.py`): `esp32_main.cpp.o` rebuilt deterministically with the flags
  (`ci/flag-obj.sh`), diffed against the unflagged, deterministic object:

  | variant | changed functions |
  |---|---|
  | `DISABLE_BATTERY` (merge and pr3) | exactly `esp32setup()` + `esp32loop()` on 27/27 ESP32 app envs, i.e. the two guarded hunks |
  | `DISABLE_BLE` (merge and pr3) | `esp32setup()` + `esp32_write_ble()` on 27/27, plus one compiler-generated `std::string` constructor instance that is emitted differently (library template code, not ours) |
  | both | `esp32setup` + `esp32_write_ble` + `esp32loop` on 27/27 |
  | **base + both (negative control)** | `esp32_main.cpp.o`: no code change on 27/27 |

  With `DISABLE_BLE`, `esp32loop` also differs on t_deck/t_deck_plus (one padding `nop`) and on ttgo_tbeam_supreme
  (a relaxed branch, `bnez`+`j` → `beqz`). Both are layout, described in `NOTES.md` (normalised diff: one `nop`; `bnez`+`j` vs `beqz`).
- **All-object negative control (v2, audit F3):**
  - Stock with both flags vs stock without them, compared over **every object of the build**: the Arduino framework
    core, every library under `.pio/libdeps` and `src/`, about 580 objects per ESP32 env.
  - Deterministic: build-date objects were rebuilt with `SOURCE_DATE_EPOCH` and the flags (`scripts/ci/det-obj-flags.sh`).
  - Diff: `ALLOBJ=1 BASE=base TREES="base base-fboth" analyse.py funcs`.
  - Result: **0 code sections differ on all 30 app envs** (`evidence/analysis/funcs-allobj-base-fboth.txt`).
  - So `PLATFORMIO_BUILD_FLAGS=-D DISABLE_BATTERY -D DISABLE_BLE` reaches no code outside `esp32_main.cpp`, neither
    in the framework nor in any library. The merge uses the same framework and library sources, so its flag builds
    can differ from the unflagged merge only in `esp32_main.cpp`, which is exactly what the table above shows.
  - The object BYTES do differ between flagged and unflagged builds, even where the code is identical: the per-env
    digests in `evidence/objects/` differ. I did not establish the cause; one plausible source is the debug info.
    That is why the comparison is by code sections, not bytes.
- **Strings:** `"[BLE ]...disabled (DISABLE_BLE)"` is present in 27/27 `esp32_main` objects of the fble/fboth builds
  and in 0/27 of merge/fbatt.
- **Which boards the flags are meant for** (PR3 text): ESP32 boards without a battery divider / without a usable BLE
  controller. They are opt-out; no variant sets them. Upstream's default builds are unchanged by PR3c/d (item 5:
  PR3 without flags is code-identical to base outside `loopNetConsole`).

## Item 7 — The two safeboot envs

- PR1's `esp32_flash.cpp` is compiled there. In the LTO object
  `.pio/build/esp32-safeboot/src/esp32/esp32_flash.cpp.o`, `nm -C` shows `T save_msgid()` and `T save_position()`
  on pr1 / pr12 / merge, and only `T save_settings()` on base.
- **None of the three reaches the linked ELF on any tree**, because safeboot calls none of them.
- **The images are identical in code and data, but not byte-identical:**
  - `safeboot.bin` / `safeboot-s3.bin` are byte-identical across base = pr2 = pr3, which shows the builds are
    reproducible.
  - pr1 / pr12 / merge differ from base only at bytes 176–207 (the ELF SHA-256 that esptool embeds at 0xB0) and in
    the last 33 bytes (the image checksum and digest).
  - The ELFs differ only in `.debug_info`, `.debug_str` and `.symtab`, which carry the debug records of the two
    unreferenced functions.
- Commands: `cmp -l`, `readelf -S -W`, `nm -C`. Recorded in `NOTES.md`.

## Item 8 — `t5_epaper` (the 33rd, commented out upstream): pre-existing failure, not testable

- `pio run -e t5_epaper` fails identically on **base** (`pio-base-t5_epaper.log`), merge, pr1 and pr2:
  `src/adc_functions.cpp:1:10: fatal error: configuration.h: No such file or directory`.
- `variants/t5_epaper/` on cf215b5d contains only `lv_conf.h` and `platformio.ini`
  (https://github.com/icssw-org/MeshCom-Firmware/tree/cf215b5d669a94e1c66c86bae21c76f4dff04061/variants/t5_epaper).
- Upstream's own env is broken, so no compile evidence for our hunks is possible there without editing the tree,
  which is not allowed.

## Item 9 — QEMU function proof: every reachable change row, each PR alone + merge, stock negative control

**Which run counts:** the counting run on the idle PC, 2026-09-26 23:18 – 2026-09-27 00:35 UTC (01:18–02:35 CEST),
with no build containers running and a 1-min load average of 2.6–7.6 (logged per step). The earlier runs made under
full build load (23:05–23:25 local) are discarded.

**QEMU and images:**
- QEMU binary `/home/makro/claude/qemu-cache-pr/b-up/qemu-system-xtensa`: sha256 `18afb66166c9830a…`, version
  9.2.2 (v9.2.2-126-gfebae182e1), stock Espressif, read-only.
- Images: meshcom-qemu-raspi `113ff40b` overlay + the tree, env `qemu-headless-extradio-gpsd`
  (`qemu/build-image-ci2.sh`, `qemu/build-one.sh`). The sha256 of every image is in `qemu/idle/manifest.txt`.
- Network: user-net `host=10.0.2.5` + `guestfwd` 10.0.2.2:7000 → a local sink, so no image could reach host port 7000.
- **These are the first QEMU proofs on the exact posted PR commits.** The earlier r6–r9 proofs used the pre-rebase
  heads.

**Harness note (not a PR property):** on trees that contain PR3, the overlay's own net-console, battery and BLE
workaround hunks no longer apply, because PR3 replaces exactly those three. So every pr3/merge image drops all three
workarounds and runs PR3's features instead (Ethernet mode via `testhack-eth.py`, `-D DISABLE_BATTERY -D DISABLE_BLE`).
PR1/PR2 rows on the merge therefore run in that configuration; the discriminating A/B for PR1/PR2 is base vs PR-alone
(same harness).

| row | stock `cf215b5d` (negative control) | PR alone | merge | verdict | logs (`qemu/…`) |
|---|---|---|---|---|---|
| **PR1 p1** (`proof.py p1`): GPS fix saved before any TX; `--aprsmc` survives a hard power-off right after the command; boot 2 starts from the saved fix; counter persisted and continues | 6/7: **FAIL** `--aprsmc survives a hard power-off` (the expected stock gap) | pr1: **7/7 PASS** | 7/7 PASS on 2 of 3 runs (see note ①) | PASS | `idle/proof-p1-{base,pr1,merge}-plain.log`, `idle/proof-p1-merge-plain-r{2,3}.log` |
| **PR1 loop gap** after 3 texts (`qemu-p1.py`, instr images) | 2733 / 3182 / 3239 ms | pr1: **0 / 0 / 0 ms** | 0 / 0 / 0 ms | PASS | `idle/qemu-p1-{base,pr1,merge}-instr.log` |
| **PR1 9 TX sites** (`sites/qemu-sites.py`, details below) | each site FLUSHES the RAM-only latitude to NVS; gap 2.8–3.7 s | pr1: never flushed; gap 0 ms; msgid persisted correctly | same as pr1 | 7 PASS, 1 unreached, 1 dead code | `sites/idle-{base,pr1,merge}-{instr,xml}/`, `sites/idle-run.out` |
| **PR1 F1 `{SET}` hop limit** (`qemu-sethop.py`, `--injectmsg`, instr) | out-of-range `{SET}44` and unchanged `{SET}4` leave 4; `{SET}2` → RAM 2, NVS 2, after reboot 2 (NVS `max_hop_text=2` through a full-save TX in the window, see ②) | pr1: RAM 2, NVS 2, after reboot 2; after TX + power-off 2 | same | PASS | `idle/qemu-sethop-{base,pr1,merge}-instr.log`, `qemu-sethop-idle-*/uart-A2.log` (`...MAXHOP text 2 / pos 2` after reboot) |
| **PR1 XML UTC offset** (`qemu-xml2.py`, TEST-ONLY `--xmltz` hook in the xml images; never in a PR) | `--xmltz +03:30` → NVS `utcof=1.0`, after reboot **UTC-OFF 1.0** (lost) | pr1: NVS `3.5`, after reboot **3.5** | NVS `3.5`, after reboot 3.5 | PASS (window CLEAN on all three: msgid 2 → 2) | `idle/qemu-xml2-{base,pr1,merge}-xml.log` |
| **PR2 setcall** (`proof.py setcall`, short images) | 6/7: **FAIL** "same callsign again (no-op): no reboot" | pr2: **7/7 PASS** | 7/7 PASS | PASS | `idle/proof-setcall-{base,pr2,merge}-short.log` |
| **PR3a net console on a non-WiFi IP network** (`qemu-netconsole.py`, Ethernet mode) | base-eth: network up, **console never answers** (180 s) | pr3-all: answers after 4 s, 0 panics | merge: answers after 4 s | PASS | `idle/qemu-netconsole-{base-eth,pr3-all,merge-plain}.log` |
| **PR3d `DISABLE_BLE`** (`qemu-measure.py`; QEMU has no BT controller) | base-noble: `assert failed: esp_bt_controller_init`; **base-noble-flag: the same assert** (stock ignores the flag) | pr3 with the flag: `[BLE ]...disabled (DISABLE_BLE)`, no BLE init, no assert; without it (drop3, drop3-batt): the assert | same as pr3 | PASS | `idle/qemu-measure-*.log`, `qemu-m-idle-*/` |
| **PR3c `DISABLE_BATTERY`** | base-nobatt and **base-nobatt-flag**: boot hangs in the unguarded battery path (no network, no console, no panic); the flag is ignored | pr3 with only `DISABLE_BLE` (drop3-ble): the same hang; with both flags (all): boots, `BATT 0.00 V … 0 %`, console after 20 s | same as pr3 | PASS | same |

① **merge p1, first run:** 6/7. "boot 2 (no GPS) starts from the saved fix" failed on the `--pos` console reply
(5 s window). The same run's NVS after boot 2 holds `node_lat=48.0`, and its UART prints `...LAT: 48.0000 N`, so the
fix was there; the console reply missed the window. Two immediate re-runs on the idle PC:
`RESULT p1: PASS (0 failed)` both (`idle/proof-p1-merge-plain-r2.log`, `-r3.log`). This is a harness timing miss,
not a firmware difference; pr1 alone passed 7/7 on the first run.

② **F1's discriminating control is the old PR1 (`c4f508b3`), not stock.** v2 (audit F4): this control is now part
of this evidence set, run on the idle PC with the same harness.
- Stock also keeps `max_hop_text=2` in this run, through a full-save TX inside the 5 s window: stock's Phase A NVS
  has `node_msgid=2`.
- With PR1 a transmission writes only `node_msgid`, so PR1's persisted `2` can only come from the `{SET}` handler's
  own `save_settings()`, which is the F1 fix.
- **Old PR1** (image sha256 `c909c3a6b77c7245…`, built from `c4f508b3`; patches, build log and hash in
  `evidence/controls/`): `{SET}2` → RAM 2, **NVS 4** after a hard power-off, **`...MAXHOP text 4` after the reboot**,
  and **NVS 4 after a TX + power-off**. The value is LOST, which is the regression.
  - Log: `qemu/idle/qemu-sethop-oldpr1-c4f508b3-instr.log`; UART: `qemu-sethop-idle-oldpr1-c4f508b3-instr/uart-A2.log`.
  - A first attempt accidentally used the fixed-PR1 image (built from `b1de77e4`); it is kept, marked INVALID.
- The after-reboot value was read from the boot banner (`...MAXHOP text 2 / pos 2`, `uart-A2.log`), because the
  harness's 1 s `--maxhop` window after the console came up printed `?` on all three images.

**PR1 per-site detail** (`sites/qemu-sites.py`, run one QEMU at a time):
- Before each site fires, the virtual GPS moves the node to a new latitude, which changes a saved field in RAM only.
  Stock's full `save_settings()` at the TX writes that latitude to NVS (**FLUSHED**); `save_msgid()` does not.
- The harness plays the external-radio bridge, so it captures every TX frame and injects RX frames. A window counts
  only if the site's own frame is the only new TX in it.
- Persistence: NVS `node_msgid` = the frame's counter + 1.

| site (merge line) | trigger | stock | PR1 | merge |
|---|---|---|---|---|
| sendPing :3344 | `--pingcall`/`--pingtime 30`/`--ping start`, 2nd ping | msgid OK, **FLUSHED**, 3151 ms | msgid OK, not flushed, 0 ms | msgid OK, not flushed, 0 ms |
| SendPong :3446 | injected RX `DL1PEE-1>TE5T-1 {ping}` | OK, **FLUSHED**, 2942 ms | OK, not flushed, 0 ms | OK, not flushed, 0 ms |
| sendMessage :4099 | `::sites text N` | OK, **FLUSHED**, 3421 ms | OK, not flushed, 0 ms | OK, not flushed, 0 ms |
| sendPosition :4859 | `--sendpos` | OK, **FLUSHED**, 2789 ms | OK, not flushed, 0 ms | OK, not flushed, 0 ms |
| SendAckMessage :5016 | injected RX DM `sites dm{485` (LoRa RX path) | OK, **FLUSHED**, 3049 ms | OK, not flushed, 0 ms | OK, not flushed, 0 ms |
| sendHey :5108 | `--sendhey` | OK, **FLUSHED**, 3670 ms | OK, not flushed, 0 ms | OK, not flushed, 0 ms |
| sendTelemetry :5447 | reached only through TEST-ONLY scaffolding (`--xmltz` sets `node_parm_1`, xml images; never in a PR) + `--ptime 5`, 2nd telemetry | OK, **FLUSHED** (no gap data: not an instr image) | OK, not flushed | OK, not flushed |
| sendInjectedPosition :4284 | — | **unreached**: the only caller is KISS/TCP (`kiss_functions.cpp:476`), whose listener opens only with WiFi connected (`kissLoop()`, `esp32_main.cpp:4009`); QEMU has only Ethernet. The same one-line `save_settings`→`save_msgid` change as the 7 proven sites: code + compile proof only (item 5). | | |
| sendAPPPosition :4946 | — | **dead code**: no caller anywhere in the tree. The same one-line change; code + compile proof only (item 5). | | |

- Every run ends with a SIGKILL and a final NVS read. For pr1/merge instr+xml, and for stock xml, NVS `node_msgid`
  = the counter after the last own new TX.
- On stock instr, the harness's final check picked a ring retransmission of the older frame id 1 as "last own TX".
  The last new frame was the HEY with ctr 7, which matches NVS `node_msgid=8`. This is harness bookkeeping, stock
  only.
- SendAckMessage's KISS and gateway-UDP callers were not exercised; the function was proven through the LoRa RX path.

**Not reachable in QEMU:** the T-Deck / T-Deck Pro UI saves (PR1 F3, SYM+K, taps, ALT keys) and all nRF52 runtime.
The hardware evidence for them is in `../AUDIT-REPORT.md` section 1, "Live, real hardware" (T-Deck and T-Deck Pro
rows, final code).

## What was NOT checked, and the limits

- **No hardware in this run.** Hardware rows are the earlier live proofs in `../AUDIT-REPORT.md` (section 1,
  "Live, real hardware": Heltec V3, T-Beam, T-Deck, T-Deck Pro), which ran on the final code.
- **Not reachable in QEMU:**
  - T-Deck / T-Deck Pro UI hunks and nRF52 runtime: compile + object proof only here; hardware evidence as above.
  - PR3a on a real Ethernet board (no T-ETH Elite / T-Connect Pro available).
- **The container is not GitHub's runner.** It matches the workflow's steps and versions (Python 3.11, latest
  PlatformIO = 6.2.0 today, both platforms), but not the runner image itself.
- The release-action upload step was not run (an artifact-existence check instead).
- **Nothing was compiled with `-Wall -Wextra` beyond upstream's own flags.**

## Incidents during this run (all environmental; none affects a verdict)

- **PlatformIO registry refusal:** my fresh CI containers re-downloaded platforms and libs on every run, and the
  registry answered "Download limit exceeded. Try again in 24 hours" (22:01 UTC). All six CI jobs had completed
  before that. From then on, every build ran with `--network none` from a cached pio home plus copied
  `.pio/libdeps`, with 0 "Installing/Downloading" lines (checked in each log).
- **Invalid logs are kept, renamed `INVALID-*`:**
  - one flag run got mangled flags (a placeholder bug of mine: `-D DISABLE BATTERY`);
  - runs stopped at the rate limit;
  - a deterministic rebuild without the flags cleaned the flag trees' build dirs, so the flag object proof was
    redone per object (`flagobj-*.log`).
- **Host port 7000:** the QEMU images dial `10.0.2.2:7000` = the host, where another session's bridge process was
  listening. The counting QEMU runs use `host=10.0.2.5` + `guestfwd` to a local sink (`qemu/*.py`), and the site
  harness uses its own bridge, so no run reached that port.
- **QEMU runs made under full build load (23:05–23:25 local) are discarded.** Only the idle-PC runs count (item 9).
