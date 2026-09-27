#!/usr/bin/env python3
"""layout_audit.py: strict re-check of every section analyse.py classified LAYOUT-ONLY (audit 5 v2, F1).

analyse.py's _norm() maps every in-function branch target to <T>, so a retargeted branch could hide there. This
checker keeps branch-target identity:
  - padding is dropped ('.byte 00', 'nop', 'nop.n'); nothing else is;
  - every kept instruction gets an ordinal; a branch/jump/call target or a self-section relocation '.text.<f>+0xNN'
    is replaced by '@I<ordinal of the instruction at NN>' (padding offsets map to the next kept instruction);
  - Xtensa narrow/wide forms are canonicalised ('s32i.n' = 's32i'; 'or aX, aY, aY' = 'mov aX, aY');
  - literal-pool relocations ('.literal.<f>+0xNN') and all relocations to other symbols stay EXACT;
  - the function's literal pool section ('.literal.<f>') must be identical too (bytes + relocations).
Result per case: STRICT-EQUIVALENT (same instruction sequence, same targets, same literals) or STRICT-DIFF (printed
for manual review). Raw unnormalised objdump of both sides goes to the raw file.

  layout_audit.py <funcs-file> <base-tree> <out-summary> <out-raw> [extra cases file]
  extra cases: lines 'tree env objrel section' (e.g. the flag diffs' esp32loop cases, compared against their base).
"""
import os, re, sys, subprocess, collections
sys.path.insert(0, os.path.dirname(__file__)); import analyse as A

PAD = re.compile(r'^\s*(\.byte\s+0x?0+|nop(\.n)?)\s*$')
INS = re.compile(r'^\s*([0-9a-f]+):\t(.*)$')
REL = re.compile(r'^\t+\s*([0-9a-f]+): (R_\S+)\t(.*)$')


_SEC_CACHE = {}


def section_bytes(od, obj, sec):
    """exact raw bytes of one section (objcopy -O binary --only-section), no hex-dump parsing"""
    k = (obj, sec)
    if k in _SEC_CACHE: return _SEC_CACHE[k]
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.bin') as tf:
        r = subprocess.run([od.replace('objdump', 'objcopy'), '-O', 'binary', '--only-section=' + sec, obj, tf.name],
                           capture_output=True, text=True)
        if r.returncode != 0: raise SystemExit(f'objcopy failed for {sec} in {obj}: {r.stderr[:200]}')
        _SEC_CACHE[k] = open(tf.name, 'rb').read()
    return _SEC_CACHE[k]


def canon_target(od, obj, tgt):
    """identity of a relocation target by CONTENT where the name/offset is compiler-numbered or layout-dependent:
    '.rodata.*str*+0xNN' -> the NUL-terminated string at NN; '.rodata.CSWTCH.N' (+0xNN) -> sha of the table's bytes
    and its own canonical relocations, plus the offset. Everything else stays exact."""
    m = re.match(r'^(\.rodata\.\S*?)(\+0x([0-9a-f]+))?$', tgt)
    if not m: return tgt
    sec, off = m.group(1), int(m.group(3) or '0', 16)
    if '.str' in sec:
        b = section_bytes(od, obj, sec); e = b.find(b'\0', off)
        return 'STR' + repr(b[off:e if e >= 0 else len(b)].decode('latin-1'))
    if re.search(r'CSWTCH\.\d+$', sec) or re.search(r'\.\d+$', sec):
        import hashlib
        rel = subprocess.run([od, '-r', '-j', sec, obj], capture_output=True, text=True).stdout
        rels = [(x.split()[0], x.split()[1], canon_target(od, obj, x.split()[2])) for x in rel.splitlines()
                if re.match(r'^[0-9a-f]{8} R_', x)]
        h = hashlib.sha1(section_bytes(od, obj, sec) + repr(rels).encode()).hexdigest()[:12]
        return f'DATA[{h}]+{off:#x}'
    return tgt


