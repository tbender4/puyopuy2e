"""Builds the English Mega Drive ROM from Puyo Puyo 2 (Japan) (v1.1).md.

Reuses Zanac's arcade helpers and assets directly, with arcade stream addresses mapped to MD
ones (MD_STREAMS).
Only the Spleen 8x16 font goes in bank 0x090000 (required by the 16-bit table entry at
0x09000e); hooks, English script pages, level sprite lists, and Rule Edit strings live in
the empty 448 KB region starting at 0x110000."""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'text'))
sys.path.insert(0, os.path.join(ROOT, 'font'))
import font, gfx, labels, levels, logo, md_credits, md_screens, png, script_en, text, titles
from build import jmp, patch_file

# Bank 0x090000 (font offset must be a 16-bit offset in bank 0x090000; free 0xff from 0x993bf)
FONT_BANK_ENTRY = 0x09000e
FONT = 0x099400

# Empty 448 KB region (0x110000..0x17ffff) for 32-bit-addressed code and tables
HOOKS = 0x110000
DATA_AT = 0x110100
DATA_END = 0x118000

# 68000 code hooks
TEXT_PUT = 0x0151cc
TEXT_PUT_END = 0x015314
OP03_PATCH = (0x014e76, 14)
OP0B_PATCH = (0x014ece, 24)

# All 70 MD script pages (58 character profiles + 12 tutorials), 1-to-1 with script_en.TEXT[:70]
MD_PAGES = (
    0x017e6c, 0x017ecc, 0x017f0e, 0x017f64, 0x017fb0, 0x017fd8, 0x018030, 0x018086,
    0x0180cc, 0x018120, 0x01816e, 0x0181b2, 0x018218, 0x01828a, 0x0182d6, 0x01830a,
    0x01835c, 0x018386, 0x0183e0, 0x018426, 0x018482, 0x0184ce, 0x018514, 0x018552,
    0x01858c, 0x0185f4, 0x01862a, 0x01866e, 0x0186b2, 0x0186da, 0x01873c, 0x018766,
    0x0187ce, 0x018832, 0x018898, 0x0188e6, 0x018918, 0x018968, 0x01899c, 0x0189da,
    0x018a18, 0x018a50, 0x018a8e, 0x018aee, 0x018b2e, 0x018b8c, 0x018bd4, 0x018c10,
    0x018c58, 0x018cac, 0x018d00, 0x018d36, 0x018d82, 0x018dea, 0x018e32, 0x018e62,
    0x018eba, 0x018f14, 0x018f7c, 0x018fe4, 0x01903e, 0x019088, 0x0190ce, 0x019156,
    0x0191a8, 0x0191dc, 0x019222, 0x01926c, 0x0192dc, 0x01933e,
)

# MD addresses used directly (LOGO_TABLES/LOGO_TILES also read by test_build_md)
LOGO_TABLES = (0x02836a, 0x0285a6)
LOGO_TILES = 0x0b751d
YAY_TILES = 0x086fa1
YAY_LIST = 0x01a2b8
LEVEL_TILES = 0x0863d1
LEVEL_TABLE = 0x01a6e2

# Arcade stream address -> MD address, so the arcade titles/labels/logo code runs unchanged
MD_STREAMS = {
    logo.TILES: LOGO_TILES,
    0x091545: 0x092640,     # tutorial tiles
    0x083f2b: 0x083f37,     # CHAIN + OFFSET
    0x0869e7: 0x086a7f,     # K.O. big
    0x085dc1: 0x085dcd,     # K.O. small
}


class _MDStreams(gfx.Streams):
    def get(self, addr):
        return super().get(MD_STREAMS.get(addr, addr))

    def original(self, addr):
        return super().original(MD_STREAMS.get(addr, addr))


def _relocate(blob, old, new, count):
    assert blob.count(old) == count, 'expected %d hits, got %d' % (count, blob.count(old))
    return blob.replace(old, new)


def _apply_text(prog, at, end):
    assert len(MD_PAGES) == 70
    for idx, orig in enumerate(MD_PAGES):
        _, kind, lines = script_en.TEXT[idx]
        # MD page 59 always shows both rotate buttons (no arcade TURN DIRECTION DIP switch)
        if idx == 59:
            lines = [l for l in lines if l != 'IFTURN']
        assert at % 2 == 0
        words = text.page_words(kind, lines, at)
        data = struct.pack('>%dH' % len(words), *words)
        if at + len(data) > end:
            raise SystemExit('English text does not fit')
        prog[at:at + len(data)] = data
        prog[orig:orig + 6] = struct.pack('>HI', 0xfffe, at)
        at += len(data)
    return at


def _apply_yay(prog, streams):
    # labels.apply_yay writes the arcade list address; MD's list is at YAY_LIST
    yimg = png.read(os.path.join(labels.ASSETS, 'yay.png'))
    ytiles = streams.get(YAY_TILES)
    sprites = [(-32, 0x0f08, 16 * k, -48 + 32 * k, 4, 4) for k in range(3)] + \
              [(0, 0x0c08, 48 + 4 * k, -48 + 32 * k, 4, 1) for k in range(3)]
    data = struct.pack('>H', len(sprites))
    for sy, size, first, sx, w, h in sprites:
        data += struct.pack('>hHHh', sy, size, 0x0680 + first, sx)
        for c in range(w):
            for r in range(h):
                cell = [row[sx + 48 + 8 * c:sx + 56 + 8 * c] for row in yimg[sy + 32 + 8 * r:sy + 40 + 8 * r]]
                gfx.tile_put(ytiles, first + h * c + r, cell)
    prog[YAY_LIST:YAY_LIST + len(data)] = data
    for t in range(60, 69):
        gfx.tile_put(ytiles, t, [[0] * 8 for _ in range(8)])


