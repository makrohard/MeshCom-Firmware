#!/bin/bash
# safeboot_proof.sh: raw evidence for report item 7 (audit 5 v2, F3). Read-only over the built trees.
W=~/claude/agent5-allenvs; PK=~/.platformio/packages
for e in esp32-safeboot esp32-S3-safeboot; do
  case $e in esp32-safeboot) n=safeboot; T=$PK/toolchain-xtensa-esp32/bin/xtensa-esp32-elf ;; *) n=safeboot-s3; T=$PK/toolchain-xtensa-esp32s3/bin/xtensa-esp32s3-elf ;; esac
  echo "################ $e"
  echo "## sha256 of $n.bin / $n.elf per tree"
  for t in base pr1 pr2 pr3 pr12 merge; do echo "$t $(sha256sum < $W/$t/.pio/build/$e/$n.bin | cut -d' ' -f1) bin  $(sha256sum < $W/$t/.pio/build/$e/$n.elf | cut -d' ' -f1) elf"; done
  for t in pr1 merge; do
    echo "## \$ cmp -l base/$n.bin $t/$n.bin   (byte offset 1-based, octal old, octal new)"
    cmp -l $W/base/.pio/build/$e/$n.bin $W/$t/.pio/build/$e/$n.bin
    echo "## differing 0-based byte ranges; image size $(stat -c%s $W/base/.pio/build/$e/$n.bin)"
    cmp -l $W/base/.pio/build/$e/$n.bin $W/$t/.pio/build/$e/$n.bin | awk '{print $1-1}' | awk 'NR==1{s=$1;p=$1;next} $1==p+1{p=$1;next} {printf "%d-%d\n",s,p; s=$1;p=$1} END{printf "%d-%d\n",s,p}'
    echo "## \$ $(basename $T)-readelf -S -W base/$n.elf  vs  $t/$n.elf  (diff of the section tables)"
    diff <($T-readelf -S -W $W/base/.pio/build/$e/$n.elf) <($T-readelf -S -W $W/$t/.pio/build/$e/$n.elf)
    echo "## per-section CONTENT comparison (objcopy --dump-section, every section incl. non-ALLOC debug sections), base vs $t"
    for s in $($T-readelf -S -W $W/base/.pio/build/$e/$n.elf | awk -F']' '/^ +\[ *[0-9]+\]/{split($2,a," "); if (a[1]!="NULL") print a[1]}'); do
      D=$(mktemp -d); $T-objcopy --dump-section "$s=$D/a" $W/base/.pio/build/$e/$n.elf $D/x1 2>/dev/null; $T-objcopy --dump-section "$s=$D/b" $W/$t/.pio/build/$e/$n.elf $D/x2 2>/dev/null
      sa=$(stat -c%s $D/a 2>/dev/null || echo NA); sb=$(stat -c%s $D/b 2>/dev/null || echo NA)
      if [ "$sa" = NA ] || [ "$sb" = NA ]; then echo "  NO-CONTENT $s (NOBITS or empty: $sa / $sb bytes)";
      elif cmp -s $D/a $D/b; then echo "  same     $s ($sa bytes)"; else echo "  DIFFERS  $s ($sa vs $sb bytes)"; fi; rm -rf $D
    done
  done
  echo "## \$ nm -C .pio/build/$e/src/esp32/esp32_flash.cpp.o | grep save_  (LTO object, per tree)"
  for t in base pr1 pr2 pr3 pr12 merge; do echo "# $t"; nm -C $W/$t/.pio/build/$e/src/esp32/esp32_flash.cpp.o 2>&1 | grep -E 'save_(settings|msgid|position)'; done
  echo "## \$ nm -C $n.elf | grep save_  (linked image, per tree; empty = not linked in)"
  for t in base pr1 merge; do echo "# $t: $($T-nm -C $W/$t/.pio/build/$e/$n.elf | grep -cE 'save_(settings|msgid|position)') matching symbols"; done
done
echo "################ symbol-table comparison (.symtab cannot be dumped): readelf -sW, symbols grouped by their section"
for e in esp32-safeboot esp32-S3-safeboot; do
  case $e in esp32-safeboot) n=safeboot; T=$PK/toolchain-xtensa-esp32/bin/xtensa-esp32-elf ;; *) n=safeboot-s3; T=$PK/toolchain-xtensa-esp32s3/bin/xtensa-esp32s3-elf ;; esac
  for t in pr1 merge; do
  echo "## $e base vs $t"
  python3 - "$T-readelf" "$W/base/.pio/build/$e/$n.elf" "$W/$t/.pio/build/$e/$n.elf" <<'PY'
import sys, subprocess, re, collections
re_, a, b = sys.argv[1:4]
def syms(f):
    secs = {}
    for l in subprocess.run([re_, '-SW', f], capture_output=True, text=True).stdout.splitlines():
        m = re.match(r'^\s+\[\s*(\d+)\]\s+(\S+)', l)
        if m: secs[m.group(1)] = m.group(2)
    out = collections.Counter()
    for l in subprocess.run([re_, '-sW', f], capture_output=True, text=True).stdout.splitlines():
        p = l.split()
        if len(p) >= 8 and p[0].endswith(':') and p[0][:-1].isdigit():
            sec = secs.get(p[6], p[6])                      # ABS/UND/COM stay as-is
            out[(sec, p[1], p[2], p[3], p[4], p[7])] += 1
    return out
A, B = syms(a), syms(b)
nondebug = lambda c: collections.Counter({k: v for k, v in c.items() if not k[0].startswith('.debug')})
dA, dB = nondebug(A), nondebug(B)
print(f'  symbols in NON-debug sections (value, size, type, bind, name): base {sum(dA.values())}, other {sum(dB.values())}, identical: {dA == dB}')
for k in sorted((dA - dB).keys()): print('   only base :', k)
for k in sorted((dB - dA).keys()): print('   only other:', k)
dbg = collections.Counter(k[0] for k in (A - B) + (B - A) if k[0].startswith('.debug'))
print(f'  differing symbols located IN debug sections: {dict(dbg)}')
PY
  done
done
