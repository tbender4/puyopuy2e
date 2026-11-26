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
import game_arts, gfx, logo, lz, saturn_arch, saturn_build, saturn_credits, saturn_iso, saturn_ui

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
            #    (a shrunk file keeps its original recorded size, zero-padded)
            saturn_iso.patch_iso(src_bin, out_bin, {'a.bin;1': b'X' * 1000}, out_cue=out_cue)
            assert os.path.isfile(os.path.join(out_dir, 'DISC (Track 2).bin'))
            with open(out_cue, encoding='utf-8') as cf:
                cue_out = cf.read()
            assert 'REM comment mentioning FILE "ignored.bin" BINARY' in cue_out
            assert 'FILE "MOD (Track 1).bin" BINARY' in cue_out
            with open(out_bin, 'rb') as f:
                ents = saturn_iso.parse_iso(f)
                assert saturn_iso.read_iso_file(f, 'A.BIN', ents) == b'X' * 1000 + bytes(4000)
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
                assert saturn_iso.read_iso_file(f, 'A.BIN', ents) == b'X' * 1000 + bytes(4000)
                assert saturn_iso.read_iso_file(f, 'B.BIN', ents) == bytes(3000)

            # 3. Incremental overlay can grow A.BIN back up to src_bin's original 3-sector cap (6144 B)
            saturn_iso.patch_iso(src_bin, out_bin, {'A.BIN': b'Z' * 6000}, fresh=False)
            with open(out_bin, 'rb') as f:
                assert saturn_iso.read_iso_file(f, 'A.BIN') == b'Z' * 6000

            # 4. Default fresh=True resets omitted B.BIN cleanly back to vanilla
            saturn_iso.patch_iso(src_bin, out_bin, {'A.BIN': b'Q' * 500})
            with open(out_bin, 'rb') as f:
                ents = saturn_iso.parse_iso(f)
                assert saturn_iso.read_iso_file(f, 'A.BIN', ents) == b'Q' * 500 + bytes(4500)
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