def _apply_levels(prog, streams, at, end):
    pieces, lists = {}, []
    for lines in levels.LABELS:
        sprites = []
        y0 = -4 * len(lines)
        for row, word in enumerate(lines):
            x0 = -((levels.PITCH * len(word) - 1) // 2)
            for i in range(0, len(word), levels.PER_PIECE):
                k = pieces.setdefault(word[i:i + levels.PER_PIECE], len(pieces))
                sprites.append((y0 + 8 * row, 0x0408, levels.ATTR + 2 * k, x0 + levels.PITCH * i))
        lists.append(sprites)
    assert len(pieces) <= 10
    tiles = streams.get(LEVEL_TILES)
    for part, k in pieces.items():
        labels.put_tiles(tiles, levels.piece_pixels(part), [[2 * k, 2 * k + 1]])
    for t in range(2 * len(pieces), 20):
        gfx.tile_put(tiles, t, [[0] * 8 for _ in range(8)])
    for level, sprites in enumerate(lists):
        assert at % 2 == 0
        data = struct.pack('>H', len(sprites)) + b''.join(struct.pack('>hHHh', *s) for s in sprites)
        if at + len(data) > end:
            raise SystemExit('levels: no room')
        prog[at:at + len(data)] = data
        prog[LEVEL_TABLE + 4 * level:LEVEL_TABLE + 4 * level + 4] = struct.pack('>I', at)
        at += len(data)
    return at


def update_md_checksum(prog):
    """Update the standard Sega Mega Drive 16-bit header checksum at 0x00018e."""
    total = sum(struct.unpack('>%dH' % ((len(prog) - 0x200) // 2), prog[0x200:])) & 0xffff
    prog[0x18e:0x190] = struct.pack('>H', total)


def build(prog, logo_mode=logo.DEFAULT_MODE):
    prog = bytearray(prog)
    # 1. Text engine (8x16 glyphs): relocate VDP write helper 0x1056 -> 0x111a
    eng = _relocate(patch_file('text8.bin'), b'\x4e\xb8\x10\x56', b'\x4e\xb8\x11\x1a', 3)
    assert len(eng) <= TEXT_PUT_END - TEXT_PUT
    prog[TEXT_PUT:TEXT_PUT + len(eng)] = eng

    # 2. Spleen 8x16 font in bank 0x090000; zero 0x00..0x1f so gfx.free_space() never claims it
    prog[FONT_BANK_ENTRY:FONT_BANK_ENTRY + 2] = struct.pack('>H', FONT & 0xffff)
    prog[FONT:FONT + 0x200] = bytes(0x200)
    for code, rows in font.font().items():
        prog[FONT + code * 16:FONT + code * 16 + 16] = rows

    # 3. Script page opener hooks + 70 English pages in empty bank 0x110000
    hooks = _relocate(patch_file('hooks.bin'), b'\x4e\xf9\x00\x01\x74\x00', b'\x4e\xf9\x00\x01\x50\xac', 2)
    prog[HOOKS:HOOKS + len(hooks)] = hooks
    jmp(prog, OP03_PATCH[0], HOOKS, OP03_PATCH[1])
    jmp(prog, OP0B_PATCH[0], HOOKS + 0x10, OP0B_PATCH[1])

    at = _apply_text(prog, DATA_AT, DATA_END)
    print('English text: %d bytes' % (at - DATA_AT))

    # 4. Shared arcade graphics + Mega Drive-exclusive screens
    streams = _MDStreams(prog)
    # Keep all 8 slots of titles.TITLES: MD skips slot 6 (JOINING IN) and reads slot 7 (QUICK TURN) at 0xffcb28.
    titles.apply(streams)
    logo.apply(prog, streams, logo_mode, LOGO_TABLES)
    if logo_mode != 'original':  # streams.get() alone would recompress the stream
        logo.apply_wallpaper(streams.get(logo.WALLPAPER_TILES), 258, logo_mode)
    labels.apply_allclear(streams)
    labels.apply_chain(streams)
    labels.apply_knockout(streams)
    _apply_yay(prog, streams)
    # Tower, Nomi, Continue, and Act Against AIDS (exact same addresses as arcade)
    labels.apply_tower(streams)
    labels.apply_here(streams)
    labels.apply_gameover(streams)
    labels.apply_aids(streams)
    at = _apply_levels(prog, streams, at, DATA_END)
    at = md_screens.apply(prog, streams, at, DATA_END)
    at = md_credits.apply(prog, streams, at, DATA_END)
    print('MD extra data total: %d bytes (ends at 0x%06x)' % (at - DATA_AT, at))
    streams.write()
    update_md_checksum(prog)
    return prog
