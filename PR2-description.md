## fix(call): --setcall with the current callsign saves nothing and does not reboot

### What changes

`--setcall <call>` (`src/command_functions.cpp`, `commandAction`) always stored the callsign,
called `save_settings()` and, on most boards, scheduled the auto-reboot 15 s later
(`rebootAuto`; T-Deck and T-Deck Plus are excluded).

With this PR the handler skips the flash write and the auto-reboot only if neither the
normalised callsign nor the resulting shortname changes. The usual confirmation
`Call:<call> Short:<short> set` is still printed. The shortname is compared too, because the
server configuration can set a custom shortname; `--setcall` with the same callsign replaces
it with the derived one, and that change is saved and rebooted exactly as before.

The server configuration paths (`src/udp_functions.cpp`, `src/nrf52/nrf_eth.cpp`) keep their own save
and reboot; their comments now say they reboot like a changed `--setcall`.

### Why

Tools, scripts and apps that send the callsign again (for example on every connect) rebooted the
node each time, although nothing changed. The web setup page is not affected: it sends
`--setcall` and then compares the stored callsign with the wanted one, which still matches.

### Tested

- Builds: `wiscore_rak4631`, `ttgo_tbeam`, `ttgo_tbeam_SX1262`, `ttgo_tbeam_SX1268`,
  `ttgo_tbeam_supreme`, `LilyGo_T-Beam-1W`, `t_deck`, `t_deck_pro`, `heltec_wifi_lora_32_V3`,
  `T-ETH-ELITE_1262`, `LilyGo_T_Connect_Pro` all build. RAK4631: +16 bytes text (three clean builds).
- T-Deck (real hardware): `--setcall` with the stored callsign prints the confirmation and the
  callsign in NVS is unchanged. (T-Deck never auto-reboots on `--setcall`.)
- Heltec LoRa32 V3 and T-Beam (real hardware; both auto-reboot on `--setcall`): a new callsign is
  saved and the node reboots; the same callsign again prints the confirmation and does not reboot.
- QEMU (ESP32): same callsign with a custom shortname in flash → saved and rebooted; same
  callsign again → no save, no reboot.

Builds, QEMU runs and the Heltec/T-Beam tests use this PR's code on icssw-org dev `6cc8b552`; QEMU uses
stock Espressif QEMU with the meshcom-qemu-raspi emulator overlay. The T-Deck test ran on the same patch
one upstream revision earlier (`2a5dcdcd`).