def _sim_sh2_text_put(code_bytes, base_pc, mem, r4_task, r5_code):
    """Minimal exact SH-2 interpreter for the opcodes emitted by saturn_build.assemble_text_put."""
    def u8(a): return mem.get(a, 0)
    def s8(v): return v - 256 if v >= 128 else v
    def s16(v): return v - 65536 if v >= 32768 else v
    def r16(a):
        assert a % 2 == 0, f'unaligned 16-bit read @ {a:#x}'
        return (u8(a) << 8) | u8(a + 1)
    def r32(a):
        assert a % 4 == 0, f'unaligned 32-bit read @ {a:#x}'
        return (r16(a) << 16) | r16(a + 2)
    def w16(a, v):
        assert a % 2 == 0, f'unaligned 16-bit write @ {a:#x}'
        mem[a], mem[a + 1] = (v >> 8) & 0xFF, v & 0xFF
    def w32(a, v):
        assert a % 4 == 0, f'unaligned 32-bit write @ {a:#x}'
        w16(a, (v >> 16) & 0xFFFF); w16(a + 2, v & 0xFFFF)

    for i, b in enumerate(code_bytes):
        mem[base_pc + i] = b
    regs = [0xDEAD0000 + i for i in range(16)]
    regs[4], regs[5] = r4_task, r5_code
    sentinel_pr = 0x06011794
    pr = sentinel_pr
    saved_callee = regs[8:]
    t_bit = 0
    pc = base_pc

    def step(cur_pc):
        nonlocal t_bit
        op = r16(cur_pc)
        hi = (op >> 12) & 0xF
        n = (op >> 8) & 0xF
        m = (op >> 4) & 0xF
        lo = op & 0xF
        nxt = cur_pc + 2
        delay_target = None
        if op == 0x000B:  # rts
            delay_target = pr
        elif hi == 0xE:  # mov #imm, Rn
            regs[n] = s8(op & 0xFF) & 0xFFFFFFFF
        elif hi == 0x7:  # add #imm, Rn
            regs[n] = (regs[n] + s8(op & 0xFF)) & 0xFFFFFFFF
        elif hi == 0x9:  # mov.w @(disp, PC), Rn
            regs[n] = s16(r16(cur_pc + 4 + (op & 0xFF) * 2)) & 0xFFFFFFFF
        elif hi == 0xD:  # mov.l @(disp, PC), Rn
            regs[n] = r32(((cur_pc + 4) & ~3) + (op & 0xFF) * 4)
        elif hi == 0xA:  # bra disp
            d = op & 0xFFF
            if d >= 0x800: d -= 0x1000
            delay_target = cur_pc + 4 + d * 2
        elif (op & 0xFF00) == 0x8500:  # mov.w @(disp, Rm), R0
            regs[0] = s16(r16((regs[m] + lo * 2) & 0xFFFFFFFF)) & 0xFFFFFFFF
        elif (op & 0xFF00) == 0x8100:  # mov.w R0, @(disp, Rn)
            w16((regs[m] + lo * 2) & 0xFFFFFFFF, regs[0])
        elif (op & 0xFF00) == 0x8900:  # bt
            if t_bit: nxt = cur_pc + 4 + s8(op & 0xFF) * 2
        elif (op & 0xFF00) == 0x8B00:  # bf
            if not t_bit: nxt = cur_pc + 4 + s8(op & 0xFF) * 2
        elif (op & 0xFF00) == 0x8D00:  # bt/s
            if t_bit: delay_target = cur_pc + 4 + s8(op & 0xFF) * 2
        elif (op & 0xFF00) == 0x8F00:  # bf/s
            if not t_bit: delay_target = cur_pc + 4 + s8(op & 0xFF) * 2
        elif (op & 0xFF00) == 0xC900:  # and #imm, R0
            regs[0] &= (op & 0xFF)
        elif hi == 0x6 and lo == 0x0:  # mov.b @Rm, Rn
            regs[n] = s8(u8(regs[m])) & 0xFFFFFFFF
        elif hi == 0x6 and lo == 0x3:  # mov Rm, Rn
            regs[n] = regs[m]
        elif hi == 0x6 and lo == 0x4:  # mov.b @Rm+, Rn
            regs[n] = s8(u8(regs[m])) & 0xFFFFFFFF
            if n != m: regs[m] = (regs[m] + 1) & 0xFFFFFFFF
        elif hi == 0x6 and lo == 0xC:  # extu.b Rm, Rn
            regs[n] = regs[m] & 0xFF
        elif hi == 0x6 and lo == 0xD:  # extu.w Rm, Rn
            regs[n] = regs[m] & 0xFFFF
        elif hi == 0x3 and lo == 0x0:  # cmp/eq Rm, Rn
            t_bit = 1 if regs[n] == regs[m] else 0
        elif hi == 0x3 and lo == 0x2:  # cmp/hs Rm, Rn
            t_bit = 1 if (regs[n] & 0xFFFFFFFF) >= (regs[m] & 0xFFFFFFFF) else 0
        elif hi == 0x3 and lo == 0xC:  # add Rm, Rn
            regs[n] = (regs[n] + regs[m]) & 0xFFFFFFFF
        elif hi == 0x2 and lo == 0x1:  # mov.w Rm, @Rn
            w16(regs[n], regs[m])
        elif hi == 0x2 and lo == 0x2:  # mov.l Rm, @Rn
            w32(regs[n], regs[m])
        elif hi == 0x2 and lo == 0x8:  # tst Rm, Rn
            t_bit = 1 if (regs[n] & regs[m]) == 0 else 0
        elif hi == 0x2 and lo == 0x9:  # and Rm, Rn
            regs[n] &= regs[m]
        elif hi == 0x0 and lo == 0x5:  # mov.w Rm, @(r0, Rn)
            w16((regs[0] + regs[n]) & 0xFFFFFFFF, regs[m])
        elif hi == 0x0 and lo == 0xD:  # mov.w @(r0, Rm), Rn
            regs[n] = s16(r16((regs[0] + regs[m]) & 0xFFFFFFFF)) & 0xFFFFFFFF
        elif hi == 0x0 and lo == 0xE:  # mov.l @(r0, Rm), Rn
            regs[n] = r32((regs[0] + regs[m]) & 0xFFFFFFFF)
        elif hi == 0x4 and (op & 0xFF) == 0x00:  # shll Rn
            t_bit = (regs[n] >> 31) & 1; regs[n] = (regs[n] << 1) & 0xFFFFFFFF
        elif hi == 0x4 and (op & 0xFF) == 0x08:  # shll2 Rn
            regs[n] = (regs[n] << 2) & 0xFFFFFFFF
        elif hi == 0x4 and (op & 0xFF) == 0x09:  # shlr2 Rn
            regs[n] = (regs[n] >> 2) & 0xFFFFFFFF
        elif hi == 0x4 and (op & 0xFF) == 0x19:  # shlr8 Rn
            regs[n] = (regs[n] >> 8) & 0xFFFFFFFF
        elif hi == 0x4 and (op & 0xFF) == 0x10:  # dt Rn
            regs[n] = (regs[n] - 1) & 0xFFFFFFFF; t_bit = 1 if regs[n] == 0 else 0
        else:
            raise AssertionError(f'unexpected SH-2 opcode {op:#06x} @ {cur_pc:#x}')
        return nxt, delay_target

    for _ in range(2000):
        nxt, dtgt = step(pc)
        if dtgt is not None:
            step(pc + 2)  # execute delay slot
            pc = dtgt
            if pc == sentinel_pr:
                assert regs[8:] == saved_callee and pr == sentinel_pr
                return
        else:
            pc = nxt
    raise AssertionError('SH-2 simulation did not return')


