"""tools/saturn_build.py - Builds English patched files for Sega Saturn Puyo Puyo 2 (T-6601G).

Milestone A: patches /0;1 ASCII strings + sprite lists and ports all shared MD/Arcade English
graphics across the 8 Bits Lab .BIN banks (DEMO_G00/03/04/05/06, GFILE08/09, FACE_G03),
reusing existing Arcade/MD helpers directly."""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'font'))
sys.path.insert(0, os.path.join(ROOT, 'text'))
import font, game_arts, gfx, labels, levels, logo, md_screens, png, saturn_arch, saturn_credits, saturn_cutscenes, saturn_iso, saturn_ui, script_en, text, title_font, titles

RAM_BASE = 0x06008000
TEXT_PUT = 0x009488
TEXT_PUT_END = 0x0096FC
TUT_SCRIPT_AT = 0x00BD00        # inside 4,472 B dead MD profile region (0x00BCA0..0x00CE17)
TUT_SCRIPT_END = 0x00CE18
TUT_PTR_REFS = ((0x043834, 0x06014E24), (0x043E74, 0x06015114))  # Part 1 (9 pages), Part 2 (3 pages)

# Exact verified /0;1 in-place ASCII replacements (same length, null-terminated C strings)
SATURN_STRINGS = (
    (0x6d3a6, b'RULE HENKA',    b'RULE SET  '),
    (0x6d3ce, b'SOUSAI',        b'OFFSET'),
    (0x6d65e, b'RENSA SHIBARI', b'CHAIN LIMIT  '),
    (0x6d726, b'MANZAI DEMO',   b'STORY DEMO '),
    (0x6d81c, b'HONTAI   ',     b'INTERNAL '),
    (0x6e684, b'MAX RENSA',     b'MAX CHAIN'),
    (0x6d294, b'COOKATRICE',    b'COCKATRICE'),
    (0x6fb6a, b'COOK',          b'COCK'),
)

# /0;1 sprite list tables (same 8-byte format as MD, with Saturn priority flag 0x02 / 0x01)
LOGO_TABLES = (0x2d038, 0x2d274)
YAY_LIST = 0x2b9e2
LEVEL_SLOTS = (0x2be7e, 0x2be90, 0x2bea2, 0x2beb4, 0x2bec6)  # 18 bytes each, in-place

# VDP1 per-sprite (w_tiles, h_tiles) layouts for modified sprite chunks
LOGO_G01_SPECS = [(4, 3), (4, 4), (3, 4), (3, 4), (3, 4), (2, 1)] + [(1, 1)] * 3
LOGO_RED_ORIG_SPECS = [(3, 3)] * 3
LOGO_RED_CROP_SPECS = [(3, 2), (1, 1), (1, 1), (1, 1)] * 3
CHAIN_TAIL_SPECS = [(4, 2), (3, 1)]
KO_BIG_SPECS = [(4, 4), (4, 4), (3, 4), (1, 2), (2, 3), (4, 3), (3, 2)]
YAY_HEAD_SPECS = [(4, 4), (4, 4), (4, 4), (4, 1), (4, 1), (4, 1)] + [(1, 1)] * 9
NOMI_YAY_SPECS = [(4, 2), (2, 2)]

# Saturn Mode Select adds a 4th Carbuncle mouth mode (Endless Puyo) at 0x732..0x899
SATURN_MODES = (
    (0x282, ('1 PLAYER', 'PUYO')),
    (0x3ea, ('2 PLAYER', 'PUYO')),
    (0x552, ('OPTIONS',)),
    (0x732, ('ENDLESS', 'PUYO')),
)

TARGET_BANKS = (
    'DEMO_G00.BIN', 'DEMO_G01.BIN', 'DEMO_G02.BIN', 'DEMO_G03.BIN', 'DEMO_G04.BIN', 'DEMO_G05.BIN',
    'DEMO_G06.BIN', 'GFILE08.BIN', 'GFILE09.BIN', 'FACE_G03.BIN',
)


