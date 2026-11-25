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
    occ = {(col + tx, row + ty) for col, row, txt in lines for ty in range(2) for tx in range(len(txt))}

    for col, row, txt in lines:
        assert 0 <= col and col + len(txt) <= map_w and 0 <= row and row + 2 <= map_h, (
            f'line {txt!r} out of bounds at ({col},{row}) in {map_w}x{map_h}'
        )
        # Expand canvas by 1 trailing cell when available so x_shift=1 keeps full 1px left & right outlines
        pad = 1 if (
            outline is not None and col + len(txt) < map_w and
            (col + len(txt), row) in erased and (col + len(txt), row + 1) in erased and
            (col + len(txt), row) not in occ and (col + len(txt), row + 1) not in occ
        ) else 0
        w_cells = len(txt) + pad
        img = _render_line_img(txt, w_cells, fg=fg, outline=outline)
        for ty in range(2):
            for tx in range(w_cells):
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
        (5, 3,  'Erase current rule & load Rule'),
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
    # 1. Practice card: remove 'れんしゅう' while preserving Arle's full hair/ponytail silhouette & solid outlines
    prac = gfx.block_pixels(tiles, tmap, (7 * 40 + 6) * 2, 8, 8, 40)
    prac_keep = {
        20: (48, 51), 21: (44, 53), 22: (42, 54), 23: (41, 54), 24: (39, 54),
        25: (38, 55), 26: (36, 55), 27: (32, 55), 28: (30, 55), 29: (30, 55),
        30: (29, 55), 31: (29, 56), 32: (28, 57),
    }
    for y in range(3, 33):
        lo, hi = prac_keep.get(y, (61, 0))
        for x in range(3, 61):
            if x < lo or x > hi:
                prac[y][x] = 0
    # Restore bold continuous black outline around bangs, upper-left crown, and ponytail right edge
    for x, y, v in (
        (41, 22, 1), (40, 23, 1), (41, 23, 1),
        (38, 24, 1), (39, 24, 1), (40, 24, 1), (41, 24, 2),
        (36, 25, 1), (37, 25, 1), (38, 25, 1), (39, 25, 2),
        (32, 26, 1), (33, 26, 1), (34, 26, 1), (35, 26, 1), (36, 26, 1), (37, 26, 2), (38, 26, 4),
        (30, 27, 1), (31, 27, 1), (32, 27, 1), (33, 27, 2), (34, 27, 7),
        (29, 28, 1), (29, 29, 1),
        (52, 20, 1), (53, 21, 1), (54, 21, 1), (54, 22, 1), (54, 23, 1), (54, 24, 1),
        (55, 25, 1), (55, 26, 1), (55, 27, 1), (55, 28, 1), (55, 29, 1),
    ):
        prac[y][x] = v
    _stamp_card(prac, _render_card_word('PRACTICE', 6, 13, 1, (9, 9, 5, 5, 5, 4, 4)), 4)
    gfx.replace_block(tiles, tmap, (7 * 40 + 6) * 2, 8, 8, prac, row_stride=40, blank=0)

    # 2. Normal card: restore sky/clouds behind 'ノーマル', preserving full Tower (incl. left wall) & clean Arle hair
    norm = gfx.block_pixels(tiles, tmap, (7 * 40 + 16) * 2, 8, 8, 40)

    def _sky(x, y):
        if y <= 4:
            return 3
        if y == 5:
            return 6 if 9 <= x <= 12 else 3
        if y == 6:
            return 11 if 8 <= x <= 14 else (6 if 5 <= x <= 17 else 3)
        if y == 7:
            return (11 if 6 <= x <= 15 else 6) if 5 <= x <= 16 else (6 if x >= 59 else 3)
        if y == 8:
            if 5 <= x <= 19:
                return 15 if 8 <= x <= 16 else (11 if 6 <= x <= 18 else 6)
            return 11 if x >= 58 else (6 if x >= 56 else 3)
        if y == 9:
            if x <= 21:
                return 15 if 4 <= x <= 18 else (11 if x <= 20 else 6)
            return 15 if x >= 56 else (11 if x >= 54 else (6 if x >= 52 else 3))
        if y == 10:
            if x <= 21:
                return 15 if x <= 20 else 11
            return 15 if x >= 54 else (11 if x >= 52 else (6 if x >= 50 else 3))
        if y == 11:
            if x <= 21:
                return 15 if x <= 18 else (11 if x <= 19 else (6 if x <= 20 else 3))
            return 15 if x >= 53 else (11 if x >= 51 else 3)
        if y == 12:
            if x <= 19:
                return 15 if 4 <= x <= 16 else (11 if x <= 17 else (6 if x <= 18 else 3))
            return 15 if x >= 52 else (11 if x >= 51 else 3)
        if y == 13:
            if x <= 17:
                return 15 if 4 <= x <= 15 else (11 if x <= 16 else 3)
            return 15 if x >= 56 else (11 if x >= 54 else (6 if x >= 51 else 3))
        if y == 14:
            if x <= 16:
                return 15 if x <= 15 else 11
            return 11 if x >= 57 else 3
        if y == 15:
            if x <= 14:
                return 11 if x <= 13 else 6
            return 11 if 58 <= x <= 59 else (6 if x >= 57 else 3)
        if y == 16:
            return 6 if (x <= 10 or x >= 58) else 3
        if y == 17:
            return 6 if x <= 5 else 3
        return 3

    tower_x = {
        5: (25, 31), 6: (23, 33), 7: (23, 33), 8: (23, 33), 9: (22, 34),
        10: (22, 34), 11: (22, 33), 12: (22, 34), 13: (22, 34), 14: (22, 34),
        15: (21, 35), 16: (20, 36), 17: (20, 36),
        **{y: (19, 37) for y in range(18, 26)},
        26: (18, 36), 27: (15, 36),
        **{y: (13, 35) for y in range(28, 36)},
    }
    arle_x = {
        22: (41, 46), 23: (40, 47), 24: (39, 48), 25: (37, 51),
        26: (36, 52), **{y: (35, 53) for y in range(27, 32)},
        **{y: (35, 54) for y in range(32, 36)},
    }
    for y in range(3, 36):
        tlo, thi = tower_x.get(y, (99, -1))
        alo, ahi = arle_x.get(y, (99, -1))
        for x in range(3, 61):
            if not (tlo <= x <= thi or alo <= x <= ahi):
                norm[y][x] = _sky(x, y)
    # Restore crisp black outlines around both hair puffs & right hair edge (tapered into y=36..39)
    for x, y in (
        (38, 24), (49, 24), (51, 25),
        (54, 29), (54, 30), (54, 31),
        (55, 32), (55, 33), (55, 34), (55, 35), (56, 35),
    ):
        norm[y][x] = 1
    _stamp_card(norm, _render_card_word('NORMAL', 8, 10, 1, (15, 12, 12, 12, 9, 9)), 3)
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


