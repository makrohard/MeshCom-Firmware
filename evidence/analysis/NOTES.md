# Agent 5 working notes (facts for the report; the source of each is named)

## Trees (step 0, 2026-09-26)
- The PR heads are based on f7f1fe9c, not cf215b5d. cf215b5d = f7f1fe9c + docs/wiederholungen.md (docs only).
  "PR alone" = a local merge commit cf215b5d + PR, which is what GitHub produces. Scratch commits (author a5,
  fixed date) live in the agent5-allenvs/base clone as branches a5-*; they are never pushed.
  - pr1  e6e8c95d tree 4f1c0e80 (10 files +79 -11)
  - pr2  97fa8df1 tree 8f693de4 (3 files +12 -4)
  - pr3  eacd07b3 tree f8294acd (2 files +34 -4)
  - pr12 d3087d9e tree e4288d45 (PR1+PR2 = PR2+PR1, same tree)
  - merge a7957f7a tree 58d99cd9 (the handler's clones)
- All 6 merge orders of PR1/PR2/PR3 on cf215b5d merge without conflict to the same tree 58d99cd9.
- Pairs: only PR1 and PR2 share a source file (src/command_functions.cpp). PR1+PR3 and PR2+PR3 share no
  source file, so no build of those pairs is needed (handler 2026-09-26).
- gh pr view (read-only, 2026-09-26): #1164/#1165/#1166 OPEN, mergeable=MERGEABLE, mergeStateStatus=BLOCKED
  (awaiting review), heads 3f936a63/84e6e308/9d8cbdbb.

## From agent 1 (claude-1e), 2026-09-26
- QEMU: /home/makro/claude/qemu-cache-pr/b-up/qemu-system-xtensa (claude-aa's stock Espressif build), read-only.
  CI carry builds its own patched QEMU, so the local and CI QEMU differ; name the binary per row.
- Overlay: meshcom-qemu-raspi 113ff40b (archived from ~/claude/mqr-docs-wording); it applied on f7f1fe9c+PR1+PR2
  (carry run 36263464324 green on ba289816).
- The r6-r9 QEMU images were built from PRE-rebase heads (eea80ff5 ...; range-diff "="). Runs on the posted heads
  3f936a63/84e6e308/9d8cbdbb are the FIRST QEMU proofs on the exact posted commits.
- PR3 on QEMU: the overlay's own net_console hunk + batt/BLE workarounds mask PR3, so use the eth / nobatt[-flag] /
  noble[-flag] / all variants.
- proof.py (+nvsdump.py, testhack-short.py): ~/claude/meshcom-carry-ci/.github/lhpc-speed/. The qemu-*.py tools are in
  ~/claude/meshcom-prs-evidence/.
  - EV is hard-coded there, so change it in my copies.
  - Fixed ports: proof 22323, netconsole 22324, setcall 22325, p1 22327, xml 22328, sethop 22331.
    Different scripts can run in parallel; two copies of the same script cannot.
  - p1/proof need gps-relay.py + valid_fix.nmea (~/claude/meshcom-qemu-raspi).
  - sethop and p1 loop-gap need instr images (--injectmsg only under INSTRUMENT_ENABLED). setcall needs short
    images. xml needs xml images (applies 7ba919cb, TEST ONLY).
  - Loop-gap numbers need an IDLE PC. setcall waits 40 s (rebootAuto 15 s after save); the "no reboot" marker is the
    overlay's "[QEMU]...auto-reboot suppressed".
  - Power-off = kill QEMU by PID, then nvsdump of the flash file.
- QEMU-reachable beyond the evidence table:
  - The nine save_msgid sites (sendPing, SendPong, sendMessage, sendInjectedPosition, sendPosition,
    sendAPPPosition, SendAckMessage, sendHey, sendTelemetry). Only sendMessage and sendPosition are proven so far.
    sendAPPPosition = phone/BLE path, probably not reachable.
  - save_position 15-min rate limit.
  - --aprsmc save (done in p1).
- Not QEMU-reachable:
  - T-Deck/T-Deck Pro UI: hardware evidence in AUDIT-REPORT.
  - nRF52 (save_msgid = save_settings): compile + objdump only.
  - The BENCH_BLE_ADV_LATE line: compile only.
  - The comment-only hunks (udp_functions.cpp:611, nrf_eth.cpp:766) and the declarations need compile proof only.
- Agent 1 is building a per-env "hunk compiled in" map and will send it.

## Build-run facts (2026-09-26 evening)
- The upstream build rewrites the TRACKED files safeboot.bin / safeboot-s3.bin (post:tools/safeboot.py) in every tree,
  base included. This is pre-existing upstream behaviour. My clean-tree guard ignores exactly these two files.
- commandAction() embeds __DATE__/__TIME__ digits (command_functions.cpp:136-141), so its object differs between any
  two builds. Build-date users: command_functions, esp32/esp32_main, t-deck/tdeck_main, web_functions, rtc_functions,
  nrf52/nrf52_functions. They are rebuilt with SOURCE_DATE_EPOCH=1790000000 (ci/det-obj.sh) before the object diff.
- The object diff (ci/analyse.py funcs) classifies LAYOUT-ONLY (branch offsets, alignment padding, narrow/wide Xtensa
  encodings) separately from CHANGED.
- sendAPPPosition() has NO caller in the tree (dead code): its PR1 site is compile-proof only.
- QEMU rows run 23:05-23:25 were under full load (handler 23:24: at most 2 QEMU while builds run). All those results
  are provisional and re-run on an idle PC.
- A scheduler race started 7 containers for about a minute; all were capped to 3 CPUs, and sched2 waits 30 s per start.
- The pr2 t5_epaper job was skipped by the guard (the safeboot files); it is redone at the end.
- t5_epaper (commented out in default_envs upstream) does NOT build on plain cf215b5d: "src/adc_functions.cpp:1:10: fatal
  error: configuration.h: No such file or directory" (also aht20.cpp). variants/t5_epaper/ has only lv_conf.h and no
  configuration.h. The failure is identical on merge, pr1 and pr2 (pio-*-t5_epaper.log) and pre-existing. No compile
  evidence is possible for t5_epaper without editing the tree (not allowed).
- The first flag run (merge-fboth) passed mangled flags ('-D DISABLE BATTERY ...', my queue placeholder bug) and is
  INVALID (renamed INVALID-flag-mangled-*.log). It was re-run with the correct flags.
- Safeboot envs: the ELFs contain none of save_settings/save_msgid/save_position on any tree (no caller, linked out).
  The LTO object src/esp32/esp32_flash.cpp.o defines save_msgid()+save_position() on pr1/pr12/merge only.
  safeboot.bin / safeboot-s3.bin: base = pr2 = pr3 byte-identical (reproducible). Trees with PR1 differ ONLY at bytes
  176-207 (the ELF SHA-256 embedded at 0xB0) and in the last 33 bytes (the image checksum + digest). The ELF diff is
  .debug_info/.debug_str/.symtab only, so code and data are identical. NOT "byte-identical".
- PR1 object diff (deterministic objects, 30 app envs; funcs-pr1.txt) matches hunk-env-map.md:
  - ESP32: the 9 sites + sendDisplayText + commandAction + NEW save_msgid/save_position; WZ_GPS_Loop only with ENABLE_GPS
    (not wireless-paper); decodeTinyXML only on E22_XML; T-Deck UI (tab_kbl/tab_standby/keypad_read) only on
    t_deck/t_deck_plus; keypad_loop only on t_deck_pro.
  - nRF52 (rak/t_echo/t114): only commandAction (--aprsmc save) + sendDisplayText ({SET} save). The 9 sites are
    unchanged, as the macro predicts.
  - The rest is LAYOUT-ONLY (branch offsets, narrow/wide encodings, CSWTCH.N numbering).
- PR2 size on nRF52 (nm -S of the ELFs, base vs pr2): commandAction +4 (rak) / +100 (t_echo) / +124 (t114). On t114
  also +368 B in an ArduinoJson template instance (a weak symbol, StringNode...), a code-generation side effect in
  library code; net +426. RAK net +4.
- MISTAKE (mine): det-obj.sh on merge-fbatt/fble/fboth ran WITHOUT PLATFORMIO_BUILD_FLAGS, so pio saw a
  config-checksum change and cleaned each env's build dir. The flag lanes' compile verdict stands (logs
  pio-merge-f*-app30.log, 30/30 SUCCESS each). For the object proof, only esp32/esp32_main.cpp.o (the only file that
  uses the flags) is rebuilt per ESP32 env with the flags + SOURCE_DATE_EPOCH (ci/flag-obj.sh) and diffed against
  merge's deterministic esp32_main.cpp.o.
- Flag object proof (esp32_main.cpp.o, deterministic, 27 ESP32 app envs, ci/flagdiff.py; the whitespace normaliser
  fix applied):
  - merge+DISABLE_BATTERY vs merge: exactly esp32setup + esp32loop on 27/27.
  - merge+DISABLE_BLE: esp32setup + esp32_write_ble on 27/27, plus a std::string helper instance. esp32loop
    differs on t_deck/t_deck_plus (a padding nop) and ttgo_tbeam_supreme (a relaxed branch, bnez+j -> beqz): layout.
  - merge+both: esp32setup + esp32_write_ble + esp32loop on 27/27.
  - String "disabled (DISABLE_BLE)": 27/27 in fble/fboth, 0/27 in merge/fbatt.
  - nRF52: the flags appear only in esp32/esp32_main.cpp, which nRF52 excludes (-<esp32/*>), so they have no
    effect; the lanes are green.
