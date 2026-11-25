#!/usr/bin/env python3
"""make_ips.py - Generate verified IPS patches for Puyo Puyo 2 (Mega Drive + Sega C2 Arcade).

Only the Python 3 standard library is used. Base ROMs are required locally to compute diffs."""
import argparse, hashlib, os, sys, zipfile, zlib
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'tools'))
sys.path.insert(0, HERE)
import build, ips, logo, make_puyopuy2e, make_puyopuy2e_md, md_build, romset


def _crc32(data):
    return zlib.crc32(data) & 0xffffffff


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _arcade_readme(mode, even_crc, odd_crc):
    (ev_name, ev_crc), (od_name, od_crc) = romset.PROGRAM
    snd_name, snd_crc = romset.SOUND
    return (
        f'Puyo Puyo 2 English (Sega System C2 Arcade) - IPS Patch Set ({mode})\n'
        f'=====================================================================\n\n'
        f'Required input chips (from MAME puyopuy2.zip):\n'
        f'  {ev_name:<15s} 524288 bytes  CRC32 {ev_crc:08x}\n'
        f'  {od_name:<15s} 524288 bytes  CRC32 {od_crc:08x}\n'
        f'  {snd_name:<15s} 524288 bytes  CRC32 {snd_crc:08x}  (unchanged)\n\n'
        f'Quick auto-patch (using the included scripts):\n'
        f'  Windows:        powershell -ExecutionPolicy Bypass -File .\\patch.ps1 puyopuy2.zip puyopuy2e-arcade-{mode}-ips.zip\n'
        f'  Linux / macOS:  ./patch.sh puyopuy2.zip puyopuy2e-arcade-{mode}-ips.zip\n'
        f'  (Add -Mame / --mame to keep epr-* filenames for upstream MAME.)\n\n'
        f'Manual patching (Lunar IPS, Floating IPS / Flips, or RomPatcher.js):\n'
        f'  1. Extract puyopuy2.zip to a temporary folder.\n'
        f'  2. Apply {ev_name}.ips to {ev_name} -> CRC32 {even_crc:08x}\n'
        f'     Apply {od_name}.ips to {od_name} -> CRC32 {odd_crc:08x}\n'
        f'  3. Re-zip with untouched {snd_name}:\n'
        f'     - For mame2003-plus (puyopuy2e): rename the patched files to\n'
        f'       {make_puyopuy2e.OUT_NAMES[0]} and {make_puyopuy2e.OUT_NAMES[1]} and zip as puyopuy2e.zip.\n'
        f'     - For upstream MAME (puyopuy2): keep original epr-* names and zip as puyopuy2.zip.\n'
    )


def build_arcade_ips(src_zip, out_dir, modes):
    """Build and round-trip-verify per-chip arcade IPS zip bundles for each logo mode."""
    orig_prog = romset.read_program(src_zip)
    orig_even, orig_odd = romset.split_program(orig_prog)
    ev_name, od_name = romset.PROGRAM[0][0], romset.PROGRAM[1][0]
    patch_ps1 = Path(HERE, 'tools', 'patch.ps1').read_bytes()
    patch_sh = Path(HERE, 'tools', 'patch.sh').read_bytes().replace(b'\r\n', b'\n')
    artifacts = []
    for mode in modes:
        new_prog = build.build(orig_prog, mode)
        new_even, new_odd = romset.split_program(new_prog)
        want = make_puyopuy2e.EXPECTED[mode]
        got = (_crc32(new_even), _crc32(new_odd))
        assert got == want, f'arcade {mode}: CRC mismatch {got} != {want}'

        p_even = ips.encode(orig_even, new_even)
        p_odd = ips.encode(orig_odd, new_odd)
        assert ips.apply(orig_even, p_even) == new_even, f'arcade {mode}: even IPS verify failed'
        assert ips.apply(orig_odd, p_odd) == new_odd, f'arcade {mode}: odd IPS verify failed'

        zname = f'puyopuy2e-arcade-{mode}-ips.zip'
        zpath = os.path.join(out_dir, zname)
        readme = _arcade_readme(mode, got[0], got[1]).encode('utf-8')
        with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
            for name, payload, mode_bits in (
                (f'{ev_name}.ips', p_even, 0o644),
                (f'{od_name}.ips', p_odd, 0o644),
                ('README.txt', readme, 0o644),
                ('patch.ps1', patch_ps1, 0o644),
                ('patch.sh', patch_sh, 0o755),
            ):
                zi = zipfile.ZipInfo(name, date_time=(2024, 1, 1, 0, 0, 0))
                zi.compress_type = zipfile.ZIP_DEFLATED
                zi.external_attr = (0o100000 | mode_bits) << 16
                z.writestr(zi, payload)
        print(f'verified {zname} (even={len(p_even)}B odd={len(p_odd)}B, CRCs {got[0]:08x}/{got[1]:08x})')
        artifacts.append(zpath)
    return artifacts


