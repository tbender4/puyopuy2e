#!/usr/bin/env python3
"""make_ips.py - Generate verified patches for Puyo Puyo 2: IPS (Mega Drive, Sega C2 Arcade), BPS (Saturn).

Only the Python 3 standard library is used. Base ROMs are required locally to compute diffs."""
import argparse, hashlib, mmap, os, sys, tempfile, zipfile, zlib
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'tools'))
sys.path.insert(0, HERE)
import bps, build, ips, logo, make_puyopuy2e, make_puyopuy2e_md, make_puyopuy2e_saturn, md_build, romset
import saturn_build, saturn_iso


def _script(name):
    """a tools/ patcher script as shipped (patch.sh with LF line ends)"""
    raw = Path(HERE, 'tools', name).read_bytes()
    return raw.replace(b'\r\n', b'\n') if name.endswith('.sh') else raw


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
        f'  (Add -Mame / --mame to keep epr-* filenames for upstream MAME; this writes\n'
        f'   puyopuy2-en.zip, which you rename to puyopuy2.zip in a separate ROM folder.)\n\n'
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
    artifacts = []
    for mode in modes:
        new_prog = build.build(orig_prog, mode)
        new_even, new_odd = romset.split_program(new_prog)
        want = make_puyopuy2e.EXPECTED[mode]
        got = (zlib.crc32(new_even), zlib.crc32(new_odd))
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
                ('patch.ps1', _script('patch.ps1'), 0o644),
                ('patch.sh', _script('patch.sh'), 0o755),
            ):
                zi = zipfile.ZipInfo(name, date_time=(2024, 1, 1, 0, 0, 0))
                zi.compress_type = zipfile.ZIP_DEFLATED
                zi.create_system = 3  # Unix, so unzip keeps patch.sh executable even when built on Windows
                zi.external_attr = (0o100000 | mode_bits) << 16
                z.writestr(zi, payload)
        print(f'verified {zname} (even={len(p_even)}B odd={len(p_odd)}B, CRCs {got[0]:08x}/{got[1]:08x})')
        artifacts.append(zpath)
    return artifacts


def build_md_ips(src_md, out_dir, modes):
    """Build and round-trip-verify Mega Drive IPS patches for each logo mode."""
    orig = make_puyopuy2e_md.read_rom(src_md)
    artifacts = []
    for mode in modes:
        built = bytes(md_build.build(orig, mode))
        patch = ips.encode(orig, built)
        assert ips.apply(orig, patch) == built, f'MD {mode}: IPS verify failed'
        fname = f'puyopuy2e-md-{mode}.ips'
        fpath = os.path.join(out_dir, fname)
        Path(fpath).write_bytes(patch)
        crc = zlib.crc32(built)
        print(f'verified {fname} ({len(patch)} bytes, patched ROM CRC32 {crc:08x})')
        artifacts.append(fpath)
    return artifacts


def build_saturn_bps(src_bin, out_dir, modes):
    """Build and round-trip-verify Saturn Track 1 BPS patches for each logo mode (IPS stops at 16 MB)."""
    make_puyopuy2e_saturn.verify_disc(src_bin)
    artifacts = []
    with tempfile.TemporaryDirectory(prefix='pp2e_bps_') as td, open(src_bin, 'rb') as sf, \
            mmap.mmap(sf.fileno(), 0, access=mmap.ACCESS_READ) as src:
        built_bin = os.path.join(td, 'track1.bin')
        for mode in modes:
            saturn_iso.patch_iso(src_bin, built_bin, saturn_build.build(src_bin, logo_mode=mode))
            with open(built_bin, 'rb') as bf, mmap.mmap(bf.fileno(), 0, access=mmap.ACCESS_READ) as dst:
                patch = bps.encode(src, dst)
            _, _, src_crc, crc = bps.header(patch)
            if src_crc != make_puyopuy2e_saturn.ORIG_CRC:   # the CRC the release notes and patch.sh require
                raise SystemExit(f'{src_bin}: not the expected Track 1 (CRC32 {src_crc:08x}, '
                                 f'need {make_puyopuy2e_saturn.ORIG_CRC:08x})')
            with open(os.path.join(td, 'check.bin'), 'w+b') as cf:
                bps.apply(src, patch, cf)   # raises unless the result matches the target CRC32
            fname = f'puyopuy2e-saturn-{mode}.bps'
            fpath = os.path.join(out_dir, fname)
            Path(fpath).write_bytes(patch)
            print(f'verified {fname} ({len(patch)} bytes, patched Track 1 CRC32 {crc:08x})')
            artifacts.append(fpath)
    return artifacts


