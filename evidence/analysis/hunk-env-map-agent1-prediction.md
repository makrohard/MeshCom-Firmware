# Which of our hunks each env compiles (agent 1 reference map, 2026-09-26)

Source: merge a7957f7a (tree 58d99cd9), resolved with `pio project config --json-output` (src filters, build_flags, -I variant configuration.h #defines) + the #if guards around each hunk (scratchpad refmap/map.py, guards.py). Y = compiled and guard-active; file-only = file compiled, hunk guarded out; - = file not compiled. ENABLE_GPS is read from configuration.h #define lines (a heuristic: an #if around the #define is not evaluated). CONFIRM every Y/- against the built artifacts (nm / strings / map file); this map is a prediction, not proof.

Safeboot correction: esp32-safeboot / esp32-S3-safeboot compile esp32/esp32_flash.cpp WITHOUT a guard around save_settings/save_msgid/save_position (only lines 4-12 and 27-66 are MC_SAFEBOOT-guarded), so PR1's save_msgid()+save_position() ARE compiled there: the safeboot builds are in scope and must pass. CORRECTED by agent 5's artifact check (2026-09-26): they are compiled into the object (nm esp32_flash.cpp.o: `T save_msgid()`, `T save_position()` on pr1/merge, only `T save_settings()` on base) but LINKED OUT of the ELF (no caller in safeboot; LTO + gc-sections drop even the stock save_settings), so the safeboot image is identical in code and data across base/pr1/merge; it differs only in the embedded ELF SHA-256 (0xB0) and the appended image checksum/digest, caused by debug/symbol records (.debug_info/.debug_str/.symtab) of the unreferenced save_msgid/save_position (agent 5, cmp + hash, 2026-09-26; base = pr2 = pr3 byte-identical, i.e. reproducible). Row = "compiled (object), linked out (no caller); build green".

```
env                          platform  PR1 9 save_msgid sites + {SET} save  PR1 save_msgid() ESP32 impl  PR1 nRF52 save_msgid macro  PR1 --aprsmc save / PR2 setcall  PR1 GPS save_position  PR1 XML utcoff  PR1 T-Deck UI saves  PR1 T-Deck Pro keypad  PR3a net console  PR3b/c batt+BLE (flag-gated)
esp32-safeboot               ESP32     -                                    file-only                    -                           -                                -                      -               -                    -                      -                 -
esp32-S3-safeboot            ESP32     -                                    file-only                    -                           -                                -                      -               -                    -                      -                 -
E22_1262-DevKitC             ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    -                      Y                 Y
E22-DevKitC                  ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    -                      Y                 Y
E22_XML-DevKitC              ESP32     Y                                    Y                            -                           Y                                Y                      Y               -                    -                      file-only         Y
E22_1268_S3-DevKitC-1-N16R8  ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    -                      Y                 Y
E22_1262_S3-DevKitC-1-N16R8  ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    -                      Y                 Y
heltec_wifi_lora_32_V2       ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    -                      Y                 Y
heltec_wifi_lora_32_V3       ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    -                      Y                 Y
heltec_wifi_lora_32_V4       ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    -                      Y                 Y
heltec_wireless_stick        ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    -                      Y                 Y
heltec_wireless_tracker      ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    -                      Y                 Y
heltec_t114                  nRF52     Y                                    -                            Y                           Y                                file-only              file-only       -                    -                      file-only         -
vision-master-e290           ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    -                      Y                 Y
vision-master-e213           ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    -                      Y                 Y
wireless-paper               ESP32     Y                                    Y                            -                           Y                                file-only              file-only       -                    -                      Y                 Y
T-ETH-ELITE_1262             ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    -                      Y                 Y
LilyGo_T-Beam-1W             ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    -                      Y                 Y
LilyGo_T3_S3_V1_3            ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    -                      Y                 Y
LilyGo_T_Connect_Pro         ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    -                      Y                 Y
ttgo-lora32-v21              ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    -                      Y                 Y
ttgo_tbeam                   ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    -                      Y                 Y
ttgo_tbeam_SX1262            ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    -                      Y                 Y
ttgo_tbeam_SX1268            ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    -                      Y                 Y
ttgo_tbeam_supreme           ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    -                      Y                 Y
t_deck                       ESP32     Y                                    Y                            -                           Y                                Y                      file-only       Y                    -                      Y                 Y
t_deck_plus                  ESP32     Y                                    Y                            -                           Y                                Y                      file-only       Y                    -                      Y                 Y
t_deck_pro                   ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    Y                      Y                 Y
t_echo                       nRF52     Y                                    -                            Y                           Y                                file-only              file-only       -                    -                      file-only         -
wiscore_rak4631              nRF52     Y                                    -                            Y                           Y                                file-only              file-only       -                    -                      file-only         -
esp32-loraprs-e22            ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    -                      Y                 Y
esp32-loraprs-ra01           ESP32     Y                                    Y                            -                           Y                                Y                      file-only       -                    -                      Y                 Y
t5_epaper                    ESP32     Y                                    Y                            -                           Y                                file-only              file-only       -                    -                      Y                 Y
```

Hunk guards (merge vs cf215b5d):
```
src/command_functions.cpp:3773 (+3)  guards: -
src/command_functions.cpp:3779 (+3)  guards: -
src/command_functions.cpp:3785 (+3)  guards: -
src/command_functions.cpp:5664 (+2)  guards: -
src/esp32/esp32_flash.cpp:623 (+24)  guards: -
src/esp32/esp32_flash.h:245 (+4)  guards: #ifndef _ESP32_FLASH_H_
src/esp32/esp32_flash.h:250 (+2)  guards: #ifndef _ESP32_FLASH_H_
src/esp32/esp32_main.cpp:1059 (+3)  guards: #if defined(DISABLE_BATTERY)   // opt-out -D DISABLE_BATTERY: board without a battery divider
src/esp32/esp32_main.cpp:1780 (+1)  guards: #if !defined(DISABLE_BLE)   // opt-out -D DISABLE_BLE: board without a usable BLE controller
src/esp32/esp32_main.cpp:1872 (+3)  guards: NOT(#if !defined(DISABLE_BLE)   // opt-out -D DISABLE_BLE: board without a usable BLE controller)
src/esp32/esp32_main.cpp:1953 (+3)  guards: #if defined(DISABLE_BLE)
src/esp32/esp32_main.cpp:1961 (+1)  guards: -
src/esp32/esp32_main.cpp:2012 (+1)  guards: #if defined(BENCH_BLE_ADV_LATE) && !defined(DISABLE_BLE)
src/esp32/esp32_main.cpp:3598 (+9)  guards: #if defined(DISABLE_BATTERY)
src/gps_functions.cpp:1254 (+11)  guards: #ifdef ENABLE_GPS & #ifdef ESP32
src/loop_functions.cpp:2337 (+2)  guards: -
src/loop_functions.cpp:2340 (+2)  guards: -
src/loop_functions.cpp:3344 (+1)  guards: -
src/loop_functions.cpp:3446 (+1)  guards: -
src/loop_functions.cpp:4099 (+1)  guards: -
src/loop_functions.cpp:4284 (+1)  guards: -
src/loop_functions.cpp:4859 (+1)  guards: -
src/loop_functions.cpp:4946 (+1)  guards: -
src/loop_functions.cpp:5016 (+1)  guards: -
src/loop_functions.cpp:5108 (+1)  guards: -
src/loop_functions.cpp:5447 (+1)  guards: -
src/net_console.cpp:44 (+4)  guards: #if defined(ESP32) && !defined(DISABLE_NET_CONSOLE)
src/net_console.cpp:352 (+9)  guards: #if defined(ESP32) && !defined(DISABLE_NET_CONSOLE)
src/nrf52/WisBlock-API.h:615 (+2)  guards: #ifndef SX126x_API_H
src/nrf52/nrf_eth.cpp:766 (+1)  guards: -
src/t-deck-pro/peri_keypad.cpp:258 (+2)  guards: -
src/t-deck-pro/peri_keypad.cpp:267 (+2)  guards: -
src/t-deck-pro/peri_keypad.cpp:279 (+2)  guards: -
src/t-deck-pro/peri_keypad.cpp:291 (+2)  guards: -
src/t-deck-pro/peri_keypad.cpp:305 (+2)  guards: -
src/t-deck/lv_obj_functions.cpp:375 (+2)  guards: -
src/t-deck/lv_obj_functions.cpp:408 (+2)  guards: -
src/t-deck/tdeck_main.cpp:1080 (+2)  guards: -
src/tinyxml_functions.cpp:309 (+5)  guards: #if defined(ENABLE_XML)
src/udp_functions.cpp:611 (+2)  guards: #ifdef ESP32
```
