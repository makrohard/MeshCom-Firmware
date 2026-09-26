## fix(netconsole): start the net console in Ethernet mode

### What changes

`loopNetConsole()` (`src/net_console.cpp`) returns early while `WiFi.status() != WL_CONNECTED`,
so that `::socket()` is not called before the lwIP stack is up. In Ethernet mode
(`HAS_ETHERNET`, `node_netmode == 1`, e.g. T-ETH Elite and T-Connect Pro) WiFi never connects,
so the net console never opened its listening socket.

On boards with `HAS_ETHERNET`, the console now also starts when the node is in Ethernet mode
and has an IP address (`node_hasIPaddress`, set by `EspETH::initethDHCP()` /
`EspETH::initethfixIP()`). The WiFi condition is unchanged, so WiFi client and WiFi AP mode
behave exactly as before.

`net_console.cpp` now includes `configuration.h`; without it `HAS_ETHERNET` is not visible in
this file.

### Why

With a network cable the web UI works (it already checks Ethernet mode), but the net console
on port 2323 never answers.

### Tested

- Builds: `wiscore_rak4631`, `ttgo_tbeam`, `ttgo_tbeam_SX1262`, `ttgo_tbeam_SX1268`,
  `ttgo_tbeam_supreme`, `LilyGo_T-Beam-1W`, `t_deck`, `heltec_wifi_lora_32_V3`,
  `T-ETH-ELITE_1262`, `LilyGo_T_Connect_Pro`, `t_deck_pro`. Both `HAS_ETHERNET` boards (T-ETH Elite,
  T-Connect Pro) build the new branch. Boards without `HAS_ETHERNET` compile to the same net console code as
  before (T-Deck: disassembly of `net_console.cpp.o` identical); RAK4631 is unchanged (the file
  is ESP32-only). T-ETH Elite: +12 bytes.
- ESP32 under QEMU on a non-WiFi IP network, Ethernet mode simulated (test-only
  `HAS_ETHERNET` + `node_netmode = 1`): with the old gate the console did not answer within
  180 s; with this change it answered after 4 s. No panic. Not yet tested on a real T-ETH Elite.

Builds and QEMU runs use this PR's exact commit on icssw-org dev `6cc8b552`; QEMU uses stock Espressif
QEMU with the meshcom-qemu-raspi emulator overlay. The hardware tests ran on the same patch one upstream
revision earlier (`2a5dcdcd`); the rebase did not change the patch.
