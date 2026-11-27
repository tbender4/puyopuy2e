#!/usr/bin/env python3
"""make_puyopuy2e_md.py [--logo MODE] [ROM | FOLDER] [OUT_ROM]

Builds the English Mega Drive ROM from Puyo Puyo 2 (Japan) (v1.1).md (raw 2 MB dump,
CRC32 25b7b2aa). Only Python 3 standard library is needed."""
import argparse, hashlib, os, sys, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import logo, md_build

ORIG_NAME = 'Puyo Puyo 2 (Japan) (v1.1).md'
ORIG_SIZE = 0x200000
ORIG_CRC = 0x25b7b2aa
OUT_DEFAULT = 'Puyo Puyo 2 (English) (v1.1).md'


def read_rom(src):
    """the input ROM's bytes, after checking it is the expected dump"""
    data = open(src, 'rb').read()
    crc = zlib.crc32(data)
    if len(data) != ORIG_SIZE or crc != ORIG_CRC:
        raise SystemExit('unexpected input ROM (%d bytes, CRC32 %08x): need raw 2 MB '
                         'Puyo Puyo 2 (Japan) (v1.1).md (CRC32 %08x, not .smd)' %
                         (len(data), crc, ORIG_CRC))
    return data


def main():
    p = argparse.ArgumentParser(usage='make_puyopuy2e_md.py [--logo MODE] [ROM | FOLDER] [OUT_ROM]')
    p.add_argument('--logo', choices=logo.MODES, default=logo.DEFAULT_MODE,
                   help='title logo variant (default: %(default)s)')
    p.add_argument('src', nargs='?')
    p.add_argument('out', nargs='?')
    args = p.parse_intermixed_args()

    src = args.src or HERE
    if os.path.isdir(src):
        src = os.path.join(src, ORIG_NAME)
    if not os.path.exists(src):
        raise SystemExit('%s not found: supply Puyo Puyo 2 (Japan) (v1.1).md' % src)

    out = args.out or os.path.join(os.path.dirname(os.path.abspath(src)), OUT_DEFAULT)
    if os.path.isdir(out):
        out = os.path.join(out, OUT_DEFAULT)
    if os.path.abspath(out) == os.path.abspath(src):
        raise SystemExit('refusing to overwrite the input ROM: %s' % src)

    new = bytes(md_build.build(read_rom(src), args.logo))
    with open(out, 'wb') as f:
        f.write(new)
    out_crc = zlib.crc32(new)
    print('written %s (%d bytes, CRC32 %08x, SHA1 %s, logo=%s)' %
          (out, len(new), out_crc, hashlib.sha1(new).hexdigest(), args.logo))


if __name__ == '__main__':
    main()
