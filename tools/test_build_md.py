#!/usr/bin/env python3
"""Stdlib-only self-test for the Mega Drive Puyo Puyo 2 English builder (blocks Pillow)."""
import os, struct, sys, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)


class BlockPIL:
    def find_spec(self, fullname, path, target=None):
        if fullname == 'PIL' or fullname.startswith('PIL.'):
            raise ImportError('Pillow blocked: runtime builder must be stdlib-only')


sys.meta_path.insert(0, BlockPIL())
import logo, lz, md_build, make_puyopuy2e_md  # noqa: E402

ROM = os.path.join(ROOT, make_puyopuy2e_md.ORIG_NAME)
if not os.path.exists(ROM):
    raise SystemExit('put %s in the repo root to run this test' % make_puyopuy2e_md.ORIG_NAME)
orig = make_puyopuy2e_md.read_rom(ROM)

EXPECTED = {'original': 0x7ba1b329, 'no-red-puyos': 0x2854fece, 'with-red-puyos': 0x5b68a1cf}
for mode in logo.MODES:
    out = bytes(md_build.build(orig, mode))
    assert len(out) == len(orig)
    hdr_csum = struct.unpack('>H', out[0x18e:0x190])[0]
    calc_csum = sum(struct.unpack('>%dH' % ((len(out) - 0x200) // 2), out[0x200:])) & 0xffff
    assert hdr_csum == calc_csum, '%s: checksum mismatch %04x != %04x' % (mode, hdr_csum, calc_csum)
    nomi_map, _ = lz.decompress(out, 0xa602d)
    nomi_tiles, _ = lz.decompress(out, 0xa5ce6)
    bg_tile = nomi_map[256 + 33]
    assert nomi_tiles[bg_tile * 32:(bg_tile + 1) * 32] == b'\x00' * 32, 'Nomi bg tile non-blank'
    if mode == 'original':
        for tbl in md_build.LOGO_TABLES:
            assert out[tbl:tbl + 194] == orig[tbl:tbl + 194], 'original mode touched logo table'
        assert out[md_build.LOGO_TILES:md_build.LOGO_TILES + 4089] == orig[md_build.LOGO_TILES:md_build.LOGO_TILES + 4089]
    crc = zlib.crc32(out) & 0xffffffff
    assert crc == EXPECTED[mode], '%s: CRC32 %08x != expected %08x' % (mode, crc, EXPECTED[mode])
    print('PASS %-15s CRC32=%08x checksum=%04x' % (mode, crc, hdr_csum))

print('All %d Mega Drive builds passed (stdlib-only).' % len(logo.MODES))
