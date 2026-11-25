"""tools/saturn_ui.py - Saturn-native Japanese UI translation (H_PUYODT.BIN + DEMO_G02 START!).

Milestone C: translates all 23 H_PUYODT.BIN VDP2 menus/dialogs, dynamic Rule Editor hardness
labels (H_PUYODT[0]), save-slot labels (H_PUYODT[77]/[79]), and Character Select START! banner
(DEMO_G02[12..13]) with zero /0;1 edits and strict VDP2 VRAM tile-count preservation."""
import struct
import font, gfx, labels

_GLYPHS = None


def _glyphs():
    global _GLYPHS
    if _GLYPHS is None:
        _GLYPHS = font.font()
    return _GLYPHS


def _render_line_img(text, width_cells, fg=15, outline=None):
    """Render ASCII text in Spleen 8x16 onto a (width_cells*8) x 16 4bpp canvas."""
    glyphs = _glyphs()
    px_w = width_cells * 8
    # shortcut: tight N-cell runs where 8px monospace reaches px_w-2 keep x_shift=0; add 1px shift only when right margin fits
    max_x = -1
    for k, ch in enumerate(text):
        for bits in glyphs[ord(ch)]:
            if bits:
                for x in range(7, -1, -1):
                    if (bits >> (7 - x)) & 1:
                        if k * 8 + x > max_x:
                            max_x = k * 8 + x
                        break
    x_shift = 1 if (outline is not None and max_x < px_w - 2) else 0
    img = [[0] * px_w for _ in range(16)]
    for k, ch in enumerate(text):
        x0 = k * 8 + x_shift
        for y, bits in enumerate(glyphs[ord(ch)]):
            for x in range(8):
                if (bits >> (7 - x)) & 1:
                    img[y][x0 + x] = fg
    if outline is not None:
        img = labels.ring(img, outline, {fg})
    return img


def _tile_bytes(block):
    out = bytearray(32)
    gfx.tile_put(out, 0, block)
    return bytes(out)


def patch_vdp2_screen(tiles, tmap, map_w, map_h, erase_rects, lines, *, fg=15, outline=None):
    """Replace Japanese text rects in an H_PUYODT VDP2 tilemap/tile pair with Spleen 8x16 English.

    Preserves all tiles referenced outside `erase_rects` at their exact original tile IDs and
    strictly keeps len(tiles) == orig_tiles (required by Saturn's gapless VDP2 VRAM layout)."""
    assert len(tiles) >= 32 and len(tiles) % 32 == 0 and not any(tiles[:32]), 'tile 0 must be blank'
    orig_tiles = len(tiles) // 32
    assert len(tmap) == map_w * map_h * 2, f'map size {len(tmap)} != {map_w}x{map_h}x2'

    erased = set()
    for cx, cy, cw, ch in erase_rects:
        assert 0 <= cx and cx + cw <= map_w and 0 <= cy and cy + ch <= map_h
        for r in range(cy, cy + ch):
            for c in range(cx, cx + cw):
                erased.add((c, r))

    keep = {0}
    for r in range(map_h):
        for c in range(map_w):
            if (c, r) not in erased:
                w = struct.unpack_from('>H', tmap, (r * map_w + c) * 2)[0]
                keep.add(w & 0x07FF)

    for c, r in erased:
        struct.pack_into('>H', tmap, (r * map_w + c) * 2, 0)

    free_pool = [t for t in range(1, orig_tiles) if t not in keep]
    dedup = {bytes(32): 0}

    for col, row, txt in lines:
        assert 0 <= col and col + len(txt) <= map_w and 0 <= row and row + 2 <= map_h, (
            f'line {txt!r} out of bounds at ({col},{row}) in {map_w}x{map_h}'
        )
        img = _render_line_img(txt, len(txt), fg=fg, outline=outline)
        for ty in range(2):
            for tx in range(len(txt)):
                assert (col + tx, row + ty) in erased, (
                    f'line {txt!r} writes outside erase_rects at ({col+tx},{row+ty})'
                )
                tb = _tile_bytes([r[tx * 8:tx * 8 + 8] for r in img[ty * 8:ty * 8 + 8]])
                tid = dedup.get(tb)
                if tid is None:
                    if not free_pool:
                        raise ValueError(f'out of VRAM tiles (budget {orig_tiles}) rendering {txt!r}')
                    tid = free_pool.pop(0)
                    tiles[tid * 32:(tid + 1) * 32] = tb
                    dedup[tb] = tid
                struct.pack_into('>H', tmap, ((row + ty) * map_w + col + tx) * 2, tid)

    # Zero unused freed tiles so LZSS compresses them to ~0 bytes
    for t in free_pool:
        tiles[t * 32:(t + 1) * 32] = bytes(32)


