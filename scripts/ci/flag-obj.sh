#!/bin/bash
# flag-obj.sh <tree> "<flags>" <env>...: build ONLY src/esp32/esp32_main.cpp.o per env, with PLATFORMIO_BUILD_FLAGS and
# SOURCE_DATE_EPOCH=1790000000 (deterministic), offline, from the cached pio home.
T=$1; F=$2; shift 2
S="cd /ws && for e in $*; do f=.pio/build/\$e/src/esp32/esp32_main.cpp.o; rm -f \$f; pio run -e \$e -t \$f >/dev/null 2>&1; [ -f \$f ] && echo \"FLAGOBJ \$e ok\" || echo \"FLAGOBJ \$e FAIL\"; done"
podman run --rm --name a5-fo-$T-$RANDOM --cpus 3 --security-opt label=disable --network none -v a5-piohome:/root/.platformio \
  -e SOURCE_DATE_EPOCH=1790000000 -e PLATFORMIO_BUILD_FLAGS="$F" -v ~/claude/agent5-allenvs/$T:/ws a5-meshcom-ci:1 bash -c "$S"