class _Streams:
    """Thin Streams shim letting Arcade/MD labels & md_screens helpers write directly into Saturn chunks."""
    def __init__(self, mapping):
        self._map = mapping
        self._orig = {k: bytes(v) for k, v in mapping.items()}

    def get(self, key):
        return self._map[key]

    def original(self, key):
        return self._orig[key]


def assemble_text_put(base_pc=RAM_BASE + TEXT_PUT):
    """Assemble leaf SH-2 8x16 text_put(r4=task, r5=u16 code) into bytes (fits in 628 B slot).

    Uses only caller-saved r0..r7 (zero stack frame, pr/r8..r15 untouched). Expands 1bpp
    8x16 Spleen glyphs at *(u32*)(r4+0x64) into two 4bpp VDP2 tiles at 0x25E00000 using the
    existing 16-entry nibble LUT at 0x0607726C and 64-slot glyph cache at 0x0608D774."""
    ops = []      # list of ('w', u16) | ('br', base_op, mask, lbl) | ('litw', rn, val) | ('litl', rn, val)
    labels_pos = {}
    pc = base_pc
    lit_w = []    # (idx_in_ops, pc_of_op, rn, val)
    lit_l = []

    def L(name):
        labels_pos[name] = pc

    def W(word):
        nonlocal pc
        ops.append(('w', word))
        pc += 2

    def BR(op_base, bits, name):
        nonlocal pc
        ops.append(('br', op_base, bits, name, pc))
        pc += 2

    def MOVW_LIT(rn, val):
        nonlocal pc
        lit_w.append((len(ops), pc, rn, val))
        ops.append(('litw', rn, val))
        pc += 2

    def MOVL_LIT(rn, val):
        nonlocal pc
        lit_l.append((len(ops), pc, rn, val))
        ops.append(('litl', rn, val))
        pc += 2

    # 1. r5 &= 0xFFFF; r6 = VDP2 nametable addr = 0x25E10000 + (((Y << 6) + X) << 2)
    W(0x655D)                   # extu.w  r5, r5
    W(0x854C)                   # mov.w   @(0x18, r4), r0   ; cursor = (X << 8) | Y
    W(0x610C)                   # extu.b  r0, r1            ; r1 = Y
    W(0x4108); W(0x4108); W(0x4108)  # shll2 r1 x3          ; r1 = Y << 6
    W(0x620D)                   # extu.w  r0, r2
    W(0x4219)                   # shlr8   r2                ; r2 = X
    W(0x312C)                   # add     r2, r1            ; (Y << 6) + X
    W(0x4108)                   # shll2   r1                ; * 4 bytes/cell
    MOVL_LIT(6, 0x25E10000)     # mov.l   .L_nt_base, r6
    W(0x361C)                   # add     r1, r6            ; r6 = nt_addr

    # 2. Glyph cache scan at 0x0608D774 (64 x u16, stepped by 2).
    #    Space (0x20) and 0x00 expand to all-zero transparent tiles via the font table,
    #    avoiding vanilla's 0x057D tile constant which is non-blank on the tutorial tileset.
    W(0xE050)                   # mov     #0x50, r0
    W(0x034D)                   # mov.w   @(r0, r4), r3     ; count (0, 2, 4, ...)
    W(0x633D)                   # extu.w  r3, r3
    MOVL_LIT(1, 0x0608D774)     # mov.l   .L_cache, r1
    W(0xE000)                   # mov     #0, r0            ; tile_off = 0
    L('scan')
    W(0x3032)                   # cmp/hs  r3, r0            ; T = (r0 >= count)
    BR(0x8900, 8, 'miss')       # bt      miss
    W(0x071D)                   # mov.w   @(r0, r1), r7
    W(0x677D)                   # extu.w  r7, r7
    W(0x3570)                   # cmp/eq  r7, r5
    BR(0x8D00, 8, 'draw_nt')    # bt/s    draw_nt
    W(0x6203)                   # [delay] mov r0, r2        ; r2 = hit tile_off
    BR(0xA000, 12, 'scan')      # bra     scan
    W(0x7002)                   # [delay] add #2, r0

    # 4. Cache miss: store code, bump count += 2, expand 16 rows 1bpp -> 4bpp (64 B = 2 tiles)
    L('miss')
    W(0x0155)                   # mov.w   r5, @(r0, r1)     ; cache[count/2] = code
    W(0x6233)                   # mov     r3, r2            ; r2 = tile_off
    W(0x7302)                   # add     #2, r3
    W(0xE050)                   # mov     #0x50, r0
    W(0x0435)                   # mov.w   r3, @(r0, r4)     ; task->count = count + 2
    W(0xE064)                   # mov     #0x64, r0
    W(0x014E)                   # mov.l   @(r0, r4), r1     ; font_base
    W(0x4508); W(0x4508)        # shll2   r5 x2             ; code << 4 (16 B/glyph)
    W(0x315C)                   # add     r5, r1            ; r1 = glyph_src
    W(0xE06A)                   # mov     #0x6A, r0
    W(0x034D)                   # mov.w   @(r0, r4), r3     ; tile_base (0x8780)
    W(0x633D)                   # extu.w  r3, r3
    W(0x332C)                   # add     r2, r3            ; tile_base + tile_off
    MOVW_LIT(0, 0x07FF)         # mov.w   .L_07ff, r0
    W(0x2309)                   # and     r0, r3
    W(0x4308); W(0x4308); W(0x4300)  # shll2 x2 + shll      ; << 5 (32 B/tile)
    MOVL_LIT(5, 0x25E00000)     # mov.l   .L_vram, r5
    W(0x335C)                   # add     r5, r3            ; r3 = VRAM dst
    MOVL_LIT(5, 0x0607726C)     # mov.l   .L_lut, r5
    W(0xE710)                   # mov     #16, r7
    L('row')
    W(0x6010)                   # mov.b   @r1, r0           ; hi nibble (keep r1)
    W(0x600C)                   # extu.b  r0, r0
    W(0x4009); W(0x4009)        # shlr2   r0 x2
    W(0x4000)                   # shll    r0                ; * 2
    W(0x005D)                   # mov.w   @(r0, r5), r0
    W(0x2301)                   # mov.w   r0, @r3
    W(0x7302)                   # add     #2, r3
    W(0x6014)                   # mov.b   @r1+, r0          ; lo nibble (advance r1)
    W(0xC90F)                   # and     #0x0F, r0
    W(0x4000)                   # shll    r0                ; * 2
    W(0x005D)                   # mov.w   @(r0, r5), r0
    W(0x2301)                   # mov.w   r0, @r3
    W(0x4710)                   # dt      r7
    BR(0x8F00, 8, 'row')        # bf/s    row
    W(0x7302)                   # [delay] add #2, r3

    # 4. Write 2 vertical nametable entries (tile, tile+1) and advance cursor X += 1
    L('draw_nt')
    W(0xE06A)                   # mov     #0x6A, r0
    W(0x034D)                   # mov.w   @(r0, r4), r3
    W(0x633D)                   # extu.w  r3, r3
    W(0x332C)                   # add     r2, r3            ; tile = tile_base + tile_off
    W(0x2632)                   # mov.l   r3, @r6           ; top cell
    W(0x7301)                   # add     #1, r3
    MOVW_LIT(1, 0x0100)         # mov.w   .L_0100, r1
    W(0x361C)                   # add     r1, r6
    W(0x2632)                   # mov.l   r3, @r6           ; bottom cell
    W(0x854C)                   # mov.w   @(0x18, r4), r0
    W(0x301C)                   # add     r1, r0            ; cursor += 0x0100 (X += 1)
    W(0x000B)                   # rts
    W(0x814C)                   # [delay] mov.w r0, @(0x18, r4)

    # Emit deduplicated 16-bit and 4-byte-aligned 32-bit literal pools right after rts
    pool = bytearray()
    w_addr = {}
    for idx, op_pc, rn, val in lit_w:
        if val not in w_addr:
            w_addr[val] = pc + len(pool)
            pool += struct.pack('>H', val)
        disp = (w_addr[val] - (op_pc + 4)) // 2
        assert 0 <= disp <= 0xFF
        ops[idx] = ('w', 0x9000 | (rn << 8) | disp)
    if (pc + len(pool)) & 3:
        pool += b'\x00\x00'
    l_addr = {}
    for idx, op_pc, rn, val in lit_l:
        if val not in l_addr:
            l_addr[val] = pc + len(pool)
            pool += struct.pack('>I', val)
        disp = (l_addr[val] - ((op_pc + 4) & ~3)) // 4
        assert 0 <= disp <= 0xFF
        ops[idx] = ('w', 0xD000 | (rn << 8) | disp)

    out = bytearray()
    for item in ops:
        if item[0] == 'w':
            out += struct.pack('>H', item[1])
        else:
            _, op_base, bits, name, op_pc = item
            d = (labels_pos[name] - (op_pc + 4)) // 2
            lo, hi = -(1 << (bits - 1)), (1 << (bits - 1)) - 1
            assert lo <= d <= hi, f'branch to {name} out of range: {d}'
            out += struct.pack('>H', op_base | (d & ((1 << bits) - 1)))
    out += pool
    assert len(out) <= TEXT_PUT_END - TEXT_PUT
    return bytes(out)