def _patch_hp0_hardness(chunk):
    """Patch H_PUYODT[0] tiles 36..75 (Rule Editor hardness words), keeping digits 0..19 & curves 20..35."""
    assert len(chunk) == 76 * 32
    slices = (
        (36, 6, 'NORMAL'),
        (48, 6, '  HARD'),
        (60, 4, 'HARD'),
        (68, 4, ' CAP'),
    )
    for start, w_cells, txt in slices:
        img = _render_line_img(txt, w_cells, fg=15, outline=1)
        for ty in range(2):
            for tx in range(w_cells):
                t = start + ty * w_cells + tx
                chunk[t * 32:(t + 1) * 32] = _tile_bytes(
                    [r[tx * 8:tx * 8 + 8] for r in img[ty * 8:ty * 8 + 8]]
                )


def _patch_slot_label(chunk, txt, n_blocks):
    """Patch H_PUYODT[77] (6x 2x2=12x2) or H_PUYODT[79] (4x 2x2=8x2) packed as 2x2 row-major blocks."""
    w_cells = n_blocks * 2
    assert len(chunk) == n_blocks * 4 * 32 and len(txt) <= w_cells
    img = _render_line_img(txt.ljust(w_cells), w_cells, fg=15, outline=1)
    for b in range(n_blocks):
        for ty in range(2):
            for tx in range(2):
                t = b * 4 + ty * 2 + tx
                cx = b * 2 + tx
                chunk[t * 32:(t + 1) * 32] = _tile_bytes(
                    [r[cx * 8:cx * 8 + 8] for r in img[ty * 8:ty * 8 + 8]]
                )


