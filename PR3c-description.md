## feat(batt): DISABLE_BATTERY for ESP32 boards without battery measurement

A board without a battery divider has nothing to read on the ADC. With `DISABLE_BATTERY` in the
board's build flags, `esp32setup()` sets `battProbeState = BATT_PROBE_NONE` instead of calling
`init_batt()`, and the loop reports the existing "not measurable" state (`global_batt = 0`,
`global_proz = 0`, `BATT_PROBE_NONE`), exactly as the `MODUL_FW_TBEAM` branch does without a PMU, so
no "/B=000" (battery empty) is sent. The flag is checked first, so it also wins on boards that define
`MODUL_FW_TBEAM` (the PMU itself is still set up; only the battery reading is off).
No board sets the flag: all existing builds are unchanged (T-Deck `esp32_main.cpp.o` disassembly
identical to upstream; RAK4631 unaffected).

Tested: T-Beam with the flag builds and no longer contains the PMU battery path or `init_batt`.
T-Deck with the flag: node runs, `--info` shows `BATT 0.00 V … 0 %`, battery init skipped.
ESP32 under QEMU (no ADC): without the flag the loop hangs after setup; with it the node runs.

Builds and QEMU runs use this PR's exact commit on icssw-org dev `6cc8b552`; QEMU uses stock Espressif
QEMU with the meshcom-qemu-raspi emulator overlay. The hardware tests ran on the same patch one upstream
revision earlier (`2a5dcdcd`); the rebase did not change the patch.
