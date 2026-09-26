## feat(ble): DISABLE_BLE for ESP32 boards without a usable BLE controller

With `DISABLE_BLE` in the board's build flags, `esp32setup()` skips the NimBLE initialisation and
advertising, and `esp32_write_ble()` does nothing (`pTxCharacteristic` is never created). Everything
else that touches BLE in the loop runs only while a phone is connected, which cannot happen without
the stack. The bench-only `BENCH_BLE_ADV_LATE` start is skipped too.
No board sets the flag: all existing builds are unchanged (T-Deck `esp32_main.cpp.o` disassembly
identical to upstream; RAK4631 unaffected).

Tested: T-Deck with the flag: node runs, boot log shows "disabled (DISABLE_BLE)", a BLE scan no longer
sees the node (without the flag it is seen). ESP32 under QEMU (no BT controller): without the flag
`esp_bt_controller_init` asserts and the node reboots in a loop; with it the node runs.

Builds and QEMU runs use this PR's exact commit on icssw-org dev `6cc8b552`; QEMU uses stock Espressif
QEMU with the meshcom-qemu-raspi emulator overlay. The hardware tests ran on the same patch one upstream
revision earlier (`2a5dcdcd`); the rebase did not change the patch.