def dump(od, obj, sec, *opts):
    r = subprocess.run([od, *opts, '-j', sec, obj], capture_output=True, text=True)
    return [l for l in r.stdout.splitlines() if 'file format' not in l]


def parse(lines, sec, od=None, obj=None):
    ins, rels = [], collections.defaultdict(list)
    for l in lines:
        m = REL.match(l)
        if m: rels[int(m.group(1), 16)].append((m.group(2), m.group(3).strip())); continue
        m = INS.match(l)
        if m: ins.append((int(m.group(1), 16), m.group(2).strip()))
    kept = [(o, t) for o, t in ins if not PAD.match(t)]
    offs = sorted(o for o, _ in kept)
    def ordinal(off):
        for i, o in enumerate(offs):
            if o >= off: return i
        return len(offs)
    fname = sec.split('.', 2)[-1]                  # .text._Z11WZ_GPS_Initv -> _Z11WZ_GPS_Initv
    out = []
    for o, t in kept:
        t = re.sub(r'\s+', ' ', t)
        mn, _, ops = t.partition(' ')
        mn = re.sub(r'\.n$', '', mn)
        m = re.match(r'(a\d+), (a\d+), \2$', ops)
        if mn == 'or' and m: mn, ops = 'mov', f'{m.group(1)}, {m.group(2)}'
        # l32r's printed operand is a fake address; its identity is the literal relocation below
        if mn == 'l32r': ops = re.sub(r'[0-9a-f]+ <[^>]*>', '<lit>', ops)
        ops = re.sub(r'\b([0-9a-f]+) <' + re.escape(fname) + r'(\+0x([0-9a-f]+))?>',
                     lambda mm: f'@I{ordinal(int(mm.group(3) or "0", 16))}', ops)
        # a remaining 'hex <othersym+0xNN>' annotation is objdump's nearest-symbol guess for an unrelocated
        # address (display only); the encoded hex stays, the annotation goes
        ops = re.sub(r'\b([0-9a-f]+) <[^>]*>', r'\1', ops)
        rl = []
        for typ, tgt in rels.get(o, []):
            m2 = re.match(r'\.text\.' + re.escape(fname) + r'(\+0x([0-9a-f]+))?$', tgt)
            if not m2 and typ == 'R_ARM_ABS32' and mn == '.word' and re.match(r'^0x[0-9a-f]+$', ops.strip()):
                mt = re.match(r'^(.*?)(\+0x([0-9a-f]+))?$', tgt)       # REL: the .word value is the addend
                tgt = f'{mt.group(1)}+{int(mt.group(3) or "0", 16) + int(ops.strip(), 16):#x}'
                ops = '<addend>'
            rl.append(f'{typ} @I{ordinal(int(m2.group(2) or "0", 16))}' if m2 else f'{typ} {canon_target(od, obj, tgt)}')
        out.append(f'{mn} {ops} ' + ' ; '.join(rl))
    return out


def literal(od, obj, sec):
    """literal pool identity: bytes with the relocated words masked, plus the relocations with content-canonical
    targets. R_XTENSA_32 is partial_inplace: the effective target is symbol + RELA addend + the 32-bit word stored at
    the relocated offset, so that in-place word is added to the target offset (and masked in the byte compare)."""
    import struct
    lsec = sec.replace('.text.', '.literal.', 1)
    b = bytearray(section_bytes(od, obj, lsec))
    rel = subprocess.run([od, '-r', '-j', lsec, obj], capture_output=True, text=True).stdout
    rels = []
    for x in rel.splitlines():
        if not re.match(r'^[0-9a-f]{8} R_', x): continue
        off, typ, tgt = x.split()[0], x.split()[1], x.split()[2]
        o = int(off, 16)
        if typ == 'R_XTENSA_32' and o + 4 <= len(b):
            inplace = struct.unpack_from('<I', b, o)[0]
            m = re.match(r'^(.*?)(\+0x([0-9a-f]+))?$', tgt)
            tgt = f'{m.group(1)}+{int(m.group(3) or "0", 16) + inplace:#x}'
            b[o:o + 4] = b'\0\0\0\0'
        rels.append((off, typ, canon_target(od, obj, tgt)))
    return (bytes(b), rels)