def _encode_saturn_tut_page(lines):
    """Encode one English tutorial page into Saturn 16-bit script words (0xFF02 newline, 0xFFFF end)."""
    out = []
    used = set()
    for row, line in enumerate(l for l in lines if l != 'IFTURN'):
        assert len(line) <= 18, f'tutorial line > 18 chars: {line!r}'
        out += [0xFF02, text.TUT_FIRST + text.TUT_STEP * row]
        codes = text.encode_line(line)
        used.update(codes)
        out += codes
    assert len(used) <= 64, f'tutorial page uses {len(used)} unique glyphs (max 64)'
    out.append(0xFFFF)
    return struct.pack(f'>{len(out)}H', *out)


def _rebuild_tut_script(prog, orig_start, pages, dst_off):
    """Rebuild one tutorial script sequence at `dst_off`, preserving all vanilla op0d/op05/op07/op0a opcodes."""
    out = bytearray()
    p = orig_start
    page_idx = 0
    while True:
        op, arg = prog[p], prog[p + 1]
        if op == 0x0D:
            out += prog[p:p + 4]
            p += 4
        elif op == 0x03:
            resume = struct.unpack_from('>I', prog, p + 2)[0]
            en_bytes = _encode_saturn_tut_page(pages[page_idx])
            page_idx += 1
            new_resume = RAM_BASE + dst_off + len(out) + 6 + len(en_bytes)
            out += bytes([op, arg]) + struct.pack('>I', new_resume) + en_bytes
            p = resume - RAM_BASE
        elif op == 0x0A:
            out += prog[p:p + 2]
            break
        else:
            out += prog[p:p + 2]
            p += 2
    assert page_idx == len(pages), f'expected {len(pages)} tutorial pages, rebuilt {page_idx}'
    return bytes(out)


