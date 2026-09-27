#!/bin/bash
# det-obj.sh <tree> <env>...: rebuild the build-date objects (__DATE__/__TIME__ users) of finished envs with a fixed
# SOURCE_DATE_EPOCH, into .pio/build/<env>/src/*.o (the ELF is NOT relinked; only the object diff uses them).
T=$1; shift; E=~/claude/meshcom-prs-evidence/all-envs
OBJS="command_functions.cpp.o esp32/esp32_main.cpp.o t-deck/tdeck_main.cpp.o web_functions/web_functions.cpp.o rtc_functions.cpp.o nrf52/nrf52_functions.cpp.o"
S="cd /ws && for e in $*; do for o in $OBJS; do f=.pio/build/\$e/src/\$o; [ -f \$f ] || continue; rm -f \$f; pio run -e \$e -t \$f >/dev/null 2>&1 || echo \"DETFAIL \$e \$o\"; [ -f \$f ] && echo \"DET \$e \$o\"; done; done"
podman run --rm --name a5-det-$T-$RANDOM --cpus 2 --security-opt label=disable --network none -v a5-piohome:/root/.platformio -e SOURCE_DATE_EPOCH=1790000000 -v ~/claude/agent5-allenvs/$T:/ws a5-meshcom-ci:1 bash -c "$S"
