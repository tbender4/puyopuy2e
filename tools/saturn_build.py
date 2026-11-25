"""tools/saturn_build.py - Builds English patched files for Sega Saturn Puyo Puyo 2 (T-6601G).

Milestone A: patches /0;1 ASCII strings + sprite lists and ports all shared MD/Arcade English
graphics across the 8 Bits Lab .BIN banks (DEMO_G00/03/04/05/06, GFILE08/09, FACE_G03),
reusing existing Arcade/MD helpers directly with zero edits to those modules."""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'font'))
import gfx, labels, levels, logo, md_screens, png, saturn_arch, saturn_iso, title_font, titles

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
    'DEMO_G00.BIN', 'DEMO_G03.BIN', 'DEMO_G04.BIN', 'DEMO_G05.BIN',
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


def _apply_strings(prog):
    for off, old, new in SATURN_STRINGS:
        assert len(old) == len(new)
        if prog[off:off + len(old)] != old:
            raise ValueError(f'/0;1 string mismatch at {off:#x}: expected {old!r}, got {bytes(prog[off:off+len(old)])!r}')
        prog[off:off + len(new)] = new


def _apply_logo(prog, chunk, mode):
    if mode not in logo.MODES:
        raise ValueError(f'unknown logo mode: {mode!r}')
    if mode == 'original':
        return
    img = png.read(os.path.join(ROOT, 'assets', 'gfx', 'logo_puyo.png'))
    group_imgs = logo._split_groups(img)
    # Work in MD tile order for G0..G4 (tiles 0..95 = 0x000..0xc00), keeping G5..G8 untouched
    work = bytearray(0xc00)
    next_tile, starts = 0, []
    for g_img, grp in zip(group_imgs, logo.GROUP_LAYOUT):
        grp_starts = []
        for (_, _, w, h, sx, sy) in grp:
            grp_starts.append(next_tile)
            for c in range(w):
                for r in range(h):
                    x0, y0 = sx + 8 * c, sy + 8 * r
                    cell = [(row[x0:x0 + 8] + [0] * 8)[:8] for row in g_img[y0:y0 + 8]]
                    gfx.tile_put(work, next_tile, cell)
                    next_tile += 1
        starts.append(grp_starts)
    assert next_tile <= logo.FIRST_RED

    chunk[0x000:0x8a0] = saturn_arch.tiles_to_sprites(work[0x000:0x8a0], LOGO_G01_SPECS)
    if mode == 'with-red-puyos':
        work[0x8a0:0xc00] = saturn_arch.sprites_to_tiles(chunk[0x8a0:0xc00], LOGO_RED_ORIG_SPECS)
        logo._repack_red_puyos(work, bytes(work))
        chunk[0x8a0:0xc00] = saturn_arch.tiles_to_sprites(work[0x8a0:0xc00], LOGO_RED_CROP_SPECS)

    for table in LOGO_TABLES:
        for g, (at, n) in enumerate(logo.read_groups(prog, table)):
            if g < 2:
                spec = logo.GROUP_LAYOUT[g]
                assert len(spec) <= n
                e0 = at + 2
                low = prog[e0 + 3]  # preserves Saturn Z-priority flag (0x02)
                attr0 = prog[e0 + 4] << 8 | prog[e0 + 5]
                prog[at:at + 2] = struct.pack('>H', len(spec))
                for k, (xr, yr, w, h, _, _) in enumerate(spec):
                    e = at + 2 + 8 * k
                    prog[e:e + 8] = struct.pack(
                        '>hBBHh', yr, (w - 1) << 2 | (h - 1), low,
                        (attr0 & 0xf800) | (logo.FIRST + starts[g][k]), xr,
                    )
            elif g in logo.RED_X:
                if mode == 'no-red-puyos':
                    for k in range(n):
                        prog[at + 2 + 8 * k:at + 4 + 8 * k] = struct.pack('>h', logo.OFFSCREEN_Y)
                else:
                    assert n == 1
                    e = at + 2
                    attr = prog[e + 4] << 8 | prog[e + 5]
                    prog[e:e + 8] = struct.pack('>hBBHh', logo.RED_Y, (2 << 2) | 1, prog[e + 3], attr, logo.RED_X[g])


def _apply_titles_and_allclear(tut_tiles, tut_map, allclear_map):
    # Same as md_build._apply_titles + ALL CLEAR, using Saturn's empty tile 0x08 (not MD 0x1c)
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
        for tx in range(w_tiles):
            gfx.tile_put(tiles_buf, next_tile + tx, [row[tx * 8:tx * 8 + 8] for row in img])
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
        banks = {name: saturn_arch.unpack_bank(saturn_iso.read_iso_file(f, name, entries)) for name in TARGET_BANKS}

    # 1. /0;1 in-place ASCII strings
    _apply_strings(prog)

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

    out = {'0': bytes(prog)}
    for name in TARGET_BANKS:
        out[name] = saturn_arch.pack_bank(banks[name])
    return out
