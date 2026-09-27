#!/usr/bin/env python3
"""analyse.py: per-env results of the CI-job logs and build trees (agent 5).

  analyse.py sizes   -> sizes.tsv       env, tree, status, RAM used/max, flash used/max, delta vs base, headroom
  analyse.py warn    -> warnings.txt    warnings per env and tree that base does not have (keyed on file + source text + message)
  analyse.py funcs   -> funcs.txt       per env and tree: functions whose object code differs from base (from .o files,
                                        objdump -d -r of the function's own section, so addresses stay local)

Trees live in ~/claude/agent5-allenvs/<tree>, logs in ~/claude/meshcom-prs-evidence/all-envs/ci-<tree>.log.
"""
import os, re, subprocess, sys, collections, hashlib
from concurrent.futures import ThreadPoolExecutor

W = os.path.expanduser('~/claude/agent5-allenvs')
E = os.path.expanduser('~/claude/meshcom-prs-evidence/all-envs')
PK = os.path.expanduser('~/.platformio/packages')
TREES = [t for t in os.environ.get('TREES', 'base pr1 pr2 pr3 pr12 merge').split()]


def envblocks(tree, logname=None):
    """{env: [lines]} from a pio log (one 'Processing <env>' block per env)."""
    blocks, cur = collections.OrderedDict(), None
    with open(os.path.join(E, logname or f'ci-{tree}.log'), errors='replace') as f:
        for line in f:
            m = re.match(r'Processing (\S+) \(', line)
            if m:
                cur = m.group(1); blocks[cur] = []
            elif line.startswith('=== STEP') or line.startswith('Environment '):
                cur = None
            if cur:
                blocks[cur].append(line.rstrip('\n'))
    return blocks


def status(lines):
    for l in reversed(lines):
        if '[SUCCESS]' in l: return 'SUCCESS'
        if '[FAILED]' in l: return 'FAILED'
    return 'INCOMPLETE'


def mem(lines, kind):
    for l in lines:
        m = re.match(kind + r':\s+\[.*?\]\s+[\d.]+% \(used (\d+) bytes from (\d+) bytes\)', l)
        if m: return int(m.group(1)), int(m.group(2))
    return None, None


def sizes(logsuffix=''):
    data = {t: envblocks(t, f'ci-{t}{logsuffix}.log') for t in TREES if os.path.exists(os.path.join(E, f'ci-{t}{logsuffix}.log'))}
    envs = list(data.get('base', next(iter(data.values()))).keys())
    out = ['env\ttree\tstatus\tram\tram_max\tflash\tflash_max\td_ram\td_flash\tflash_free\tflash_free_pct']
    for env in envs:
        b = data.get('base', {}).get(env, [])
        br, _ = mem(b, 'RAM'); bf, _ = mem(b, 'Flash')
        for t, d in data.items():
            ls = d.get(env)
            if ls is None:
                out.append(f'{env}\t{t}\tNOT-RUN'); continue
            r, rm = mem(ls, 'RAM'); fl, fm = mem(ls, 'Flash')
            dr = '' if r is None or br is None else r - br
            df = '' if fl is None or bf is None else fl - bf
            free = '' if fl is None else fm - fl
            pct = '' if fl is None else f'{100 * (fm - fl) / fm:.2f}'
            out.append(f'{env}\t{t}\t{status(ls)}\t{r}\t{rm}\t{fl}\t{fm}\t{dr}\t{df}\t{free}\t{pct}')
    return '\n'.join(out) + '\n'


WRE = re.compile(r'^(\S+?):(\d+):(\d+): warning: (.*)$')


def warnkeys(tree, env, lines):
    keys = collections.Counter()
    for l in lines:
        m = WRE.match(l)
        if not m:
            if 'warning:' in l: keys[('?', l.strip())] += 1
            continue
        path, ln, _, msg = m.groups()
        src = ''
        p = os.path.join(W, tree, path)
        if os.path.isfile(p):
            try:
                with open(p, errors='replace') as f:
                    src = f.readlines()[int(ln) - 1].strip()
            except IndexError:
                pass
        keys[(path, src, msg)] += 1
    return keys


def warn(logsuffix=''):
    data = {t: envblocks(t, f'ci-{t}{logsuffix}.log') for t in TREES if os.path.exists(os.path.join(E, f'ci-{t}{logsuffix}.log'))}
    out = []
    for env in data['base']:
        bk = warnkeys('base', env, data['base'][env])
        out.append(f'## {env}: base has {sum(bk.values())} warning lines ({len(bk)} distinct)')
        for t in data:
            if t == 'base' or env not in data[t]: continue
            tk = warnkeys(t, env, data[t][env])
            new = tk - bk; gone = bk - tk
            out.append(f'  {t}: {sum(tk.values())} lines, NEW {sum(new.values())}, GONE {sum(gone.values())}')
            for k, n in new.items(): out.append(f'    NEW x{n}: {k}')
            for k, n in gone.items(): out.append(f'    GONE x{n}: {k}')
    return '\n'.join(out) + '\n'


def objdump_for(builddir):
    """Pick the objdump from the ELF header (ARM = nRF52), and esp32 vs esp32s3 from the map file."""
    elf = os.path.join(builddir, 'firmware.elf')
    if not os.path.exists(elf): raise SystemExit(f'no firmware.elf in {builddir}')
    h = subprocess.run(['readelf', '-h', elf], capture_output=True, text=True).stdout
    if 'ARM' in h: return f'{PK}/toolchain-gccarmnoneeabi/bin/arm-none-eabi-objdump'
    if 'Xtensa' not in h: raise SystemExit(f'unknown ELF machine in {elf}')
    txt = open(os.path.join(builddir, 'firmware.map'), errors='replace').read()
    if '/esp32s3/' in txt or 'esp32s3' in txt: return f'{PK}/toolchain-xtensa-esp32s3/bin/xtensa-esp32s3-elf-objdump'
    return f'{PK}/toolchain-xtensa-esp32/bin/xtensa-esp32-elf-objdump'


