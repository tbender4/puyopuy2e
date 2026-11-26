#!/usr/bin/env python3
"""make_puyopuy2e_saturn.py [--logo MODE] [--fast] [TRACK1_BIN | FOLDER] [OUT_DIR]

Builds the English Sega Saturn disc image from PUYO_PUYO_TSU____ (Track 1).bin (T-6601G
V1.200, Mode 1/2352). Only the Python 3 standard library is needed."""
import argparse, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import logo, saturn_build, saturn_iso

ORIG_NAME = 'PUYO_PUYO_TSU____ (Track 1).bin'
ORIG_SIZE = 606498480
ORIG_CRC = 0x3f966f9d
OUT_BIN_NAME = 'Puyo Puyo 2 (English) (Track 1).bin'
OUT_CUE_NAME = 'Puyo Puyo 2 (English).cue'


def verify_disc(src_bin):
    size = os.path.getsize(src_bin)
    if size != ORIG_SIZE:
        raise SystemExit(f'unexpected Track 1 size ({size} bytes): need {ORIG_NAME} ({ORIG_SIZE} bytes)')
    with open(src_bin, 'rb') as f:
        f.seek(16)
        ip = f.read(64)
    if ip[0:15] != b'SEGA SEGASATURN' or b'T-6601G' not in ip:
        raise SystemExit(f'{src_bin}: IP.BIN does not match Sega Saturn Puyo Puyo 2 (T-6601G)')


def main():
    p = argparse.ArgumentParser(usage='make_puyopuy2e_saturn.py [--logo MODE] [--fast] [TRACK1_BIN | FOLDER] [OUT_DIR]')
    p.add_argument('--logo', choices=logo.MODES, default=logo.DEFAULT_MODE,
                   help='title logo variant (default: %(default)s)')
    p.add_argument('--fast', action='store_true',
                   help='overlay onto an existing output Track 1 .bin instead of copying 606 MB')
    args, pos = p.parse_known_args()
    bad = [a for a in pos if a.startswith('-')]
    if bad:
        p.error('unrecognized arguments: %s' % ' '.join(bad))
    if len(pos) > 2:
        p.error('unrecognized arguments: %s' % ' '.join(pos[2:]))

    src = pos[0] if pos else os.path.join(HERE, 'saturn')
    if os.path.isdir(src):
        src = os.path.join(src, ORIG_NAME)
    if not os.path.isfile(src):
        raise SystemExit(f'{src} not found: supply {ORIG_NAME}')
    verify_disc(src)

    out_dir = pos[1] if len(pos) > 1 else os.path.join(HERE, 'dist', 'saturn')
    out_bin = os.path.join(out_dir, OUT_BIN_NAME)
    out_cue = os.path.join(out_dir, OUT_CUE_NAME)

    replacements = saturn_build.build(src, logo_mode=args.logo)
    summary = saturn_iso.patch_iso(src, out_bin, replacements, out_cue=out_cue, fresh=not args.fast)
    for name, info in summary.items():
        cap = info['sectors'] * saturn_iso.SECTOR_USER
        print(f'  {name:13s} LBA {info["lba"]:4d}  {info["old_size"]:6d} -> {info["new_size"]:6d} / {cap:6d} B')
    print(f'written {out_cue} (logo={args.logo}, fresh={not args.fast})')


if __name__ == '__main__':
    main()
