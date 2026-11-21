#!/usr/bin/env python3
"""make_puyopuy2e.py [FOLDER | puyopuy2.zip] [OUT_FOLDER]

Builds puyopuy2e.zip, Puyo Puyo 2 (English bootleg), from the MAME set puyopuy2.zip.
FOLDER is where puyopuy2.zip is (default: this folder); the new set is written next to
it, or to OUT_FOLDER. Only Python 3 is needed."""
import os, sys, zipfile, zlib, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import romset, build

OUT_NAMES = ('pp2e-17241.ic32', 'pp2e-17240.ic31')
# the CRCs the puyopuy2e entry of mame2003-plus expects
EXPECTED = {'pp2e-17241.ic32': 0x788b7ded, 'pp2e-17240.ic31': 0x68dcbc68, 'epr-17239.ic4': 0x020ff6ef}


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else HERE
    if os.path.isdir(src):
        src = os.path.join(src, 'puyopuy2.zip')
    if not os.path.exists(src):
        raise SystemExit('%s not found: put puyopuy2.zip (the MAME set) there' % src)
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(src))
    prog = romset.read_program(src)
    sound = romset.read_sound(src)
    new = build.build(prog)
    even, odd = romset.split_program(new)
    out = os.path.join(out_dir, 'puyopuy2e.zip')
    files = ((OUT_NAMES[0], even), (OUT_NAMES[1], odd), (romset.SOUND[0], sound))
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in files:
            z.writestr(name, data)
    print('written', out)
    ok = True
    for name, data in files:
        crc = zlib.crc32(data) & 0xffffffff
        print('  %-16s %7d  %08x  %s' % (name, len(data), crc, hashlib.sha1(data).hexdigest()))
        ok = ok and crc == EXPECTED[name]
    print('CRCs match the mame2003-plus driver' if ok else
          'WARNING: the CRCs differ from the ones the mame2003-plus driver expects')


if __name__ == '__main__':
    main()