def build_md_ips(src_md, out_dir, modes):
    """Build and round-trip-verify Mega Drive IPS patches for each logo mode."""
    orig = Path(src_md).read_bytes()
    if len(orig) != make_puyopuy2e_md.ORIG_SIZE or _crc32(orig) != make_puyopuy2e_md.ORIG_CRC:
        raise SystemExit(
            f'unexpected Mega Drive ROM (got {len(orig)} bytes CRC32 {_crc32(orig):08x}; '
            f'need {make_puyopuy2e_md.ORIG_NAME}: {make_puyopuy2e_md.ORIG_SIZE} bytes CRC32 {make_puyopuy2e_md.ORIG_CRC:08x})'
        )
    artifacts = []
    for mode in modes:
        built = bytes(md_build.build(orig, mode))
        patch = ips.encode(orig, built)
        assert ips.apply(orig, patch) == built, f'MD {mode}: IPS verify failed'
        fname = f'puyopuy2e-md-{mode}.ips'
        fpath = os.path.join(out_dir, fname)
        Path(fpath).write_bytes(patch)
        crc = _crc32(built)
        print(f'verified {fname} ({len(patch)} bytes, patched ROM CRC32 {crc:08x})')
        artifacts.append(fpath)
    return artifacts


def write_checksums(out_dir, paths):
    """Write SHA256SUMS.txt covering all generated patch artifacts."""
    lines = [f'{_sha256(Path(path).read_bytes())}  {os.path.basename(path)}\n' for path in paths]
    spath = os.path.join(out_dir, 'SHA256SUMS.txt')
    Path(spath).write_text(''.join(lines), encoding='utf-8', newline='\n')
    return spath


def main():
    p = argparse.ArgumentParser(description='Generate verified IPS patches for Mega Drive and Arcade.')
    p.add_argument('--out', default=os.path.join(HERE, 'dist'), help='output directory (default: dist)')
    p.add_argument('--logo', choices=logo.MODES, action='append',
                   help=f'logo variant to build (repeatable; default: {logo.DEFAULT_MODE})')
    p.add_argument('--roms-dir', default=None,
                   help='directory holding puyopuy2.zip and Puyo Puyo 2 (Japan) (v1.1).md')
    p.add_argument('--arcade', default=None, help='path to puyopuy2.zip')
    p.add_argument('--no-arcade', action='store_true', help='skip arcade IPS bundles')
    p.add_argument('--md', default=None, help='path to Puyo Puyo 2 (Japan) (v1.1).md')
    p.add_argument('--no-md', action='store_true', help='skip Mega Drive IPS patches')
    args = p.parse_args()

    if args.no_md and args.no_arcade:
        raise SystemExit('nothing to build: both --no-md and --no-arcade set')

    modes = list(dict.fromkeys(args.logo)) if args.logo else [logo.DEFAULT_MODE]
    os.makedirs(args.out, exist_ok=True)
    artifacts = []
    rom_root = args.roms_dir or HERE

    if not args.no_md:
        md_path = args.md or os.path.join(rom_root, make_puyopuy2e_md.ORIG_NAME)
        if not os.path.exists(md_path):
            raise SystemExit(f'{md_path} not found (pass --no-md to skip)')
        artifacts.extend(build_md_ips(md_path, args.out, modes))

    if not args.no_arcade:
        arc_path = args.arcade or os.path.join(rom_root, 'puyopuy2.zip')
        if not os.path.exists(arc_path):
            raise SystemExit(f'{arc_path} not found (pass --no-arcade to skip)')
        artifacts.extend(build_arcade_ips(arc_path, args.out, modes))

    # Copy auto-patcher helper scripts alongside the generated patches
    for script, unix_nl in (('patch.ps1', False), ('patch.sh', True)):
        raw = Path(HERE, 'tools', script).read_bytes()
        if unix_nl:
            raw = raw.replace(b'\r\n', b'\n')
        dst = os.path.join(args.out, script)
        Path(dst).write_bytes(raw)
        artifacts.append(dst)

    sums = write_checksums(args.out, artifacts)
    print(f'wrote {len(artifacts) + 1} files to {args.out}')


if __name__ == '__main__':
    main()
