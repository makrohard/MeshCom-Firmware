#!/usr/bin/env python3
"""relax_check.py: prove that the two ttgo_tbeam_supreme esp32loop cases differ ONLY by one Xtensa branch relaxation.
Takes the strict-normalised streams from layout_audit.parse(); finds the single place where BEFORE has
'b<cc> R, @I(i+2)' + 'j @I(T)' and AFTER has 'b<inverse cc> R, @I(T')'; then checks that EVERY other instruction is
identical once AFTER ordinals >= i+1 are mapped back (+1) to BEFORE numbering."""
import sys, re, os
sys.path.insert(0, os.path.dirname(__file__)); import layout_audit as L
INV = {'bnez': 'beqz', 'beqz': 'bnez', 'bne': 'beq', 'beq': 'bne', 'blt': 'bge', 'bge': 'blt', 'bltu': 'bgeu',
       'bgeu': 'bltu', 'bnei': 'beqi', 'beqi': 'bnei', 'blti': 'bgei', 'bgei': 'blti', 'bbc': 'bbs', 'bbs': 'bbc',
       'bbci': 'bbsi', 'bbsi': 'bbci', 'bany': 'bnone', 'bnone': 'bany', 'ball': 'bnall', 'bnall': 'ball'}
od = '/home/makro/.platformio/packages/toolchain-xtensa-esp32s3/bin/xtensa-esp32s3-elf-objdump'
W = '/home/makro/claude/agent5-allenvs'; sec = '.text._Z9esp32loopv'
for tree, base in [('merge-fble', 'merge'), ('pr3-fble', 'pr3')]:
    bo = f'{W}/{base}/.pio/build/ttgo_tbeam_supreme/src/esp32/esp32_main.cpp.o'
    to = f'{W}/{tree}/.pio/build/ttgo_tbeam_supreme/src/esp32/esp32_main.cpp.o'
    B = L.parse(L.dump(od, bo, sec, '-d', '-r', '-z', '--no-show-raw-insn'), sec, od, bo)
    A = L.parse(L.dump(od, to, sec, '-d', '-r', '-z', '--no-show-raw-insn'), sec, od, to)
    assert len(B) == len(A) + 1, (len(B), len(A))
    found = None
    for i in range(len(A)):
        mb = re.match(r'^(\w+) (.*), @I(\d+) ', B[i]); mj = re.match(r'^j @I(\d+) ', B[i + 1]); ma = re.match(r'^(\w+) (.*), @I(\d+) ', A[i])
        if mb and mj and ma and int(mb.group(3)) == i + 2 and INV.get(mb.group(1)) == ma.group(1) and mb.group(2) == ma.group(2):
            if int(ma.group(3)) + (1 if int(ma.group(3)) >= i + 1 else 0) == int(mj.group(1)):
                found = i; break
    assert found is not None, 'no relaxation pattern found'
    i = found
    remap = lambda line: re.sub(r'@I(\d+)', lambda m: f'@I{int(m.group(1)) + (1 if int(m.group(1)) >= i + 1 else 0)}', line)
    rest_a = [remap(x) for k, x in enumerate(A) if k != i]
    rest_b = [x for k, x in enumerate(B) if k not in (i, i + 1)]
    ok = rest_a == rest_b
    print(f'{tree} vs {base} ttgo_tbeam_supreme esp32loop: relaxation at instruction {i}:')
    print(f'   before: {B[i].strip()}  |  {B[i + 1].strip()}')
    print(f'   after : {A[i].strip()}')
    print(f'   all other {len(rest_b)} instructions identical after ordinal remap: {ok}')
    lb, la = L.literal(od, bo, sec), L.literal(od, to, sec)
    print(f'   literal pool identical (content-canonical): {lb == la}')
