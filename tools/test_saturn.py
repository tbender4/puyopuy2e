#!/usr/bin/env python3
"""Self-contained stdlib-only tests for Sega Saturn modding helpers (saturn_iso, saturn_arch)."""
import os, stat, struct, sys, tempfile

# Prove pure Python 3 stdlib (no Pillow / external packages)
class _BlockPIL:
    def find_spec(self, name, path=None, target=None):
        if name == 'PIL' or name.startswith('PIL.'):
            raise ImportError('PIL blocked in stdlib-only test')

sys.meta_path.insert(0, _BlockPIL())

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import logo, lz, saturn_arch, saturn_build, saturn_iso

SATURN_BIN = os.path.join(ROOT, 'saturn', 'PUYO_PUYO_TSU____ (Track 1).bin')
MD_ROM = os.path.join(ROOT, 'Puyo Puyo 2 (Japan) (v1.1).md')

BANKS = (
    'DEMO_G00.BIN', 'DEMO_G01.BIN', 'DEMO_G02.BIN', 'DEMO_G03.BIN', 'DEMO_G04.BIN',
    'DEMO_G05.BIN', 'DEMO_G06.BIN', 'GFILE08.BIN', 'GFILE09.BIN',
    'FACE_G00.BIN', 'FACE_G01.BIN', 'FACE_G02.BIN', 'FACE_G03.BIN',
)


