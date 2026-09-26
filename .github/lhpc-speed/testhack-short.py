# TEST ONLY (never part of any PR): at the end of setup, do what the server CONF path does
# (udp_functions.cpp: set a custom node_short, then save_settings()), so --setcall meets a
# persisted custom shortname.
import sys, pathlib
f = pathlib.Path(sys.argv[1]) / "src/esp32/esp32_main.cpp"; s = f.read_text()
a = '    printlndeb("CLIENT STARTED");\n'
assert s.count(a) == 1, s.count(a)
s = s.replace(a, a + '    snprintf(meshcom_settings.node_short, sizeof(meshcom_settings.node_short), "%s", "CUST5");   // TEST ONLY\n    save_settings();   // TEST ONLY\n    printlndeb("[TEST] custom shortname CUST5 saved");   // TEST ONLY\n', 1)
f.write_text(s); print("TEST-ONLY custom-short hack applied")
