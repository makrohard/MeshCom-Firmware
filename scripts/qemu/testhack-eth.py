# TEST ONLY (never part of any PR): make the emulator build look like an Ethernet board in Ethernet mode,
# so upstream's and PR3a's net-console gates can be compared on a real non-WiFi IP network.
import sys, pathlib
f = pathlib.Path(sys.argv[1]) / "src/net_console.cpp"; s = f.read_text()
a = '#include "net_console.h"\n'
assert s.count(a) == 1
s = s.replace(a, a + '#include <esp32/esp32_flash.h>   // TEST ONLY\n#define HAS_ETHERNET                 // TEST ONLY\n', 1)
b = "void loopNetConsole()\n{\n"
assert s.count(b) == 1
s = s.replace(b, b + "    meshcom_settings.node_netmode = 1;   // TEST ONLY: Ethernet mode\n", 1)
f.write_text(s); print("TEST-ONLY Ethernet hack applied to", f)
