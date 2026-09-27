#!/usr/bin/env python3
"""drop-hunks.py IN OUT KEYWORD...: copy a unified diff, dropping every hunk whose added lines contain a keyword,
and whole file sections whose path contains a keyword prefixed with 'file:'."""
import re, sys
src, dst, keys = sys.argv[1], sys.argv[2], sys.argv[3:]
filekeys = [k[5:] for k in keys if k.startswith("file:")]
hdrkeys = [k[4:] for k in keys if k.startswith("hdr:")]
hunkkeys = [k for k in keys if not k.startswith(("file:","hdr:"))]
text = open(src).read()
sections = re.split(r"(?m)^(?=diff --git )", text)
out, dropped = [], []
for sec in sections:
    if not sec.startswith("diff --git "):
        out.append(sec); continue
    path = sec.split("\n", 1)[0].split(" b/")[-1]
    if any(k in path for k in filekeys):
        dropped.append(f"file {path}"); continue
    head, *hunks = re.split(r"(?m)^(?=@@ )", sec)
    kept = []
    for h in hunks:
        added = "\n".join(l for l in h.splitlines() if l.startswith("+"))
        if any(k in added for k in hunkkeys) or any(h.startswith("@@ " + k + ",") for k in hdrkeys):
            dropped.append(f"hunk {path} {h.splitlines()[0][:40]}")
        else:
            kept.append(h)
    if kept:
        out.append(head + "".join(kept))
open(dst, "w").write("".join(out))
print("\n".join(dropped))