def cases_from_funcs(path):
    env = tree = None
    for l in open(path):
        m = re.match(r'## (\S+)', l)
        if m: env = m.group(1); continue
        m = re.match(r'  ([\w-]+): ', l)
        if m: tree = m.group(1); continue
        m = re.match(r'    (\S+): LAYOUT-ONLY (.*)', l)
        if m and not m.group(2).startswith('.literal'):
            yield tree, env, m.group(1), None, m.group(2)


def section_for(od, obj, demangled):
    """find the .text.* section whose demangled name matches (analyse.py printed demangled names)"""
    h = subprocess.run([od, '-h', obj], capture_output=True, text=True).stdout
    secs = re.findall(r'\s(\.text\.\S+)\s', h)
    names = A.demangle([s.replace('.text.', '', 1) for s in secs])
    for s, n in zip(secs, names):
        if n == demangled: return s
    raise SystemExit(f'no section for {demangled} in {obj}')


def main():
    funcs, base, out_sum, out_raw = sys.argv[1:5]
    extra = sys.argv[5] if len(sys.argv) > 5 else None
    cases = list(cases_from_funcs(funcs))
    if extra:
        for l in open(extra):
            if l.strip() and not l.startswith('#'):
                t, e, o, b, s = l.split()
                cases.append((t, e, o, b, s))
    summ, raw, verdicts = [], [], collections.Counter()
    for tree, env, objrel, btree, name in cases:
        btree = btree or base
        bdir = os.path.join(A.W, btree, '.pio', 'build', env); tdir = os.path.join(A.W, tree, '.pio', 'build', env)
        od = A.objdump_for(bdir)
        bo, to = os.path.join(bdir, objrel), os.path.join(tdir, objrel)
        sec = name if name.startswith('.text.') else section_for(od, bo, name)
        rb = dump(od, bo, sec, '-d', '-r', '-z', '--no-show-raw-insn')
        rt = dump(od, to, sec, '-d', '-r', '-z', '--no-show-raw-insn')
        sb, st = parse(rb, sec, od, bo), parse(rt, sec, od, to)
        if not sb or not st:   # a missing/empty section must never compare as "equivalent"
            raise SystemExit(f'EMPTY or MISSING section {sec} in {bo if not sb else to}')
        lit_same = literal(od, bo, sec) == literal(od, to, sec)
        ok = sb == st and lit_same
        v = 'STRICT-EQUIVALENT' if ok else 'STRICT-DIFF'
        verdicts[v] += 1
        why = []
        if sb != st: why.append(f'instruction stream differs ({len(sb)} vs {len(st)} kept instructions)')
        if not lit_same: why.append('literal pool differs')
        summ.append(f'{v:18s} {tree:12s} vs {btree:6s} {env:30s} {objrel} {sec} ' + ('; '.join(why)))
        raw.append(f'\n######## {v} {tree} vs {btree} | {env} | {objrel} | {sec}\n'
                   f'#### BEFORE ({btree}) raw objdump -d -r -z --no-show-raw-insn\n' + '\n'.join(rb) +
                   f'\n#### AFTER ({tree})\n' + '\n'.join(rt))
        if not ok:
            import difflib
            raw.append('#### STRICT-NORMALISED DIFF (for manual review)\n' +
                       '\n'.join(difflib.unified_diff(sb, st, 'before', 'after', lineterm='', n=3)))
    open(out_sum, 'w').write(f'# layout_audit.py: {sum(verdicts.values())} cases: ' +
                             ', '.join(f'{k} {n}' for k, n in verdicts.items()) + '\n' + '\n'.join(summ) + '\n')
    open(out_raw, 'w').write('\n'.join(raw) + '\n')
    print(dict(verdicts))


if __name__ == '__main__':
    main()