def _apply_text(prog, gfile09):
    """Milestone B: install SH-2 8x16 text_put, Spleen 8x16 font in GFILE09[7], and 12 tutorial pages."""
    # 1. Replace text_put in-place (zero-pad remainder of 628 B slot with SH-2 nop 0x0009)
    code = assemble_text_put()
    pad_nops = b'\x00\x09' * ((TEXT_PUT_END - TEXT_PUT - len(code)) // 2)
    prog[TEXT_PUT:TEXT_PUT_END] = code + pad_nops

    # 2. Replace GFILE09[7] (raw[0]) 8,224 B 1bpp JP font with 2,048 B Spleen 8x16 ASCII (0x00..0x7F)
    fbuf = bytearray(128 * 16)
    for code_pt, rows in font.font().items():
        if code_pt < 128:
            fbuf[code_pt * 16:code_pt * 16 + 16] = rows
    gfile09['raw'][0] = fbuf

    # 3. Rebuild Tutorial Part 1 (9 pages) + Part 2 (3 pages) into dead MD profile area (0x00BD00..)
    tut_pages = [lines for _, _, lines in script_en.TEXT[58:70]]
    at = TUT_SCRIPT_AT
    for (ref_off, orig_ram), chunk_pages in zip(TUT_PTR_REFS, (tut_pages[:9], tut_pages[9:])):
        cur = struct.unpack_from('>I', prog, ref_off)[0]
        if cur != orig_ram:
            raise ValueError(f'tutorial pointer at {ref_off:#x}: expected {orig_ram:#x}, got {cur:#x}')
        rebuilt = _rebuild_tut_script(prog, orig_ram - RAM_BASE, chunk_pages, at)
        if at + len(rebuilt) > TUT_SCRIPT_END:
            raise ValueError('English tutorial scripts overflow dead profile region')
        prog[at:at + len(rebuilt)] = rebuilt
        struct.pack_into('>I', prog, ref_off, RAM_BASE + at)
        at += len(rebuilt)
        if at & 1:
            at += 1


def _apply_strings(prog):
    for off, old, new in SATURN_STRINGS:
        assert len(old) == len(new)
        if prog[off:off + len(old)] != old:
            raise ValueError(f'/0;1 string mismatch at {off:#x}: expected {old!r}, got {bytes(prog[off:off+len(old)])!r}')
        prog[off:off + len(new)] = new


def _apply_logo(prog, chunk, mode):
    if mode == 'original':
        return
    # logo.apply packs G0..G4 in MD tile order (tiles 0..95); VDP1 needs them re-swizzled per sprite
    work = bytearray(0xc00)
    work[0x8a0:0xc00] = saturn_arch.sprites_to_tiles(chunk[0x8a0:0xc00], LOGO_RED_ORIG_SPECS)
    logo.apply(prog, _Streams({logo.TILES: work}), mode, LOGO_TABLES)
    chunk[0x000:0x8a0] = saturn_arch.tiles_to_sprites(work[0x000:0x8a0], LOGO_G01_SPECS)
    if mode == 'with-red-puyos':
        chunk[0x8a0:0xc00] = saturn_arch.tiles_to_sprites(work[0x8a0:0xc00], LOGO_RED_CROP_SPECS)


def _apply_titles_and_allclear(tut_tiles, tut_map, allclear_map):
    # Same as titles.apply + labels.apply_allclear, using Saturn's empty tile 0x08 (not MD 0x1c)
    letters = sorted(set(''.join(titles.TITLES)) - {' '})
    assert titles.FIRST_TILE + 2 * len(letters) <= titles.LAST_TILE + 1
    slot = {}
    for k, ch in enumerate(letters):
        g = title_font.glyph(ch)
        top, bot = titles.FIRST_TILE + 2 * k, titles.FIRST_TILE + 2 * k + 1
        gfx.tile_put(tut_tiles, top, [[titles.COLOUR * v for v in r] for r in g[:8]])
        gfx.tile_put(tut_tiles, bot, [[titles.COLOUR * v for v in r] for r in g[8:]])
        slot[ch] = (top, bot)
    blank = [[0] * 8 for _ in range(8)]
    for t in range(titles.FIRST_TILE + 2 * len(letters), titles.LAST_TILE + 1):
        gfx.tile_put(tut_tiles, t, blank)
    for k, title in enumerate(titles.TITLES):
        s = title.center(titles.WIDTH)
        for row in range(2):
            for col, ch in enumerate(s):
                v = 0x08 if ch == ' ' else slot[ch][row]
                i = titles.MAP_AT + 2 * ((2 * k + row) * titles.WIDTH + col)
                tut_map[i:i + 2] = v.to_bytes(2, 'big')

    img = [[0] * 96 for _ in range(8)] + labels.render(labels.ALL_CLEAR, 96, 16, 0xa, 0x1)
    for x in range(96):
        for y in range(23, -1, -1):
            if img[y][x] == 0xa:
                img[y][x] = 0x9
                break
    gfx.replace_block(tut_tiles, allclear_map, 0x270, 12, 3, img, row_stride=14, blank=0x08)


def _apply_levels(prog, chunk):
    # Pack 4 single-sprite words in GFILE08[13] tiles 0..12 so all 5 level lists fit in-place
    # inside their original 18-byte slots (0x2be7e..0x2bed7), never touching live /0;1 BSS.
    word_specs = (('EXTRA', 4), ('MILD', 3), ('MEDIUM', 4), ('HOT', 2))
    word_info = {}
    tiles_buf = bytearray(20 * 32)
    next_tile = 0
    for word, w_tiles in word_specs:
        px_w = w_tiles * 8
        img = [[0] * px_w for _ in range(8)]
        for k, ch in enumerate(word):
            for y, row in enumerate(levels.FONT[ch]):
                for x, c in enumerate(row):
                    if c == '#':
                        xx = levels.PITCH * k + x
                        img[y][xx] = 7
                        for dy, dx in ((1, 0), (0, 1), (1, 1)):
                            if y + dy < 8 and xx + dx < px_w and img[y + dy][xx + dx] == 0:
                                img[y + dy][xx + dx] = 1
        labels.put_tiles(tiles_buf, img, [list(range(next_tile, next_tile + w_tiles))])
        word_info[word] = (next_tile, w_tiles, levels.PITCH * len(word) - 1)
        next_tile += w_tiles

    specs = [(w, 1) for _, w in word_specs] + [(1, 1)] * (20 - next_tile)
    chunk[0x000:0x280] = saturn_arch.tiles_to_sprites(tiles_buf, specs)

    for slot, lines in zip(LEVEL_SLOTS, levels.LABELS):
        y0 = -4 * len(lines)
        entries = []
        for row, word in enumerate(lines):
            first, w_tiles, text_w = word_info[word]
            sz = (w_tiles - 1) << 2
            entries.append((y0 + 8 * row, sz, 0x02, levels.ATTR + first, -(text_w // 2)))
        data = struct.pack('>H', len(entries)) + b''.join(struct.pack('>hBBHh', *e) for e in entries)
        assert len(data) <= 18
        prog[slot:slot + len(data)] = data


def _apply_yay(prog, chunk):
    yimg = png.read(os.path.join(labels.ASSETS, 'yay.png'))
    tiles_buf = bytearray(69 * 32)
    sprites = [(-32, 0x0f02, 16 * k, -48 + 32 * k, 4, 4) for k in range(3)] + \
              [(0, 0x0c02, 48 + 4 * k, -48 + 32 * k, 4, 1) for k in range(3)]
    data = struct.pack('>H', len(sprites))
    for sy, sz_flag, first, sx, w, h in sprites:
        data += struct.pack('>hHHh', sy, sz_flag, 0x0680 + first, sx)
        for c in range(w):
            for r in range(h):
                cell = [row[sx + 48 + 8 * c:sx + 56 + 8 * c] for row in yimg[sy + 32 + 8 * r:sy + 40 + 8 * r]]
                gfx.tile_put(tiles_buf, first + h * c + r, cell)
    prog[YAY_LIST:YAY_LIST + len(data)] = data
    chunk[0x000:0x8a0] = saturn_arch.tiles_to_sprites(tiles_buf, YAY_HEAD_SPECS)


def _apply_special_rules(hdr_map, hdr_tiles, rule_map, rule_tiles):
    hdr = md_screens._remap(png.read(os.path.join(labels.ASSETS, 'choose_rule.png')), md_screens.HEADER_REMAP)
    gfx.replace_block(hdr_tiles, hdr_map, 0x8c0, 33, 3, hdr)
    # 0x9c is empty, >= 0x78 (outside header tileset), and unreferenced in rule_map so it never enters the pool
    blocks = [(off, 18, 2, md_screens._render_rule_line_md(txt, 18), 18) for off, txt in md_screens.SPECIAL_RULES]
    gfx.replace_blocks(rule_tiles, rule_map, blocks, blank=0x9c)
    assert not any(rule_tiles[0x9c * gfx.TILE:0x9d * gfx.TILE])


def build(src_bin, logo_mode=logo.DEFAULT_MODE):
    """Build patched Saturn files from Track 1 .bin. Returns dict {iso_name: bytes}."""
    with open(src_bin, 'rb') as f:
        entries = saturn_iso.parse_iso(f)
        prog = bytearray(saturn_iso.read_iso_file(f, '0', entries))
        hp = saturn_arch.unpack_hpuyodt(saturn_iso.read_iso_file(f, 'H_PUYODT.BIN', entries))
        banks = {name: saturn_arch.unpack_bank(saturn_iso.read_iso_file(f, name, entries)) for name in TARGET_BANKS}
        puyoshow = saturn_iso.read_iso_file(f, 'PUYOSHOW.FLD', entries)
        effect = saturn_iso.read_iso_file(f, 'EFFECT.DAT', entries)

    # 1. /0;1 in-place ASCII strings + Milestone B SH-2 8x16 tutorial text engine & font
    _apply_strings(prog)
    _apply_text(prog, banks['GFILE09.BIN'])

    # 2. VDP1 sprite chunks with /0;1 sprite tables
    _apply_logo(prog, banks['DEMO_G04.BIN']['chunks'][7], logo_mode)
    _apply_levels(prog, banks['GFILE08.BIN']['chunks'][13])
    _apply_yay(prog, banks['GFILE08.BIN']['chunks'][15])

    # 3. Direct-reuse VDP2 & hybrid chunks via _Streams shim
    g8_chain = banks['GFILE08.BIN']['chunks'][5]
    g8_ko_big = banks['GFILE08.BIN']['chunks'][14]
    f3_idle, f3_win, f3_box = banks['FACE_G03.BIN']['chunks'][9:12]

    # Unswizzle read-modify-write VDP1 slices before handing to Arcade/MD helpers
    g8_chain[0xe00:0xf60] = saturn_arch.sprites_to_tiles(g8_chain[0xe00:0xf60], CHAIN_TAIL_SPECS)
    ko_big_tiles = bytearray(len(g8_ko_big))

    streams = _Streams({
        0x0900be: banks['GFILE09.BIN']['chunks'][0],      # Pause (raw)
        0x091545: banks['GFILE09.BIN']['chunks'][4],      # Tutorial tiles (VDP2)
        0x0456fa: banks['DEMO_G06.BIN']['chunks'][9],     # Tutorial ASK map (VDP2)
        0x083f2b: g8_chain,                               # Chain + Offset (tail unswizzled)
        0x0869e7: ko_big_tiles,                           # KO Big (unswizzled)
        0x085dc1: banks['GFILE08.BIN']['chunks'][9],      # KO Small (raw)
        0x0c62d1: banks['DEMO_G00.BIN']['chunks'][9],     # Tower PICK YOUR RIVAL (VDP2)
        0x0c8503: banks['DEMO_G00.BIN']['chunks'][11],    # Nomi Tower portrait (raw)
        0x0cc655: banks['DEMO_G00.BIN']['chunks'][13],    # Continue map (VDP2)
        0x0cca17: banks['DEMO_G00.BIN']['chunks'][14],    # Continue tiles (VDP2)
        0x03eaff: banks['DEMO_G05.BIN']['chunks'][17],    # Act Against AIDS map (VDP2)
        0x03ee26: banks['DEMO_G05.BIN']['chunks'][18],    # Act Against AIDS tiles (VDP2)
        0x0a5a1e: f3_idle,                                # Nomi center idle (hybrid)
        0x0a5ce6: f3_win,                                 # Nomi center win (hybrid)
        0x0a602d: f3_box,                                 # Nomi Tower box map (VDP2)
        0x0ebd39: bytearray(0x50 * 32),                   # Unused on Saturn (dummy target for apply_here)
    })

    md_screens.apply_pause(streams)
    labels.apply_chain(streams)
    labels.apply_knockout(streams)
    labels.apply_tower(streams)
    labels.apply_here(streams)
    labels.apply_gameover(streams)
    labels.apply_aids(streams)
    labels.apply_ask(streams)

    # Swizzle modified VDP1 slices back to Saturn linear 4bpp
    g8_chain[0xe00:0xf60] = saturn_arch.tiles_to_sprites(g8_chain[0xe00:0xf60], CHAIN_TAIL_SPECS)
    g8_ko_big[:] = saturn_arch.tiles_to_sprites(ko_big_tiles, KO_BIG_SPECS)
    f3_idle[0:128] = saturn_arch.tiles_to_vdp1(f3_idle[0:128], 4, 1)
    f3_idle[0x0a * 32:0x1c * 32] = saturn_arch.tiles_to_sprites(f3_idle[0x0a * 32:0x1c * 32], [(4, 1), (2, 1)] * 3)
    f3_win[0:128] = saturn_arch.tiles_to_vdp1(f3_win[0:128], 4, 1)
    f3_win[10 * 32:22 * 32] = saturn_arch.tiles_to_sprites(f3_win[10 * 32:22 * 32], NOMI_YAY_SPECS)
    f3_win[22 * 32:34 * 32] = saturn_arch.tiles_to_sprites(f3_win[22 * 32:34 * 32], NOMI_YAY_SPECS)

    # 4. Saturn-adjusted VDP2 screens (blank tile offsets + 4th Mode Select option)
    _apply_titles_and_allclear(
        banks['GFILE09.BIN']['chunks'][4],
        banks['DEMO_G06.BIN']['chunks'][2],
        banks['DEMO_G06.BIN']['chunks'][7],
    )
    md_screens.patch_mode_select(banks['DEMO_G06.BIN']['chunks'][13], banks['DEMO_G06.BIN']['chunks'][12],
                                 SATURN_MODES, blank=0x04)
    _apply_special_rules(
        banks['DEMO_G03.BIN']['chunks'][14], banks['DEMO_G03.BIN']['chunks'][15],
        banks['DEMO_G03.BIN']['chunks'][16], banks['DEMO_G03.BIN']['chunks'][17],
    )

    # 5. Milestone C: Saturn-native H_PUYODT.BIN UI screens + DEMO_G01/G02 Nomi & START! + shared wallpaper
    saturn_ui.apply_hpuyodt(hp)
    logo.apply_wallpaper(hp['chunks'][68], 0, logo_mode)
    logo.apply_wallpaper(banks['DEMO_G00.BIN']['chunks'][7], 260, logo_mode)
    saturn_ui.apply_demo_g01_nomi(banks['DEMO_G01.BIN']['chunks'][6], banks['DEMO_G01.BIN']['chunks'][7])
    saturn_ui.apply_demo_g02_start(banks['DEMO_G02.BIN']['chunks'][12], banks['DEMO_G02.BIN']['chunks'][13])
    saturn_ui.apply_demo_g02_nomi(banks['DEMO_G02.BIN']['chunks'][12])

    # 6. Milestone D: Game Arts files (PUYOSHOW.FLD staff roll and cutscene art, EFFECT.DAT caption)
    show = game_arts.fld_parse(puyoshow)
    saturn_credits.apply(show)
    saturn_cutscenes.apply_signs(show)
    saturn_cutscenes.apply_captions(show)
    saturn_cutscenes.apply_aids(show)
    saturn_cutscenes.apply_schezo(show)

    out = {'0': bytes(prog), 'H_PUYODT.BIN': saturn_arch.pack_hpuyodt(hp),
           'PUYOSHOW.FLD': game_arts.fld_pack(show, struct.unpack_from('>I', puyoshow, 0)[0]),
           'EFFECT.DAT': saturn_cutscenes.apply_effect(effect)}
    for name in TARGET_BANKS:
        out[name] = saturn_arch.pack_bank(banks[name])
    return out