# Declarative spec for all 23 H_PUYODT.BIN VDP2 map/tile pairs:
# (tile_idx, map_idx, w, h, outline, erase_rects, lines)
HPUYODT_SCREENS = (
    # Controller pad prompts
    (9, 10, 40, 28, None, [(0, 0, 40, 28)], [
        (5, 11, 'Please connect a Control Pad'),
        (11, 14, 'to Controller Port 1.'),
    ]),
    (11, 12, 40, 28, None, [(0, 0, 40, 28)], [
        (5, 8,  'Please connect a Control Pad'),
        (11, 11, 'to Controller Port 1,'),
        (6, 14, 'or move the Port 2 Control'),
        (11, 17, 'Pad into Port 1.'),
    ]),
    # Backup RAM unformatted warning
    (13, 14, 40, 28, None, [(0, 0, 40, 28)], [
        (4, 2,  'Internal RAM (or Cartridge RAM)'),
        (6, 5,  'is not formatted for saving.'),
        (5, 9,  'Please clear all data on your'),
        (5, 12, 'Internal or Cartridge RAM in'),
        (6, 15, 'the Saturn Memory Manager.'),
        (5, 19, 'Hold L or R and press Reset to'),
        (4, 22, 'open the Saturn Memory Manager.'),
    ]),
    # Insufficient save space prompt (preserves YES/NO at (12,20,6,2) and (24,20,4,2))
    (15, 16, 40, 28, None, [(0, 0, 40, 19)], [
        (4, 7,  'Not enough free memory to save.'),
        (4, 10, 'If you start now, your progress'),
        (11, 13, 'cannot be saved.'),
        (10, 16, 'Start game anyway?'),
    ]),
    # Required save blocks screen (dynamic 18 drawn at (25,2,3,2); leave 1-cell gap on both sides)
    (17, 18, 40, 28, None, [(0, 0, 40, 28)], [
        (9, 2,  'Saving requires'),
        (29, 2, 'blocks'),
        (6, 5,  'free to save your game data.'),
        (6, 9,  'Delete other files in Memory'),
        (7, 12, 'Manager, or copy them to a'),
        (4, 15, 'Backup RAM cartridge & restart.'),
        (5, 19, 'Hold L or R and press Reset to'),
        (4, 22, 'open the Saturn Memory Manager.'),
    ]),
    # 1P Level Select header (preserves 3 art panels at r7..14 and description frame at r18..25)
    (19, 20, 40, 28, 1, [(4, 2, 32, 2)], [
        (11, 2, 'Select Difficulty.'),
    ]),
    # 1P Level Select descriptions (blitted into frame at r19; outline=1 pops over translucent box)
    (21, 24, 23, 5, 1, [(0, 0, 23, 5)], [
        (5, 0, 'PRACTICE MODE'),
        (1, 3, 'Battle just 4 rivals.'),
    ]),
    (22, 25, 31, 5, 1, [(0, 0, 31, 5)], [
        (9, 0, 'NORMAL MODE'),
        (1, 3, 'Climb the tower of rivals.'),
    ]),
    (23, 26, 23, 5, 1, [(0, 0, 23, 5)], [
        (7, 0, 'TSUU MODE'),
        (1, 3, 'Battle all 36 rivals.'),
    ]),
    # Save file select (cursor highlights (4,6/10/14/18,8,2) and (4,22,12,2); dynamic slots at col 14)
    (27, 28, 40, 28, 1, [(0, 0, 40, 28)], [
        (8, 2,  'Select a file to continue.'),
        (4, 6,  'BACK'),
        (4, 10, 'DATA 1'),
        (4, 14, 'DATA 2'),
        (4, 18, 'DATA 3'),
        (4, 22, 'DELETE DATA'),
    ]),
    # Delete save select (cursor highlights (4,6/10/14/18,8,2); dynamic slots at col 14)
    (29, 30, 40, 28, 1, [(0, 0, 40, 28)], [
        (8, 2,  'Delete which save file?'),
        (4, 6,  'BACK'),
        (4, 10, 'DATA 1'),
        (4, 14, 'DATA 2'),
        (4, 18, 'DATA 3'),
    ]),
    # Rule Editor WITH Save/Load (dynamic rule# at (19,1,1,2); cursor (4,r,24,2); curve icon preserved at (35,22,2,2))
    (31, 32, 40, 28, 1, [(0, 0, 40, 21), (0, 21, 35, 3), (0, 24, 40, 4)], [
        (14, 1,  'RULE'),
        (21, 1,  'EDITOR'),
        (4, 4,   'BACK'),
        (4, 7,   'SAVE / LOAD RULE'),
        (4, 10,  'PUYO TO POP'),
        (35, 10, 'PY'),
        (4, 13,  'NUISANCE RATE'),
        (35, 13, 'PT'),
        (4, 16,  'NUISANCE PTS'),
        (35, 16, 'PT'),
        (4, 19,  'NUISANCE TYPE'),
        (4, 22,  'CHAIN RATE'),
        (29, 22, 'TYPE'),
        (4, 25,  'ALL CLEAR'),
        (35, 25, 'PY'),
    ]),
    # Rule Editor WITHOUT Save/Load (blitted at screen (0,1); [45+46] overlays (35,8,2,8) at runtime)
    (43, 44, 40, 28, 1, [(0, 0, 40, 28)], [
        (14, 2,  'RULE EDITOR'),
        (4, 5,   'BACK'),
        (4, 8,   'PUYO TO POP'),
        (4, 11,  'NUISANCE RATE'),
        (4, 14,  'NUISANCE PTS'),
        (4, 17,  'NUISANCE TYPE'),
        (4, 20,  'CHAIN RATE'),
        (29, 20, 'TYPE'),
        (4, 23,  'ALL CLEAR'),
        (35, 23, 'PY'),
    ]),
    # Vertical 2x8 unit overlay for [43+44] at screen (35,9)
    (45, 46, 2, 8, 1, [(0, 0, 2, 8)], [
        (0, 0, 'PY'),
        (0, 3, 'PT'),
        (0, 6, 'PT'),
    ]),
    # Rule Back confirm box (preserves border + YES/NO at r9..10; dynamic rule# at (19,3,1,2))
    (33, 34, 40, 13, 1, [(4, 0, 6, 2), (4, 3, 31, 5)], [
        (5, 0,  'BACK'),
        (6, 3,  'Save to Rule'),
        (20, 3, '?'),
        (13, 6, 'Are you sure?'),
    ]),
    # Rule Save/Load submenu (dynamic rule# at (24,2,1,2); cursor highlights (4,r,6,2))
    (35, 36, 40, 13, 1, [(0, 0, 40, 13)], [
        (14, 2, 'RULE SLOT'),
        (4, 5,  'BACK'),
        (4, 8,  'SAVE'),
        (4, 11, 'LOAD'),
    ]),
    # Rule Save confirm box (preserves border + YES/NO at r9..10; dynamic rule# at (19,3,1,2))
    (37, 38, 40, 13, 1, [(4, 0, 6, 2), (4, 3, 31, 5)], [
        (5, 0,  'SAVE'),
        (6, 3,  'Save to Rule'),
        (20, 3, '?'),
        (13, 6, 'Are you sure?'),
    ]),
    # Rule Load confirm box (preserves border + YES/NO at r12..13; dynamic rule# at (6,6,1,2))
    (39, 40, 40, 16, 1, [(4, 0, 6, 2), (4, 3, 32, 8)], [
        (5, 0,  'LOAD'),
        (4, 3,  'Erase current rule and load Rule'),
        (5, 6,  '#'),
        (7, 6,  '.'),
        (13, 9, 'Are you sure?'),
    ]),
    # Rule Edit Main Menu (cursor highlights (5,r,16,2))
    (41, 42, 40, 13, 1, [(0, 0, 40, 13)], [
        (13, 2, 'RULE EDIT MENU'),
        (5, 5,  'BACK'),
        (5, 8,  'EDIT RULE'),
        (5, 11, 'START GAME'),
    ]),
    # Load / Save failure screens
    (47, 48, 40, 28, None, [(0, 0, 40, 28)], [
        (7, 9,  'Failed to load save data.'),
        (8, 12, 'This file cannot be used.'),
        (10, 16, 'Press any button.'),
    ]),
    (49, 50, 40, 28, None, [(0, 0, 40, 28)], [
        (7, 9,  'Failed to save game data.'),
        (10, 12, 'Please try again.'),
        (10, 16, 'Press any button.'),
    ]),
    # Sound Test bonus video titles (ZUTTO.CPK / SYA.CPK)
    (51, 52, 22, 5, None, [(0, 0, 22, 5)], [
        (1, 0, 'ZUTTO SOBA NI IRU YO'),
        (1, 3, 'BURNING FIRE DANCE'),
    ]),
    # Rule Number selector bar (preserves digits 1..9 on rows 4..5!)
    (53, 54, 40, 6, 1, [(4, 0, 32, 2)], [
        (14, 0, 'RULE NUMBER'),
    ]),
)


