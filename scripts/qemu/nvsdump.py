#!/usr/bin/env python3
"""Read keys from an ESP-IDF NVS partition inside a raw flash image (read-only).

  nvsdump.py IMAGE [--offset 0x9000] [--size 0x5000] [--ns Credentials] [KEY ...]

Prints the current (newest written) value of each requested key, or all keys of
the namespace. Format: ESP-IDF NVS v2 pages (4096 B: 32 B header, 32 B entry
state bitmap, 126 entries of 32 B). Only what MeshCom's Preferences uses is
decoded: I8/U8/I16/U16/I32/U32/I64/U64, strings (SZ) and blobs (8-byte blob =
double, as Preferences::putDouble writes it).
"""
import argparse
import struct

PAGE = 4096
ENTRY = 32
TYPES_INT = {0x01: "<B", 0x11: "<b", 0x02: "<H", 0x12: "<h",
             0x04: "<I", 0x14: "<i", 0x08: "<Q", 0x18: "<q"}


def pages(img, off, size):
    for p in range(off, off + size, PAGE):
        page = img[p:p + PAGE]
        state, seq = struct.unpack_from("<II", page, 0)
        if state == 0xFFFFFFFF:          # never used
            continue
        yield seq, page


def entries(page):
    bitmap = page[32:64]
    i = 0
    while i < 126:
        st = (bitmap[i // 4] >> ((i % 4) * 2)) & 3
        raw = page[64 + i * ENTRY: 64 + (i + 1) * ENTRY]
        ns, typ, span = raw[0], raw[1], raw[2]
        if st != 2 or span == 0 or span == 0xFF:   # 2 = written
            i += 1
            continue
        key = raw[8:24].split(b"\0", 1)[0].decode("ascii", "replace")
        data = raw[24:32]
        extra = page[64 + (i + 1) * ENTRY: 64 + (i + span) * ENTRY]
        yield ns, typ, key, data, extra
        i += span


def decode(typ, data, extra):
    if typ in TYPES_INT:
        return struct.unpack_from(TYPES_INT[typ], data)[0]
    if typ in (0x21, 0x42, 0x41):        # string / blob data / legacy blob
        length = struct.unpack_from("<H", data)[0]
        payload = extra[:length]
        if typ == 0x21:
            return payload.rstrip(b"\0").decode("utf-8", "replace")
        if length == 8:
            return struct.unpack("<d", payload)[0]
        if length == 4:
            return round(struct.unpack("<f", payload)[0], 4)   # Preferences::putFloat
        return payload.hex()
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--offset", type=lambda s: int(s, 0), default=0x9000)
    ap.add_argument("--size", type=lambda s: int(s, 0), default=0x5000)
    ap.add_argument("--ns", default="Credentials")
    ap.add_argument("keys", nargs="*")
    a = ap.parse_args()
    img = open(a.image, "rb").read()
    found = sorted(pages(img, a.offset, a.size), key=lambda t: t[0])
    ns_index = None
    values = {}
    for _, page in found:
        for ns, typ, key, data, extra in entries(page):
            if ns == 0 and key == a.ns:
                ns_index = data[0]
    if ns_index is None:
        raise SystemExit("namespace %r not found" % a.ns)
    for _, page in found:                # later pages overwrite earlier ones
        for ns, typ, key, data, extra in entries(page):
            if ns == ns_index and typ != 0x48:       # skip blob index entries
                values[key] = decode(typ, data, extra)
    for k in (a.keys or sorted(values)):
        print("%s=%s" % (k, values.get(k, "<missing>")))


if __name__ == "__main__":
    main()