def test_sh2_text_put_sim():
    code = saturn_build.assemble_text_put()
    assert len(code) <= saturn_build.TEXT_PUT_END - saturn_build.TEXT_PUT
    mem = {}
    # Populate LUT at 0x0607726C (1bpp nibble -> 4bpp 0xF/0x0 u16)
    for nib in range(16):
        w = sum((0xF << (4 * (3 - b))) for b in range(4) if (nib >> (3 - b)) & 1)
        mem[0x0607726C + nib * 2], mem[0x0607726C + nib * 2 + 1] = w >> 8, w & 0xFF
    # Populate mock font at 0x00293000 with distinct patterns for 'A' (0x41) and 'B' (0x42)
    font_base = 0x00293000
    glyph_a = bytes([0x81, 0x42, 0x24, 0x18] * 4)
    glyph_b = bytes([0xFF, 0x00] * 8)
    for i, b in enumerate(glyph_a): mem[font_base + 0x41 * 16 + i] = b
    for i, b in enumerate(glyph_b): mem[font_base + 0x42 * 16 + i] = b
    # Init mock task struct at 0x06090000: cursor=(X=21,Y=6)=0x1506, count=0, font_base, tile_base=0x8780
    task = 0x06090000
    for off, fmt, val in ((0x18, '>H', 0x1506), (0x50, '>H', 0), (0x64, '>I', font_base), (0x6A, '>H', 0x8780)):
        for i, b in enumerate(struct.pack(fmt, val)): mem[task + off + i] = b

    def rd32(a): return struct.unpack('>I', bytes(mem.get(a + i, 0) for i in range(4)))[0]
    def rd16(a): return (mem.get(a, 0) << 8) | mem.get(a + 1, 0)
    nt = lambda x, y: 0x25E10000 + (((y << 6) + x) << 2)

    # 1. Draw 'A' at (21, 6): cache miss -> tiles 0x8780/0x8781, count -> 2, cursor -> (22, 6)
    _sim_sh2_text_put(code, saturn_build.RAM_BASE + saturn_build.TEXT_PUT, mem, task, ord('A'))
    assert rd16(task + 0x50) == 2 and rd16(task + 0x18) == 0x1606 and rd16(0x0608D774) == ord('A')
    assert rd32(nt(21, 6)) == 0x8780 and rd32(nt(21, 7)) == 0x8781
    assert rd32(0x25E0F000) == 0xF000000F and rd32(0x25E0F004) == 0x0F0000F0  # top tile rows 0..1
    assert rd32(0x25E0F03C) == 0x000FF000  # bottom tile row 15 (0x18)

    # 2. Draw space (0x20) at (22, 6): allocates all-zero transparent tiles 0x8782/0x8783, count -> 4
    _sim_sh2_text_put(code, saturn_build.RAM_BASE + saturn_build.TEXT_PUT, mem, task, 0x20)
    assert rd16(task + 0x50) == 4 and rd16(task + 0x18) == 0x1706 and rd16(0x0608D776) == 0x20
    assert rd32(nt(22, 6)) == 0x8782 and rd32(nt(22, 7)) == 0x8783
    assert all(mem.get(0x25E0F040 + i, 0) == 0 for i in range(64))

    # 3. Draw 'A' again at (23, 6): cache hit -> reuses 0x8780/0x8781, count stays 4
    _sim_sh2_text_put(code, saturn_build.RAM_BASE + saturn_build.TEXT_PUT, mem, task, ord('A'))
    assert rd16(task + 0x50) == 4 and rd16(task + 0x18) == 0x1806
    assert rd32(nt(23, 6)) == 0x8780 and rd32(nt(23, 7)) == 0x8781

    # 4. Draw 'B' at (24, 6): cache miss -> tiles 0x8784/0x8785 at 0x25E0F080, count -> 6
    _sim_sh2_text_put(code, saturn_build.RAM_BASE + saturn_build.TEXT_PUT, mem, task, ord('B'))
    assert rd16(task + 0x50) == 6 and rd16(task + 0x18) == 0x1906 and rd16(0x0608D778) == ord('B')
    assert rd32(nt(24, 6)) == 0x8784 and rd32(nt(24, 7)) == 0x8785
    assert rd32(0x25E0F080) == 0xFFFFFFFF and rd32(0x25E0F0BC) == 0x00000000  # top row 0 & bottom row 15
    print(f'PASS SH-2 text_put behavioral simulation ({len(code)} B, miss/space/hit/2nd-glyph verified)')