def _norm(line):
    """Layout-only normalisation: drop self-relative branch targets and alignment padding."""
    if re.match(r'^\s*\.byte 0x?0+$', line.strip()) or line.strip() in ('.byte 00', '...'):
        return None
    line = re.sub(r'\b[0-9a-f]+ <[^>]*\+0x[0-9a-f]+>', '<T>', line)       # j 7848 <f+0x7848>
    line = re.sub(r'\b([a-z0-9]+)\.n\b', r'\1', line)                        # xtensa narrow/wide (s32i.n = s32i)
    line = re.sub(r'\bor\s+(a\d+), (a\d+), \2\b', r'mov \1, \2', line)      # widened mov.n
    line = re.sub(r'\bmovi\s', 'movi ', line)
    line = re.sub(r'\b(CSWTCH|\.LC|\.L)\.?\d+\b', r'\1.N', line)                 # compiler-numbered local labels/tables
    line = re.sub(r'(R_XTENSA_\w+|R_ARM_\w+)\s+(\.text\.\S+?)\+0x[0-9a-f]+', r'\1 \2+<T>', line)
    return re.sub(r'\s+', ' ', line).strip()


def funcsigs(objdump, obj):
    """{section: (exact hash, layout-normalised hash)} of every code section of a relocatable object."""
    r = subprocess.run([objdump, '-d', '-r', '-z', '--no-show-raw-insn', obj], capture_output=True, text=True)
    if r.returncode != 0 or "file format" not in r.stdout:
        raise SystemExit(f'objdump could not read {obj} ({objdump}): {r.stderr[:200]}')
    secs, cur, buf = {}, None, []
    def put():
        if cur is None: return
        exact = hashlib.sha1('\n'.join(buf).encode()).hexdigest()[:12]
        norm = hashlib.sha1('\n'.join(x for x in map(_norm, buf) if x is not None).encode()).hexdigest()[:12]
        secs[cur] = (exact, norm)
    for l in r.stdout.splitlines():
        m = re.match(r'Disassembly of section (\S+):', l)
        if m:
            put(); cur, buf = m.group(1), []
        elif cur is not None:
            buf.append(re.sub(r'^\s*[0-9a-f]+:', '', l))
    put()
    return secs


def objs(builddir):
    res = {}
    # ALLOBJ=1: every object of the env build (framework core + libraries + src), not only src/
    src = builddir if os.environ.get('ALLOBJ') else os.path.join(builddir, 'src')
    for root, _, files in os.walk(src):
        for fn in files:
            if fn.endswith('.o'):
                p = os.path.join(root, fn); res[os.path.relpath(p, builddir)] = p
    return res


def demangle(names):
    r = subprocess.run(['c++filt'], input='\n'.join(names), capture_output=True, text=True)
    return r.stdout.splitlines()


def funcs_env(env, trees):
    bdir = os.path.join(W, os.environ.get('BASE', 'base'), '.pio', 'build', env)
    if not os.path.isdir(bdir): return f'## {env}: no base build\n'
    od = objdump_for(bdir)
    bo = objs(bdir)
    out = [f'## {env} ({os.path.basename(od)})']
    bsig = {k: funcsigs(od, p) for k, p in bo.items()}
    for t in trees:
        tdir = os.path.join(W, t, '.pio', 'build', env)
        if not os.path.isdir(tdir): out.append(f'  {t}: no build'); continue
        to = objs(tdir)
        changed = []
        for k in sorted(set(bo) | set(to)):
            if k not in to: changed.append((k, '(object only in base)')); continue
            if k not in bo: changed.append((k, '(object only in tree)')); continue
            ts = funcsigs(od, to[k]); bs = bsig[k]
            for s in sorted(set(bs) | set(ts)):
                if bs.get(s) != ts.get(s):
                    tag = 'NEW' if s not in bs else 'GONE' if s not in ts else \
                          ('LAYOUT-ONLY' if bs[s][1] == ts[s][1] else 'CHANGED')
                    changed.append((k, f'{tag} {s}'))
        names = demangle([c[1].split(' ', 1)[1].replace('.text.', '', 1) if ' ' in c[1] else c[1] for c in changed])
        out.append(f'  {t}: {len(changed)} code sections differ from base')
        for (k, c), n in zip(changed, names):
            out.append(f'    {k}: {c.split(" ")[0]} {n}')
    return '\n'.join(out) + '\n'


def funcs():
    envs = sys.argv[2:] or [l.strip() for l in open(os.path.join(E, 'envs33.txt'))]
    trees = [t for t in TREES if t != os.environ.get('BASE', 'base')]
    with ThreadPoolExecutor(8) as ex:
        return ''.join(ex.map(lambda e: funcs_env(e, trees), envs))


if __name__ == '__main__':
    cmd = sys.argv[1]
    suffix = os.environ.get('LOGSUFFIX', '')
    if cmd == 'sizes': sys.stdout.write(sizes(suffix))
    elif cmd == 'warn': sys.stdout.write(warn(suffix))
    elif cmd == 'funcs': sys.stdout.write(funcs())