def _make_mini_iso(bin_path, cue_path, track2_path, files):
    """Build a valid 32-sector Mode 1/2352 synthetic ISO-9660 disc + Track 2 + .cue."""
    sectors = [bytearray(saturn_iso.SECTOR_USER) for _ in range(32)]
    pvd = sectors[16]
    pvd[0:6] = b'\x01CD001'
    struct.pack_into('<I', pvd, 156 + 2, 20)
    struct.pack_into('<I', pvd, 156 + 10, 2048)

    pos, lba = 0, 22
    root = sectors[20]
    for name, data in files:
        raw_name = (name + ';1').encode('ascii')
        rec_len = 33 + len(raw_name) + ((33 + len(raw_name)) & 1)
        root[pos] = rec_len
        struct.pack_into('<I', root, pos + 2, lba)
        struct.pack_into('>I', root, pos + 6, lba)
        struct.pack_into('<I', root, pos + 10, len(data))
        struct.pack_into('>I', root, pos + 14, len(data))
        root[pos + 25] = 0
        root[pos + 32] = len(raw_name)
        root[pos + 33:pos + 33 + len(raw_name)] = raw_name
        pos += rec_len
        n_sec = (len(data) + saturn_iso.SECTOR_USER - 1) // saturn_iso.SECTOR_USER
        for i in range(n_sec):
            chunk = data[i * saturn_iso.SECTOR_USER:(i + 1) * saturn_iso.SECTOR_USER]
            sectors[lba + i][:len(chunk)] = chunk
        lba += n_sec

    with open(bin_path, 'wb') as f:
        for s_lba, user in enumerate(sectors):
            f.write(saturn_iso.encode_mode1_sector(s_lba, bytes(user)))
    with open(track2_path, 'wb') as f:
        f.write(b'\x00' * (saturn_iso.SECTOR_RAW * 2))
    with open(cue_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('REM comment mentioning FILE "ignored.bin" BINARY\n')
        f.write(f'FILE "{os.path.basename(bin_path)}" BINARY\n  TRACK 01 MODE1/2352\n    INDEX 01 00:00:00\n')
        f.write(f'FILE "{os.path.basename(track2_path)}" BINARY\n  TRACK 02 AUDIO\n    INDEX 01 00:00:00\n')


def test_mode1_and_iso_patcher():
    sec = saturn_iso.encode_mode1_sector(1234, bytes(range(256)) * 8)
    assert len(sec) == 2352
    assert saturn_iso.verify_mode1_sector(1234, sec)
    assert not saturn_iso.verify_mode1_sector(1235, sec)
    bad = bytearray(sec)
    bad[100] ^= 1
    assert not saturn_iso.verify_mode1_sector(1234, bytes(bad))

    with tempfile.TemporaryDirectory() as td:
        src_dir = os.path.join(td, 'src')
        out_dir = os.path.join(td, 'out')
        os.makedirs(src_dir)
        src_bin = os.path.join(src_dir, 'DISC (Track 1).bin')
        src_cue = os.path.join(src_dir, 'DISC.cue')
        src_t2 = os.path.join(src_dir, 'DISC (Track 2).bin')
        _make_mini_iso(src_bin, src_cue, src_t2, [
            ('A.BIN', b'A' * 5000),  # 3 sectors (6144 B cap)
            ('B.BIN', b'B' * 3000),  # 2 sectors (4096 B cap)
        ])
        # Mark source .bin read-only (common for Redump archival dumps)
        os.chmod(src_bin, stat.S_IREAD)
        try:
            out_bin = os.path.join(out_dir, 'MOD (Track 1).bin')
            out_cue = os.path.join(out_dir, 'MOD.cue')

            # 1. Fresh build from read-only source, shrinking A.BIN 3 -> 1 sector + .cue & Track 2
            saturn_iso.patch_iso(src_bin, out_bin, {'a.bin;1': b'X' * 1000}, out_cue=out_cue)
            assert os.path.isfile(os.path.join(out_dir, 'DISC (Track 2).bin'))
            with open(out_cue, encoding='utf-8') as cf:
                cue_out = cf.read()
            assert 'REM comment mentioning FILE "ignored.bin" BINARY' in cue_out
            assert 'FILE "MOD (Track 1).bin" BINARY' in cue_out
            with open(out_bin, 'rb') as f:
                ents = saturn_iso.parse_iso(f)
                assert saturn_iso.read_iso_file(f, 'A.BIN', ents) == b'X' * 1000
                assert saturn_iso.read_iso_file(f, 'B.BIN', ents) == b'B' * 3000
                for lba in (20, 22, 23, 24):
                    f.seek(lba * 2352)
                    raw = f.read(2352)
                    assert saturn_iso.verify_mode1_sector(lba, raw)
                    if lba in (23, 24):
                        assert raw[16:2064] == b'\x00' * 2048

            # 2. Incremental overlay (fresh=False) preserves A.BIN while patching B.BIN + supports empty file
            saturn_iso.patch_iso(src_bin, out_bin, {'B.BIN': b''}, fresh=False)
            with open(out_bin, 'rb') as f:
                ents = saturn_iso.parse_iso(f)
                assert saturn_iso.read_iso_file(f, 'A.BIN', ents) == b'X' * 1000
                assert saturn_iso.read_iso_file(f, 'B.BIN', ents) == b''

            # 3. Incremental overlay can grow A.BIN back up to src_bin's original 3-sector cap (6144 B)
            saturn_iso.patch_iso(src_bin, out_bin, {'A.BIN': b'Z' * 6000}, fresh=False)
            with open(out_bin, 'rb') as f:
                assert saturn_iso.read_iso_file(f, 'A.BIN') == b'Z' * 6000

            # 4. Default fresh=True resets omitted B.BIN cleanly back to vanilla
            saturn_iso.patch_iso(src_bin, out_bin, {'A.BIN': b'Q' * 500})
            with open(out_bin, 'rb') as f:
                ents = saturn_iso.parse_iso(f)
                assert saturn_iso.read_iso_file(f, 'A.BIN', ents) == b'Q' * 500
                assert saturn_iso.read_iso_file(f, 'B.BIN', ents) == b'B' * 3000

            # 5. Guardrails: overflow, overwrite src bin (incl. different casing), overwrite src cue (no orphan bin), bad cue dir
            orphan = os.path.join(src_dir, 'ORPHAN.bin')
            alt_case_src = os.path.join(src_dir, 'disc (track 1).bin')
            checks = [
                lambda: saturn_iso.patch_iso(src_bin, out_bin, {'B.BIN': b'0' * 4097}),
                lambda: saturn_iso.patch_iso(src_bin, src_bin, {'A.BIN': b'1'}),
                lambda: saturn_iso.patch_iso(src_bin, orphan, {'A.BIN': b'1'}, out_cue=src_cue),
                lambda: saturn_iso.patch_iso(src_bin, out_bin, {'A.BIN': b'1'}, out_cue=os.path.join(td, 'bad.cue')),
            ]
            if os.name == 'nt':
                checks.append(lambda: saturn_iso.patch_iso(src_bin, alt_case_src, {'A.BIN': b'1'}, fresh=False))
            for fn in checks:
                try:
                    fn()
                except ValueError:
                    pass
                else:
                    raise AssertionError('expected ValueError guardrail')
            assert not os.path.exists(orphan), 'failed out_cue check should not leave orphan out_bin'
        finally:
            os.chmod(src_bin, stat.S_IWRITE | stat.S_IREAD)
    print('PASS Mode 1/2352 codec + ISO-9660 patcher (fresh, incremental, shrink, read-only, cue, guardrails)')


def test_lzss_arch_and_vdp1_units():
    # Edge cases: empty, 1-3 bytes, RLE overlap (dist=1), max match (66 B), ring wrap (>1024 B), bytearray input
    cases = [
        b'',
        b'A',
        b'AB',
        b'ABC',
        bytearray(b'XYZXYZXYZ123456'),
        b'A' * 200,
        b'ABCD' * 400,
        bytes((i * 37) & 0xFF for i in range(2500)) + b'\x00' * 130 + b'PUYO' * 40,
    ]
    for c in cases:
        comp = saturn_arch.bits_compress(c)
        dec, end = saturn_arch.bits_decompress(comp, 0)
        assert dec == bytes(c) and end == len(comp), f'LZSS round-trip failed for len={len(c)}'

    # Synthetic H_PUYODT archive: unpack -> untouched repack -> edit chunk -> 64 KB overflow check
    c0, c1 = saturn_arch.bits_compress(b'HELLO' * 10), saturn_arch.bits_compress(b'WORLD' * 8)
    hp_buf = bytearray(8)
    o0 = len(hp_buf); hp_buf.extend(c0); hp_buf.extend(b'\x00' * ((-len(hp_buf)) & 3))
    o1 = len(hp_buf); hp_buf.extend(c1); hp_buf.extend(b'\x00' * ((-len(hp_buf)) & 3))
    struct.pack_into('>II', hp_buf, 0, o0, o1)
    hp = saturn_arch.unpack_hpuyodt(bytes(hp_buf))
    assert saturn_arch.pack_hpuyodt(hp) == bytes(hp_buf)
    hp['chunks'][1] = bytearray(b'ENGLISH!' * 6)
    hp_mod = saturn_arch.unpack_hpuyodt(saturn_arch.pack_hpuyodt(hp))
    assert bytes(hp_mod['chunks'][0]) == b'HELLO' * 10 and bytes(hp_mod['chunks'][1]) == b'ENGLISH!' * 6
    try:
        hp['chunks'][0] = bytearray(os.urandom(70000))
        saturn_arch.pack_hpuyodt(hp)
    except ValueError:
        pass
    else:
        raise AssertionError('expected 64 KB overflow ValueError for H_PUYODT')

    # Synthetic .BIN bank: leading zero slot, shared descriptor list, LZSS chunks, 4-byte-aligned raw entry
    lz0 = saturn_arch.bits_compress(b'TILE' * 16)
    lz1 = saturn_arch.bits_compress(b'MAP!' * 20)
    raw_font = bytes(range(64))
    # Table (4 slots = 8 B): [0]=0, [1]=desc0, [2]=desc0 (shared), [3]=raw_font
    # desc0 at 8: (0xC000, 0x0100, lz0_off), (0xC000, 0x0200, lz1_off), 0xFFFF -> 14 B (ends at 22)
    b_buf = bytearray(22)
    lz0_off = len(b_buf); b_buf.extend(lz0)
    b_buf.extend(b'\x00' * ((-len(b_buf)) & 3))
    raw_off = len(b_buf); b_buf.extend(raw_font)
    lz1_off = len(b_buf); b_buf.extend(lz1)
    struct.pack_into('>4H', b_buf, 0, 0, 8, 8, raw_off)
    struct.pack_into('>HHHHHHH', b_buf, 8, 0xC000, 0x0100, lz0_off, 0xC000, 0x0200, lz1_off, 0xFFFF)
    bank = saturn_arch.unpack_bank(bytes(b_buf))
    assert bank['table'] == [None, ('desc', 0), ('desc', 0), ('raw', 0)]
    assert saturn_arch.pack_bank(bank) == bytes(b_buf)
    bank['chunks'][0] = bytearray(b'NEW!' * 16)
    bank['raw'][0] = bytearray(b'\xAA' * 32)
    repacked = saturn_arch.pack_bank(bank)
    assert struct.unpack_from('>H', repacked, 6)[0] % 4 == 0
    bank2 = saturn_arch.unpack_bank(repacked)
    assert bytes(bank2['chunks'][0]) == b'NEW!' * 16 and bytes(bank2['raw'][0]) == b'\xAA' * 32
    try:
        bank['raw'][0] = bytearray(70000)
        saturn_arch.pack_bank(bank)
    except ValueError:
        pass
    else:
        raise AssertionError('expected 64 KB overflow ValueError for bank')

    # Synthetic VDP1 <-> MD tiles round-trip across mixed sprite sizes
    specs = [(4, 4), (3, 2), (1, 1), (2, 3)]
    raw_tiles = bytes((i * 19 + 7) & 0xFF for i in range(sum(w * h * 32 for w, h in specs)))
    vdp1 = saturn_arch.tiles_to_sprites(raw_tiles, specs)
    back = saturn_arch.sprites_to_tiles(vdp1, specs)
    assert bytes(back) == raw_tiles
    print('PASS Bits Lab 10/6 LZSS + H_PUYODT/.BIN archive + per-sprite VDP1 unit tests')


def test_real_disc():
    if not os.path.isfile(SATURN_BIN):
        print('SKIP real Saturn disc tests (Track 1 .bin not found)')
        return
    with open(SATURN_BIN, 'rb') as f:
        for lba in (0, 15, 16, 20, 21, 25, 2167, 257864):
            f.seek(lba * saturn_iso.SECTOR_RAW)
            assert saturn_iso.verify_mode1_sector(lba, f.read(saturn_iso.SECTOR_RAW)), f'LBA {lba} mismatch'

        entries = saturn_iso.parse_iso(f)
        assert len(entries) == 210

        hp_raw = saturn_iso.read_iso_file(f, 'H_PUYODT.BIN', entries)
        hp = saturn_arch.unpack_hpuyodt(hp_raw)
        assert len(hp['chunks']) == 80
        assert saturn_arch.pack_hpuyodt(hp) == hp_raw
        hp_re = saturn_arch.pack_hpuyodt(dict(hp, _orig_uncomp=[None] * len(hp['chunks'])))
        assert len(hp_re) <= entries['H_PUYODT.BIN']['sectors'] * saturn_iso.SECTOR_USER
        assert saturn_arch.unpack_hpuyodt(hp_re)['chunks'] == hp['chunks']

        gfile08 = gfile09 = None
        for name in BANKS:
            raw = saturn_iso.read_iso_file(f, name, entries)
            b = saturn_arch.unpack_bank(raw)
            assert saturn_arch.pack_bank(b) == raw, f'{name} untouched repack not bit-for-bit identical'
            b_re = saturn_arch.pack_bank(dict(b, _orig_uncomp=[None] * len(b['chunks'])))
            sec_cap = entries[name]['sectors'] * saturn_iso.SECTOR_USER
            assert len(b_re) <= saturn_arch.LOW_WRAM_SLOT and len(b_re) <= sec_cap, (
                f'{name} repacked {len(b_re)} B exceeds cap {sec_cap} B'
            )
            b2 = saturn_arch.unpack_bank(b_re)
            assert b2['chunks'] == b['chunks'] and b2['raw'] == b['raw']
            if name == 'DEMO_G03.BIN':
                assert [i for i, r in enumerate(b['table']) if r is None] == [0, 1, 10, 11]
            if name == 'GFILE08.BIN':
                gfile08 = b
            if name == 'GFILE09.BIN':
                gfile09 = b
                assert b['table'][7] == ('raw', 0) and len(b['raw'][0]) == 8224
                font_off = struct.unpack_from('>H', b_re, 7 * 2)[0]
                assert font_off % 4 == 0, f'GFILE09[7] font offset {font_off:#x} not 4-byte aligned'
    print('PASS real disc Mode 1/2352 + all 14 .BIN archives bit-for-bit & forced-recompress round-trip')

    if os.path.isfile(MD_ROM):
        with open(MD_ROM, 'rb') as mf:
            md = mf.read()
        md_ko, _ = lz.decompress(md, 0x086A7F)
        sat_ko = bytes(gfile08['chunks'][14])
        assert saturn_arch.tiles_to_sprites(md_ko, saturn_build.KO_BIG_SPECS) == sat_ko
        assert bytes(saturn_arch.sprites_to_tiles(sat_ko, saturn_build.KO_BIG_SPECS)) == md_ko
        assert bytes(gfile09['raw'][0]) == md[0x093D60:0x093D60 + 8224]
        print('PASS real MD v1.1 <-> Saturn VDP1 sprite proof (KO Big) + 1bpp font identity')
    else:
        print('SKIP MD <-> Saturn proof (MD v1.1 ROM not found)')

    # 5. Milestone A build verification across all 3 logo modes (caps, logo invariants, blank tiles)
    with open(SATURN_BIN, 'rb') as f:
        orig_0 = saturn_iso.read_iso_file(f, '0', entries)
        orig_g04 = saturn_iso.read_iso_file(f, 'DEMO_G04.BIN', entries)
        orig_logo = bytes(saturn_arch.unpack_bank(orig_g04)['chunks'][7])
    groups0 = logo.read_groups(orig_0, saturn_build.LOGO_TABLES[0])
    for mode in logo.MODES:
        repl = saturn_build.build(SATURN_BIN, logo_mode=mode)
        assert len(repl['0']) == entries['0']['size']
        assert repl['0'][0x6d3a6:0x6d3b0] == b'RULE SET  '
        assert repl['0'][0x6d294:0x6d29e] == b'COCKATRICE'
        unpacked = {}
        for name, data in repl.items():
            cap = entries[name]['sectors'] * saturn_iso.SECTOR_USER
            assert len(data) <= cap, f'{mode} {name}: {len(data)} B exceeds ISO cap {cap} B'
            if name != '0':
                assert len(data) <= saturn_arch.LOW_WRAM_SLOT
                unpacked[name] = saturn_arch.unpack_bank(data)
        # Verify blank tiles stay all-zero after replace_blocks
        assert not any(unpacked['DEMO_G06.BIN']['chunks'][13][0x04 * 32:0x05 * 32])
        assert not any(unpacked['DEMO_G03.BIN']['chunks'][17][0x9c * 32:0x9d * 32])
        assert not any(unpacked['GFILE09.BIN']['chunks'][4][0x08 * 32:0x09 * 32])
        # Verify per-mode logo invariants on DEMO_G04[7] and LOGO_TABLES
        logo_chunk = bytes(unpacked['DEMO_G04.BIN']['chunks'][7])
        g0_cnt = struct.unpack_from('>H', repl['0'], groups0[0][0])[0]
        if mode == 'original':
            assert repl['DEMO_G04.BIN'] == orig_g04 and g0_cnt == 4
        elif mode == 'no-red-puyos':
            assert logo_chunk[:0x8a0] != orig_logo[:0x8a0] and logo_chunk[0x8a0:] == orig_logo[0x8a0:]
            assert g0_cnt == 3
            for g in logo.RED_X:
                assert struct.unpack_from('>h', repl['0'], groups0[g][0] + 2)[0] == logo.OFFSCREEN_Y
        else:
            assert logo_chunk[:0x8a0] != orig_logo[:0x8a0] and logo_chunk[0x8a0:0xc00] != orig_logo[0x8a0:0xc00]
            assert logo_chunk[0xc00:] == orig_logo[0xc00:]
            for g in logo.RED_X:
                at = groups0[g][0]
                assert struct.unpack_from('>hB', repl['0'], at + 2) == (logo.RED_Y, (2 << 2) | 1)
    print('PASS Milestone A Saturn build (3/3 logo modes, invariants, blank tiles, RAM + ISO caps)')


if __name__ == '__main__':
    test_mode1_and_iso_patcher()
    test_lzss_arch_and_vdp1_units()
    test_real_disc()
    print('All Saturn building-block tests passed (stdlib-only).')
