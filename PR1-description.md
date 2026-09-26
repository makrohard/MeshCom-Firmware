## Save settings where they change; on ESP32 save only the counter after a transmission

Two commits.

### 1. fix(flash): save settings where they change
Some settings were changed in RAM without being saved. They only reached flash because every
transmission rewrote all settings afterwards, so a change was lost if the node was switched off
before its next HEY or message:
- `--aprsmc` now calls `save_settings()` like every other setting command (`src/command_functions.cpp`).
- T-Deck: the standby (eye) and keyboard-backlight buttons in the header (`src/t-deck/lv_obj_functions.cpp`)
  and SYM+K (`src/t-deck/tdeck_main.cpp`) save the lock state; it is restored from flash at boot. SYM+L is
  left as it is: its lock is re-derived from the header state (`node_modus`) on every header refresh.
- T-Deck Pro: ALT+L, ALT+K, ALT+O, ALT+I and ALT+M save the changed backlight lock, keyboard lock, map
  and mute (`src/t-deck-pro/peri_keypad.cpp`).
- A UTC offset received via the soft-serial XML is saved when it changes (`src/tinyxml_functions.cpp`).
- A text hop limit received in a `{SET}` message is saved when it is accepted and differs from the
  current value (`sendDisplayText()`, `src/loop_functions.cpp`); `max_hop_pos` stays unsaved, as before.
- ESP32: a new GPS fix is saved with the new `save_position()` (five keys, at most every 15 min,
  `src/gps_functions.cpp`). Without a fix the node sends the stored position, so a recent fix has to
  survive a reboot.

Unchanged by design: phone settings are committed by 0xF0 "Save Settings" or the 0x0A save flag, and
periodic phone positions are not saved (as documented in `src/phone_commands.cpp`); the T-Deck setup
page is committed by its Save button.

### 2. perf(flash): on ESP32, after a transmission save only the message counter
Previously, every transmission (HEY, position, message, ping, pong, ACK, telemetry, and a position
injected by a KISS client) incremented `node_msgid` and then called `save_settings()`, which goes
through all ~130 keys. On ESP32 `save_msgid()` now writes only `node_msgid` in all nine paths:
the eight `// Flash rewrite` sites and `sendInjectedPosition()` (`src/loop_functions.cpp`).
Runtime values (sensor readings, MCP23017 inputs, the smart-beaconing
symbol) are measured or chosen again after a reboot. On nRF52 the settings file is written only when
its content changed, so there `save_msgid()` is `save_settings()` and nRF52 behaves as before.
`src/esp32/esp32_flash.h` now notes at the save functions that a transmission no longer persists other
settings: each setting is committed by its owning path, and some UI and phone paths stage changes until
an explicit Save.

### Tested
- Builds: RAK4631, T-Beam (4 variants), T-Beam 1W, T-Deck, T-Deck Pro, Heltec V3, T-ETH Elite,
  T-Connect Pro.
  RAK4631: +8…+16 bytes text in three clean builds. ESP32: +164…+340 bytes text
  (T-Deck: +340 bytes).
- T-Deck (real hardware): counter persists across a reset and keeps counting; `--aprsmc` survives a
  reset issued right after the command; tapping the eye / keyboard buttons stores the locks in flash
  immediately.
- Heltec LoRa32 V3 and T-Beam (real hardware): `--aprsmc` survives a reset issued right after the
  command; the counter is saved after each transmission and continues across resets.
- ESP32 under QEMU with a GPS feed: no loop stall after a transmission (largest gap 0–0.4 s; current
  upstream stalls the loop for about 2 s after each transmission in the emulator); the GPS fix is in
  flash before any transmission; `--aprsmc` survives a hard power-off.
- ESP32 under QEMU, `{SET}` delivered through the real handler: an accepted text hop limit survives a
  hard power-off, also when a transmission follows it (upstream keeps it only through a transmission's
  full save); out-of-range and unchanged values leave the setting alone.

Builds and QEMU runs use this PR's code on icssw-org dev `6cc8b552`; the final amendments since those
runs change only comments. QEMU uses stock Espressif QEMU with the meshcom-qemu-raspi emulator overlay.
The Heltec and T-Beam tests use this PR's code; the T-Deck tests ran on an earlier revision of this
patch (on `2a5dcdcd`), and the code they cover (counter save, `--aprsmc`, header buttons) is unchanged
since.

**Fuer die Release-Notes:** Einstellungen werden dort gespeichert, wo sie sich aendern (u. a. `--aprsmc`,
`{SET}`-Hoplimit, T-Deck- und T-Deck-Pro-Tasten, XML-UTC-Offset, GPS-Position); nach einer Aussendung
schreibt ESP32 nur noch den Nachrichtenzaehler statt aller Einstellungen.