def write_checksums(out_dir, paths):
    """Write SHA256SUMS.txt covering all generated patch artifacts."""
    lines = [f'{hashlib.sha256(Path(path).read_bytes()).hexdigest()}  {os.path.basename(path)}\n' for path in paths]
    spath = os.path.join(out_dir, 'SHA256SUMS.txt')
    Path(spath).write_text(''.join(lines), encoding='utf-8', newline='\n')
    return spath


def main():
    p = argparse.ArgumentParser(description='Generate verified patches for Mega Drive, Arcade and Saturn.')
    p.add_argument('--out', default=os.path.join(HERE, 'dist'), help='output directory (default: dist)')
    p.add_argument('--logo', choices=logo.MODES, action='append',
                   help=f'logo variant to build (repeatable; default: {logo.DEFAULT_MODE})')
    p.add_argument('--roms-dir', default=None,
                   help='directory holding puyopuy2.zip, Puyo Puyo 2 (Japan) (v1.1).md and saturn/')
    p.add_argument('--arcade', default=None, help='path to puyopuy2.zip')
    p.add_argument('--no-arcade', action='store_true', help='skip arcade IPS bundles')
    p.add_argument('--md', default=None, help='path to Puyo Puyo 2 (Japan) (v1.1).md')
    p.add_argument('--no-md', action='store_true', help='skip Mega Drive IPS patches')
    p.add_argument('--saturn', default=None, help=f'path to {make_puyopuy2e_saturn.ORIG_NAME}')
    p.add_argument('--no-saturn', action='store_true', help='skip Saturn BPS patches')
    args = p.parse_args()

    if args.no_md and args.no_arcade and args.no_saturn:
        raise SystemExit('nothing to build: --no-md, --no-arcade and --no-saturn all set')

    modes = list(dict.fromkeys(args.logo)) if args.logo else [logo.DEFAULT_MODE]
    os.makedirs(args.out, exist_ok=True)
    artifacts = []
    rom_root = args.roms_dir or HERE

    # check every input before building anything, so a missing one leaves no half-written dist
    jobs = [
        (args.no_md, args.md or os.path.join(rom_root, make_puyopuy2e_md.ORIG_NAME), '--no-md', build_md_ips),
        (args.no_arcade, args.arcade or os.path.join(rom_root, 'puyopuy2.zip'), '--no-arcade', build_arcade_ips),
        (args.no_saturn, args.saturn or os.path.join(rom_root, 'saturn', make_puyopuy2e_saturn.ORIG_NAME),
         '--no-saturn', build_saturn_bps),
    ]
    jobs = [job[1:] for job in jobs if not job[0]]
    for path, flag, _ in jobs:
        if not os.path.exists(path):
            raise SystemExit(f'{path} not found (pass {flag} to skip)')
    for path, _, fn in jobs:
        artifacts.extend(fn(path, args.out, modes))

    # Copy auto-patcher helper scripts alongside the generated patches
    for script in ('patch.ps1', 'patch.sh'):
        dst = os.path.join(args.out, script)
        Path(dst).write_bytes(_script(script))
        artifacts.append(dst)

    write_checksums(args.out, artifacts)
    print(f'wrote {len(artifacts) + 1} files to {args.out}')


if __name__ == '__main__':
    main()
