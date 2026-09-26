## Save settings where they change; on ESP32 save only the counter after a transmission

Two commits.

### 1. fix(flash): save settings where they change
Some settings were changed in RAM without being saved. They only reached flash because every
transmission rewrote all settings afterwards, so a change was lost if the node was switched off
before its next HEY or message:
- `--aprsmc` now calls `save_settings()` like every other setting command (`src/command_functions.cpp`).
- T-Deck: the standby (eye) and keyboard-backlight buttons in the header (`src/t-deck/lv_obj_functions.cpp`)
  and SYM+L / SYM+K (`src/t-deck/tdeck_main.cpp`) save the lock state; it is restored from flash at boot.
- T-Deck Pro: ALT+L, ALT+K, ALT+O, ALT+I and ALT+M save the changed backlight lock, keyboard lock, map
  and mute (`src/t-deck-pro/peri_keypad.cpp`).
- A UTC offset received via the soft-serial XML is saved when it changes (`src/tinyxml_functions.cpp`).
- ESP32: a new GPS fix is saved with the new `save_position()` (five keys, at most every 15 min,
  `src/gps_functions.cpp`). Without a fix the node sends the stored position, so a recent fix has to
  survive a reboot.

Unchanged by design: phone settings are committed by 0xF0 "Save Settings" or the 0x0A save flag, and
periodic phone positions are not saved (as documented in `src/phone_commands.cpp`); the T-Deck setup
page is committed by its Save button.

### 2. perf(flash): on ESP32, after a transmission save only the message counter
Every transmission (HEY, position, message, ping, pong, ACK, telemetry) increments `node_msgid` and
then called `save_settings()`, which goes through all ~130 keys. A transmission changes nothing else,
so on ESP32 `save_msgid()` now writes only `node_msgid` at the eight `// Flash rewrite` sites
(`src/loop_functions.cpp`). Runtime values (sensor readings, MCP23017 inputs, the smart-beaconing
symbol) are measured or chosen again after a reboot. On nRF52 the settings file is written only when
its content changed, so there `save_msgid()` is `save_settings()` and nRF52 behaves as before.

### Tested
- Builds: RAK4631, T-Beam (4 variants), T-Beam 1W, T-Deck, T-Deck Pro, Heltec V3, T-ETH Elite, T-Connect Pro.
  RAK4631: +16 bytes (three clean builds; the only code added there is the `--aprsmc` save, 4 bytes,
  the rest is alignment). ESP32: +156…+280 bytes text.
- T-Deck (real hardware): counter persists across a reset and keeps counting; `--aprsmc` survives a
  reset issued right after the command; tapping the eye / keyboard buttons stores the locks in flash
  immediately.
- ESP32 under QEMU with a GPS feed: no loop stall after a transmission (largest gap 0–0.4 s; upstream stalls the loop
  for 2–13 s after each transmission in the emulator); the GPS fix is in flash before any transmission; `--aprsmc` survives a hard power-off.

Builds and QEMU runs use this PR's exact commit on icssw-org dev `6cc8b552`; QEMU uses stock Espressif
QEMU with the meshcom-qemu-raspi emulator overlay. The hardware tests ran on the same patch one upstream
revision earlier (`2a5dcdcd`); the rebase did not change the patch.