def test_saturn_ui_units():
    # 1. patch_vdp2_screen: keeps untouched tiles/art intact, deduplicates glyphs, enforces VRAM cap
    tiles = bytearray(20 * 32)
    tiles[1 * 32:2 * 32] = b'\x77' * 32   # preserved border tile 1
    tiles[2 * 32:3 * 32] = b'\x88' * 32   # old Japanese text tile 2 (erased -> reusable)
    tmap = bytearray(10 * 4 * 2)
    struct.pack_into('>H', tmap, 0, 1)    # (0,0) kept border
    struct.pack_into('>H', tmap, 2, 2)    # (1,0) erased old text
    saturn_ui.patch_vdp2_screen(tiles, tmap, 10, 4, [(1, 0, 9, 4)], [(2, 1, 'AA')], outline=1)
    assert tiles[1 * 32:2 * 32] == b'\x77' * 32 and struct.unpack_from('>H', tmap, 0)[0] == 1
    assert struct.unpack_from('>H', tmap, 2)[0] == 0  # erased cell zeroed
    # Two 'A's with outline must share tiles (<= 4 unique tiles for 2x2 cells)
    t_a0 = struct.unpack_from('>H', tmap, (1 * 10 + 2) * 2)[0]
    t_a1 = struct.unpack_from('>H', tmap, (1 * 10 + 3) * 2)[0]
    assert t_a0 > 1 and t_a0 == t_a1
    # VRAM budget overflow must raise ValueError
    tiny_tiles = bytearray(3 * 32)
    tiny_map = bytearray(10 * 2 * 2)
    try:
        saturn_ui.patch_vdp2_screen(tiny_tiles, tiny_map, 10, 2, [(0, 0, 10, 2)], [(0, 0, 'ABCD')])
    except ValueError:
        pass
    else:
        raise AssertionError('expected VRAM overflow ValueError')

    # 2. _patch_hp0_hardness preserves digits 0..19 & curves 20..35, writes 36..75
    hp0 = bytearray(76 * 32)
    hp0[:36 * 32] = b'\x55' * (36 * 32)
    saturn_ui._patch_hp0_hardness(hp0)
    assert hp0[:36 * 32] == b'\x55' * (36 * 32) and any(hp0[36 * 32:])

    # 3. _patch_slot_label packs 2x2 row-major blocks with full 1px left outline when room exists
    s77 = bytearray(24 * 32)
    saturn_ui._patch_slot_label(s77, 'NEW GAME', 6)
    assert any(s77[:4 * 32]) and not any(s77[20 * 32:])  # trailing 2 blank blocks
    # First column of pixels in tile 0 (row 0..15) should include outline pixel (1) thanks to x_shift=1
    assert 1 in [b >> 4 for b in s77[0:32:4]]

    # 4. apply_demo_g02_start + apply_demo_g02_nomi preserve surrounding tiles, arrow cap/tip, & flea
    g2_t = bytearray(0xB0 * 32)
    g2_t[1 * 32:0x19 * 32] = b'\x33' * (0x18 * 32)
    g2_t[0x50 * 32:0xA1 * 32] = b'\x44' * (0x51 * 32)
    g2_t[0xAA * 32:] = b'\x66' * (0x06 * 32)
    # Seed Nomi bottom tiles (rows 16..23) with sentinel 0x55 so we verify arrow cap/tip kept & kana dust cleared
    g2_t[0xA7 * 32:0xAA * 32] = b'\x55' * (3 * 32)
    g2_m = bytearray(12 * 5 * 2)
    saturn_ui.apply_demo_g02_start(g2_t, g2_m)
    saturn_ui.apply_demo_g02_nomi(g2_t)
    assert g2_t[1 * 32:0x19 * 32] == b'\x33' * (0x18 * 32)
    assert g2_t[0x50 * 32:0xA1 * 32] == b'\x44' * (0x51 * 32) and g2_t[0xAA * 32:] == b'\x66' * (0x06 * 32)
    nomi_bot = [[0] * 24 for _ in range(8)]
    for tx in range(3):
        blk = gfx.tile_get(g2_t, 0xA7 + tx)
        for y in range(8):
            nomi_bot[y][tx * 8:tx * 8 + 8] = blk[y]
    # Row 17 (bot y=1): arrow cap (11..12) preserved (5); row 18 (bot y=2): arrow (10..12) preserved, kana dust (7..8, 15..18) cleared to 7
    assert all(nomi_bot[1][x] == 5 for x in (11, 12)) and all(nomi_bot[2][x] == 5 for x in (10, 11, 12))
    assert all(nomi_bot[2][x] == 7 for x in (7, 8, 15, 16, 17, 18))
    # Rows 19..23 (bot y=3..7) must remain completely untouched (5)
    assert all(nomi_bot[y][x] == 5 for y in range(3, 8) for x in range(24))
    used_ids = {struct.unpack_from('>H', g2_m, i)[0] for i in range(0, len(g2_m), 2)}
    assert used_ids <= ({0} | set(range(0x19, 0x50))) and len(used_ids) > 10
    # 5. apply_demo_g01_nomi preserves dot (0), arrows (1..3, 0x32), blank (0x16), and writes YAY!/K.O.
    g1_t = bytearray(51 * 32)
    g1_t[0:4 * 32] = b'\xAA' * (4 * 32)
    g1_t[0x32 * 32:0x33 * 32] = b'\xBB' * 32
    g1_m = bytearray(struct.pack('>53H', *range(53)))
    saturn_ui.apply_demo_g01_nomi(g1_t, g1_m)
    assert g1_t[0:4 * 32] == b'\xAA' * (4 * 32) and g1_t[0x32 * 32:0x33 * 32] == b'\xBB' * 32
    assert not any(g1_t[0x16 * 32:0x17 * 32])
    m_words = struct.unpack('>53H', g1_m)
    assert m_words[:4] == (0, 1, 2, 3) and m_words[52] == 52
    assert set(m_words[4:52]) <= set(range(0x04, 0x32)) and len(set(m_words[4:52])) > 20
    print('PASS Milestone C saturn_ui synthetic unit tests (VDP2 screen, hardness, slot, START!, Nomi x2)')


