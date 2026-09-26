## ESP32: Ethernet net console, DISABLE_BATTERY and DISABLE_BLE

Three small, independent changes, one commit each. The first lets the net console start in Ethernet mode;
the other two add build flags for ESP32 boards that have no battery divider or no usable BLE controller.
No board sets the new flags, and boards without `HAS_ETHERNET` compile to the same code as before.
Each flag carries an `opt-out -D …` comment at its first `#if`, in the wording `DISABLE_KISS_TCP` uses in
`configuration_global.h`.

### 1. fix(netconsole): start the net console in Ethernet mode

`loopNetConsole()` (`src/net_console.cpp`) returns early while `WiFi.status() != WL_CONNECTED`,
so that `::socket()` is not called before the lwIP stack is up. In Ethernet mode
(`HAS_ETHERNET`, `node_netmode == 1`, e.g. T-ETH Elite and T-Connect Pro) WiFi never connects,
so the net console never opened its listening socket and port 2323 never answers. The web server
already handles Ethernet mode (`startWebserver()` skips its WiFi IP check when `node_netmode == 1`).

On boards with `HAS_ETHERNET`, the console now also starts when the node is in Ethernet mode
and has an IP address (`node_hasIPaddress`, set by `EspETH::initethDHCP()` /
`EspETH::initethfixIP()`). The WiFi condition is unchanged, so WiFi client and WiFi AP mode
behave exactly as before. `net_console.cpp` now includes `configuration.h`; without it
`HAS_ETHERNET` is not visible in this file.

### 2. feat(batt): DISABLE_BATTERY for ESP32 boards without battery measurement

A board without a battery divider has nothing to read on the ADC. With `DISABLE_BATTERY` in the
board's build flags, `esp32setup()` sets `battProbeState = BATT_PROBE_NONE` instead of calling
`init_batt()`, and the loop reports the existing "not measurable" state (`global_batt = 0`,
`global_proz = 0`, `BATT_PROBE_NONE`), exactly as the `MODUL_FW_TBEAM` branch does without a PMU, so
no "/B=000" (battery empty) is sent. The flag is checked first, so it also wins on boards that define
`MODUL_FW_TBEAM` (the PMU itself is still set up; only the battery reading is off).

### 3. feat(ble): DISABLE_BLE for ESP32 boards without a usable BLE controller

With `DISABLE_BLE` in the board's build flags, `esp32setup()` skips the NimBLE initialisation and
advertising, and `esp32_write_ble()` does nothing (`pTxCharacteristic` is never created). Everything
else that touches BLE in the loop runs only while a phone is connected, which cannot happen without
the stack. The bench-only `BENCH_BLE_ADV_LATE` start is skipped too.

### Tested

- Builds of this branch: `wiscore_rak4631`, `ttgo_tbeam`, `ttgo_tbeam_SX1262`, `ttgo_tbeam_SX1268`,
  `ttgo_tbeam_supreme`, `LilyGo_T-Beam-1W`, `t_deck`, `t_deck_pro`, `heltec_wifi_lora_32_V3`,
  `T-ETH-ELITE_1262`, `LilyGo_T_Connect_Pro`. RAK4631 is unchanged (the changes are ESP32-only; every
  symbol has the same size). The two `HAS_ETHERNET` boards grow by 12 bytes (commit 1); the other
  boards are unchanged apart from a few bytes of build jitter. Without the flags, the T-Deck objects of
  the changed files are identical to upstream (code, relocations and data).
- Commit 1, ESP32 under QEMU on a non-WiFi IP network, Ethernet mode simulated (test-only
  `HAS_ETHERNET` + `node_netmode = 1`): with the old gate the console did not answer within 180 s;
  with this change it answers after 4 s. No panic. Not tested on a real T-ETH Elite or T-Connect Pro.
- Commit 2: T-Beam built with the flag no longer contains the PMU battery path or `init_batt`.
  T-Deck with the flag: node runs, `--info` shows `BATT 0.00 V … 0 %`, battery init skipped.
  ESP32 under QEMU (no ADC): without the flag the loop hangs after setup; with it the node runs.
- Commit 3: T-Deck with the flag: node runs, boot log shows "disabled (DISABLE_BLE)", a BLE scan no
  longer sees the node (without the flag it is seen). ESP32 under QEMU (no BT controller): without the
  flag `esp_bt_controller_init` asserts and the node reboots in a loop; with it the node runs.
- All three together under QEMU (both flags, Ethernet mode simulated): one boot, network up, console
  answers, no panic.
- Heltec LoRa32 V3 and T-Beam (real hardware): without the flags the battery is read (divider on the
  Heltec, PMU on the T-Beam) and BLE advertises; with `DISABLE_BATTERY` `--info` shows `BATT 0.00 V`
  on both, also on the T-Beam's `MODUL_FW_TBEAM` path; with `DISABLE_BLE` the boot log shows
  "disabled (DISABLE_BLE)" and a BLE scan no longer sees the node.

Builds and QEMU runs use this branch on icssw-org dev `6cc8b552`; QEMU uses stock Espressif QEMU with
the meshcom-qemu-raspi emulator overlay. The Heltec and T-Beam tests use this branch's code; the
T-Deck tests ran on the same three patches one upstream revision earlier (`2a5dcdcd`).