def _pack_img(tiles, tmap, base_word, w_tiles, h_tiles, img, pool, dedup):
    """Deduplicate an (8*w_tiles)x(8*h_tiles) 4bpp image into `pool` and write row-major IDs into `tmap`."""
    for ty in range(h_tiles):
        for tx in range(w_tiles):
            tb = _tile_bytes([r[tx * 8:tx * 8 + 8] for r in img[ty * 8:ty * 8 + 8]])
            tid = dedup.get(tb)
            if tid is None:
                if not pool:
                    raise ValueError('image exceeded exclusive tile pool budget')
                tid = pool.pop(0)
                tiles[tid * 32:(tid + 1) * 32] = tb
                dedup[tb] = tid
            struct.pack_into('>H', tmap, (base_word + ty * w_tiles + tx) * 2, tid)


def apply_demo_g01_nomi(tiles, tmap):
    """Translate High Score (BEST RECORDS) right-window Nomi 'やった'/'ばたんきゅー' to 'YAY!'/'K.O.'."""
    assert len(tiles) == 51 * 32 and len(tmap) == 53 * 2 and not any(tiles[0x16 * 32:0x17 * 32])

    def _banner(mask, shades):
        mw, mh = len(mask[0]), len(mask)
        img = [[0] * 48 for _ in range(32)]
        x0, y0 = (48 - mw) // 2, (32 - mh) // 2
        for y, row in enumerate(mask):
            c = shades[min(len(shades) - 1, y * len(shades) // mh)]
            for x, v in enumerate(row):
                if v:
                    img[y0 + y][x0 + x] = c
        return labels.ring(img, 1, set(shades))

    m_yay = [a + [0, 0] + b for a, b in zip(labels.scaled_mask('YAY', 10, 20, 2), labels.scaled_mask('!', 4, 20, 0))]
    yay_img = _banner(m_yay, (13, 11, 10, 9, 8))
    ko_img = _banner(labels.scaled_mask('K.O.', 10, 20, 2), (15, 6, 5, 4, 3))

    # Preserve tile 0 (flea dot), tiles 1..3 & 0x32 (4 directional arrows), and blank tile 0x16
    pool = [t for t in range(0x04, 0x32) if t != 0x16]
    dedup = {bytes(32): 0x16}
    _pack_img(tiles, tmap, 4, 6, 4, yay_img, pool, dedup)
    _pack_img(tiles, tmap, 28, 6, 4, ko_img, pool, dedup)
    for t in pool:
        tiles[t * 32:(t + 1) * 32] = bytes(32)


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
    _pack_img(tiles, tmap, 0, 12, 5, img, pool, {bytes(32): 0})
    for t in pool:
        tiles[t * 32:(t + 1) * 32] = bytes(32)