def _render_card_word(word, w_each, h_each, gap, shades, outline=1):
    """Render chunky arcade lettering with vertical band shading + 1px outline."""
    m = labels.scaled_mask(word, w_each, h_each, gap)
    mw, mh = len(m[0]), len(m)
    canvas = [[0] * (mw + 2) for _ in range(mh + 2)]
    for y, row in enumerate(m):
        c = shades[min(len(shades) - 1, y * len(shades) // mh)]
        for x, v in enumerate(row):
            if v:
                canvas[y + 1][x + 1] = c
    return labels.ring(canvas, outline, set(shades))


def _stamp_card(img, sprite, y0):
    x0 = (64 - len(sprite[0])) // 2
    for y, row in enumerate(sprite):
        yy = y0 + y
        if 3 <= yy < 61:
            for x, v in enumerate(row):
                xx = x0 + x
                if v and 3 <= xx < 61:
                    img[yy][xx] = v


def _patch_difficulty_cards(tiles, tmap):
    """Translate Japanese text inside Practice (6,7) and Normal (16,7) art cards; keep iconic Tsuu kanji."""
    # 1. Practice card: clear kana above Arle/Carbuncle (preserving Arle from arle_left[y]..54) & draw PRACTICE
    prac = gfx.block_pixels(tiles, tmap, (7 * 40 + 6) * 2, 8, 8, 40)
    arle_left = {20: 47, 21: 44, 22: 42, 23: 40, 24: 37, 25: 36, 26: 35, 27: 32, 28: 30, 29: 30, 30: 25, 31: 25, 32: 25}
    for y in range(3, 33):
        for x in range(3, arle_left.get(y, 61)):
            prac[y][x] = 0
        if 20 <= y <= 29:
            for x in range(53 if y <= 21 else 55, 61):
                prac[y][x] = 0
    _stamp_card(prac, _render_card_word('PRACTICE', 6, 14, 1, (9, 9, 5, 5, 5, 4, 4)), 4)
    gfx.replace_block(tiles, tmap, (7 * 40 + 6) * 2, 8, 8, prac, row_stride=40, blank=0)

    # 2. Normal card: restore blue sky/clouds behind kana (preserving Tower & Arle) & draw NORMAL
    norm = gfx.block_pixels(tiles, tmap, (7 * 40 + 16) * 2, 8, 8, 40)

    def _sky(x, y):
        if y <= 5:
            return 3
        if y <= 7:
            return 6 if (6 <= x <= 14 or x >= 55) else 3
        if y <= 14:
            if x <= 17:
                return 15 if 9 <= y <= 13 and x <= 15 else 11
            if x >= 49:
                return 15 if 9 <= y <= 13 and x >= 52 else 11
            return 3
        if y == 15:
            return 11 if (x <= 14 or x >= 54) else 3
        if y == 16:
            return 6 if (x <= 11 or x >= 56) else 3
        return 3

    def _keep(x, y):
        return (
            (5 <= y <= 14 and 23 <= x <= 35) or (15 <= y <= 24 and 19 <= x <= 39) or
            (25 <= y <= 34 and 15 <= x <= 41) or (22 <= y <= 26 and 41 <= x <= 51) or
            (y == 27 and 41 <= x <= 53) or (28 <= y <= 34 and 36 <= x <= 55)
        )

    for y in range(3, 35):
        for x in range(3, 61):
            v = norm[y][x]
            if v == 12 or (not _keep(x, y) and (v in (1, 4, 7, 9) or ((y <= 8 or y >= 15) and v == 15))):
                norm[y][x] = _sky(x, y)
    _stamp_card(norm, _render_card_word('NORMAL', 8, 12, 1, (15, 12, 12, 12, 9, 9)), 3)
    gfx.replace_block(tiles, tmap, (7 * 40 + 16) * 2, 8, 8, norm, row_stride=40, blank=0)


def apply_hpuyodt(hp):
    """Apply all Milestone C English UI translations to an unpacked H_PUYODT.BIN dict."""
    chunks = hp['chunks']
    for ti, mi, w, h, outline, rects, lines in HPUYODT_SCREENS:
        patch_vdp2_screen(chunks[ti], chunks[mi], w, h, rects, lines, fg=15, outline=outline)
    _patch_difficulty_cards(chunks[19], chunks[20])
    _patch_hp0_hardness(chunks[0])
    _patch_slot_label(chunks[77], 'NEW GAME', 6)
    _patch_slot_label(chunks[79], 'CLEARED!', 4)


def apply_demo_g02_nomi(tiles):
    """Translate Tsuu Character Select 3x3 Nomi portrait (DEMO_G02[12] tiles 0xA1..0xA9, row-major)."""
    assert len(tiles) >= 0xAA * 32 and len(tiles) % 32 == 0
    img = [[0] * 24 for _ in range(24)]
    for ty in range(3):
        for tx in range(3):
            cell = gfx.tile_get(tiles, 0xA1 + ty * 3 + tx)
            for y in range(8):
                img[ty * 8 + y][tx * 8:tx * 8 + 8] = cell[y]
    for y in range(2, 19):
        for x in range(2, 22):
            if (y == 17 and x in (11, 12)) or (y == 18 and x in (10, 11, 12)):
                continue
            img[y][x] = 7
    labels._draw_tiny(img, "I'M", 3, 0xC, outline=1)
    labels._draw_tiny(img, "HERE", 10, 0xC, outline=1)
    for ty in range(3):
        for tx in range(3):
            gfx.tile_put(tiles, 0xA1 + ty * 3 + tx, [r[tx * 8:tx * 8 + 8] for r in img[ty * 8:ty * 8 + 8]])


def apply_demo_g02_start(tiles, tmap):
    """Replace Tsuu Character Select 12x5 Japanese 'すたぁと！' with 'START!' inside tiles 0x19..0x4f."""
    assert len(tiles) >= 0x50 * 32 and len(tiles) % 32 == 0 and not any(tiles[:32])
    assert len(tmap) == 12 * 5 * 2
    m_word = labels.scaled_mask('START', 13, 24, 2)
    m_bang = labels.scaled_mask('!', 4, 24, 0)
    m = [a + [0, 0] + b for a, b in zip(m_word, m_bang)]
    mw, mh = len(m[0]), len(m)
    img = [[0] * 96 for _ in range(40)]
    x0, y0 = (96 - mw) // 2, (40 - mh) // 2
    # Vertical gradient fill (12->11->10->9), dark inner edge (5), bright white bubble outline (15)
    shades = (12, 11, 10, 9)
    for y, row in enumerate(m):
        c = shades[min(3, y * 4 // mh)]
        for x, v in enumerate(row):
            if v:
                img[y0 + y][x0 + x] = c
    img = labels.ring(img, 5, {9, 10, 11, 12})
    img = labels.ring(img, 15, {5, 9, 10, 11, 12})

    pool = list(range(0x19, 0x50))  # 55 exclusive tiles (preserves bg 0x01..0x18 & portraits 0x50..0x19c)
    dedup = {bytes(32): 0}
    for ty in range(5):
        for tx in range(12):
            tb = _tile_bytes([r[tx * 8:tx * 8 + 8] for r in img[ty * 8:ty * 8 + 8]])
            tid = dedup.get(tb)
            if tid is None:
                if not pool:
                    raise ValueError('DEMO_G02 START! exceeded 55-tile budget (0x19..0x4f)')
                tid = pool.pop(0)
                tiles[tid * 32:(tid + 1) * 32] = tb
                dedup[tb] = tid
            struct.pack_into('>H', tmap, (ty * 12 + tx) * 2, tid)
    for t in pool:
        tiles[t * 32:(t + 1) * 32] = bytes(32)
