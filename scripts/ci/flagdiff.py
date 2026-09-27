#!/usr/bin/env python3
"""flagdiff.py <base-tree> <tree>...: per ESP32 app env, diff src/esp32/esp32_main.cpp.o of each tree against base-tree
(both deterministic), by function section; prints non-layout changes (analyse.py's normalisation)."""
import os, sys, collections
sys.path.insert(0, os.path.dirname(__file__)); import analyse as A
base, trees = sys.argv[1], sys.argv[2:]
envs = [l.strip() for l in open(os.path.join(A.E, 'envs27-esp32app.txt'))]
groups = collections.defaultdict(lambda: collections.defaultdict(list))
for e in envs:
    bdir = os.path.join(A.W, base, '.pio', 'build', e)
    od = A.objdump_for(bdir)
    bs = A.funcsigs(od, os.path.join(bdir, 'src/esp32/esp32_main.cpp.o'))
    for t in trees:
        o = os.path.join(A.W, t, '.pio', 'build', e, 'src/esp32/esp32_main.cpp.o')
        if not os.path.exists(o): groups[t][('MISSING OBJECT',)].append(e); continue
        ts = A.funcsigs(od, o); ch = []
        for s in sorted(set(bs) | set(ts)):
            if s.startswith('.literal'): continue
            if s not in bs: ch.append('NEW ' + s)
            elif s not in ts: ch.append('GONE ' + s)
            elif bs[s][1] != ts[s][1]: ch.append('CHANGED ' + s)
        groups[t][tuple(A.demangle([c.split(' ', 1)[1].replace('.text.', '', 1) for c in ch]) and
                        [c.split(' ')[0] + ' ' + n for c, n in zip(ch, A.demangle([c.split(' ', 1)[1].replace('.text.', '', 1) for c in ch]))])].append(e)
for t in trees:
    print(f'=== {t} vs {base} (esp32_main.cpp.o)')
    for k, es in sorted(groups[t].items(), key=lambda x: -len(x[1])):
        print(f'  [{len(es)} envs] {" ".join(es)}')
        for x in k: print('     ', x)