def test_game_arts():
    """Game Arts codecs: synthetic LZSS/map round trips, then the real PUYOSHOW.FLD and
    EFFECT.DAT rebuilt byte for byte from their parsed parts."""
    for data in (b'', b'a', bytes(5000), bytes(range(256)) * 40, os.urandom(3000) + bytes(3000)):
        assert game_arts.lzss_decompress(game_arts.lzss_compress(data))[0] == data
    cells = [0x00020001] * 70 + [0x00020002, 0x40020003] + [0] * 5
    w, h, back, _ = game_arts.map_decode(game_arts.map_encode(7, 11, cells), 0)
    assert (w, h, back) == (7, 11, cells)
    if not os.path.exists(SATURN_BIN):
        print('SKIP Game Arts real-disc round trip (no Track 1)')
        return
    with open(SATURN_BIN, 'rb') as f:
        entries = saturn_iso.parse_iso(f)
        show = saturn_iso.read_iso_file(f, 'PUYOSHOW.FLD', entries)
        effect = saturn_iso.read_iso_file(f, 'EFFECT.DAT', entries)
    ents = game_arts.fld_parse(show)
    assert len(ents) == 158 and game_arts.fld_pack(ents, 2048) == show
    for entry, (block, _) in saturn_credits.ENDINGS.items():
        head, blocks, order = game_arts.container_parse(ents[entry])
        assert game_arts.container_pack(head, blocks, order) == ents[entry]
        assert game_arts.scene_pack(game_arts.scene_parse(blocks[block])) == blocks[block]
    assert game_arts.scene_pack(game_arts.scene_parse(effect)) == effect
    print('PASS Game Arts LZSS/map units + PUYOSHOW.FLD/EFFECT.DAT byte-exact repack')


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

    # 5. Milestone A+B+C build verification across all 3 logo modes (caps, invariants, blank tiles, VRAM budgets)
    with open(SATURN_BIN, 'rb') as f:
        orig_0 = saturn_iso.read_iso_file(f, '0', entries)
        orig_g04 = saturn_iso.read_iso_file(f, 'DEMO_G04.BIN', entries)
        orig_logo = bytes(saturn_arch.unpack_bank(orig_g04)['chunks'][7])
        orig_hp_lens = [len(c) for c in hp['chunks']]
        orig_g01_b = saturn_arch.unpack_bank(saturn_iso.read_iso_file(f, 'DEMO_G01.BIN', entries))
        orig_g01_t6, orig_g01_m7 = bytes(orig_g01_b['chunks'][6]), bytes(orig_g01_b['chunks'][7])
        orig_g02_t12 = bytes(saturn_arch.unpack_bank(saturn_iso.read_iso_file(f, 'DEMO_G02.BIN', entries))['chunks'][12])
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
            if name == 'H_PUYODT.BIN':
                assert len(data) <= saturn_arch.LOW_WRAM_SLOT
                hp_new = saturn_arch.unpack_hpuyodt(data)
                assert [len(c) for c in hp_new['chunks']] == orig_hp_lens
                # Verify the Practice (6,7), Normal (16,7) and Tsuu (26,7) cards are translated with intact borders
                for cx, expect_same in ((6, False), (16, False), (26, False)):
                    orig_c = gfx.block_pixels(hp['chunks'][19], hp['chunks'][20], (7 * 40 + cx) * 2, 8, 8, 40)
                    new_c = gfx.block_pixels(hp_new['chunks'][19], hp_new['chunks'][20], (7 * 40 + cx) * 2, 8, 8, 40)
                    assert (new_c == orig_c) == expect_same
                    # outer frame untouched, inner border a solid black line (restored on Tsuu)
                    assert new_c[:2] == orig_c[:2] and new_c[62:] == orig_c[62:]
                    assert all(nr[:2] == or_[:2] and nr[62:] == or_[62:] for nr, or_ in zip(new_c, orig_c))
                    assert all(new_c[i][j] == 1 for i in (2, 61) for j in range(2, 62))
                    assert all(new_c[j][i] == 1 for i in (2, 61) for j in range(2, 62))
            elif name == 'PUYOSHOW.FLD':
                # staff roll: each ending entry fits its 832 KB work RAM slot, credit maps stay 40x50
                show = game_arts.fld_parse(data)
                for entry, (block, first) in saturn_credits.ENDINGS.items():
                    assert len(show[entry]) <= 851968
                    scene = game_arts.scene_parse(game_arts.container_parse(show[entry])[1][block])
                    for p in range(saturn_credits.PAGES):
                        assert game_arts.map_decode(scene['parts'][first + p], 0)[:2] == (40, 50)
            elif name != '0':
                assert len(data) <= saturn_arch.LOW_WRAM_SLOT
                unpacked[name] = saturn_arch.unpack_bank(data)
        # Verify DEMO_G01[6]+[7] preserved dot/arrows (0..3, 0x32) & blank (0x16) while translating YAY!/K.O.
        g01_t6 = bytes(unpacked['DEMO_G01.BIN']['chunks'][6])
        g01_m7 = bytes(unpacked['DEMO_G01.BIN']['chunks'][7])
        assert len(g01_t6) == len(orig_g01_t6) and len(g01_m7) == len(orig_g01_m7)
        assert g01_t6[:4 * 32] == orig_g01_t6[:4 * 32] and g01_t6[0x32 * 32:] == orig_g01_t6[0x32 * 32:]
        assert not any(g01_t6[0x16 * 32:0x17 * 32])
        assert g01_m7[:8] == orig_g01_m7[:8] and g01_m7[-2:] == orig_g01_m7[-2:]
        assert g01_t6[4 * 32:0x32 * 32] != orig_g01_t6[4 * 32:0x32 * 32]
        # Verify DEMO_G02[12] preserved bg stripes (0x00..0x18) & other 35 portraits (only 0x19..0x4f & Nomi 0xA1..0xA9 patched)
        g02_new = bytes(unpacked['DEMO_G02.BIN']['chunks'][12])
        assert g02_new[:0x19 * 32] == orig_g02_t12[:0x19 * 32]
        assert g02_new[0x50 * 32:0xA1 * 32] == orig_g02_t12[0x50 * 32:0xA1 * 32]
        assert g02_new[0xA1 * 32:0xAA * 32] != orig_g02_t12[0xA1 * 32:0xAA * 32]
        assert g02_new[0xAA * 32:] == orig_g02_t12[0xAA * 32:]
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
        # Verify Milestone B: 2,048 B Spleen font in GFILE09[7] (4-byte aligned) + 12 English tutorial pages
        assert len(unpacked['GFILE09.BIN']['raw'][0]) == 2048
        assert struct.unpack_from('>H', repl['GFILE09.BIN'], 7 * 2)[0] % 4 == 0
        p1_ram = struct.unpack_from('>I', repl['0'], 0x043834)[0]
        p2_ram = struct.unpack_from('>I', repl['0'], 0x043E74)[0]
        assert saturn_build.RAM_BASE + saturn_build.TUT_SCRIPT_AT == p1_ram < p2_ram
        # Walk both rebuilt scripts to verify every op03 resume pointer matches 0xFFFF end
        total_pages = 0
        for start_ram in (p1_ram, p2_ram):
            p = start_ram - saturn_build.RAM_BASE
            while True:
                op = repl['0'][p]
                if op == 0x0D: p += 4
                elif op == 0x03:
                    res = struct.unpack_from('>I', repl['0'], p + 2)[0] - saturn_build.RAM_BASE
                    words = struct.unpack(f'>{(res - (p + 6)) // 2}H', repl['0'][p + 6:res])
                    assert words[-1] == 0xFFFF
                    row_offs = [words[i + 1] for i in range(len(words) - 1) if words[i] == 0xFF02]
                    assert row_offs == [0x01A4 + 0x0180 * r for r in range(len(row_offs))]
                    total_pages += 1; p = res
                elif op == 0x0A: break
                else: p += 2
        assert total_pages == 12
    print('PASS Milestone A+B+C Saturn build (3/3 logo modes, SH-2 text/12 tuts, 23 H_PUYODT UIs, START!, caps)')


if __name__ == '__main__':
    test_mode1_and_iso_patcher()
    test_lzss_arch_and_vdp1_units()
    test_sh2_text_put_sim()
    test_saturn_ui_units()
    test_game_arts()
    test_real_disc()
    print('All Saturn tests passed (stdlib-only).')
