"""Small English labels drawn over Japanese ones, with the capitals of font/title_font.py:
the letters filled with one colour and outlined with another, as the originals are."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'font'))
import title_font, gfx


def letter_mask(ch):
    """rows of 0/1, trimmed to the letter's columns"""
    if ch == ' ':
        return [[0, 0] for _ in range(13)]
    rows = [r for r in title_font.glyph(ch)[1:14]]
    cols = [x for x in range(8) if any(r[x] for r in rows)]
    return [r[cols[0]:cols[-1] + 1] for r in rows]


def render(text, width, height, fill, outline, gap=1, shine=None):
    """width x height pixel values: text centred, filled and outlined"""
    masks = [letter_mask(ch) for ch in text]
    w = sum(len(m[0]) for m in masks) + gap * (len(masks) - 1)
    if w + 2 > width:
        raise SystemExit('label %r: %d pixels, room for %d' % (text, w + 2, width))
    img = [[0] * width for _ in range(height)]
    x0, y0 = (width - w) // 2, (height - 13) // 2
    x = x0
    for m in masks:
        for y, row in enumerate(m):
            for dx, v in enumerate(row):
                if v:
                    img[y0 + y][x + dx] = fill
        x += len(m[0]) + gap
    out = [row[:] for row in img]
    for y in range(height):
        for x in range(width):
            if img[y][x] == fill:
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        yy, xx = y + dy, x + dx
                        if 0 <= yy < height and 0 <= xx < width and img[yy][xx] != fill:
                            out[yy][xx] = outline
    if shine is not None:                    # the top of each letter a lighter colour
        for x in range(width):
            for y in range(height):
                if img[y][x] == fill:
                    out[y][x] = shine
                    break
    return out


def put_tiles(tiles, img, order):
    """order[ty][tx] = the tile that gets the 8x8 block (tx, ty) of img"""
    for ty, row in enumerate(order):
        for tx, t in enumerate(row):
            gfx.tile_put(tiles, t, [r[tx * 8:tx * 8 + 8] for r in img[ty * 8:ty * 8 + 8]])


def sprite_order(first, width_tiles, height_tiles, sprites):
    """tile numbers of sprites side by side, each width_tiles x height_tiles, column-major"""
    order = [[0] * (width_tiles * sprites) for _ in range(height_tiles)]
    for s in range(sprites):
        for c in range(width_tiles):
            for r in range(height_tiles):
                order[r][s * width_tiles + c] = first + s * width_tiles * height_tiles + c * height_tiles + r
    return order


JOIN_IN = "JOIN IN!"


def apply(streams):
    # the 乱入可能 sign: in play (two 4x2 sprites, stream 0x900be tiles 0-15) and in the
    # tutorial (stream 0x91545, 8 x 2 tiles from 0x14d, row by row)
    img = render(JOIN_IN, 64, 16, 0xf, 0x1)
    put_tiles(streams.get(0x900be), img, sprite_order(0, 4, 2, 2))
    apply_crossed(streams, img)
    put_tiles(streams.get(0x91545), img, [list(range(0x14d, 0x155)), list(range(0x155, 0x15d))])
    apply_allclear(streams)
    apply_tower(streams)
    apply_gameover(streams)
    apply_here(streams)
    apply_entry(streams)
    apply_aids(streams)
    apply_chain(streams)
    apply_badge(streams)
    apply_rules(streams)


def rows_order(first, width_tiles, height_tiles):
    """tile numbers of a block stored row by row"""
    return [list(range(first + r * width_tiles, first + (r + 1) * width_tiles)) for r in range(height_tiles)]


PICK = ("PICK", "YOUR RIVAL")


def apply_tower(streams):
    # 相手を / えらんでね on the tower screen (stream 0xc62d1): 6 x 2 tiles from 0x78, then
    # 10 x 2 tiles from 0x84, in red (8) outlined (7), the top of each letter lighter (d)
    tiles = streams.get(0xc62d1)
    put_tiles(tiles, render(PICK[0], 48, 16, 8, 7, shine=0xd), rows_order(0x78, 6, 2))
    put_tiles(tiles, render(PICK[1], 80, 16, 8, 7, shine=0xd), rows_order(0x84, 10, 2))


def blit_map(streams, tiles_addr, tile_base, pool, map_addr, map_rows, img, blank=0):
    """draws img through a tile map: map_rows = [(offset of the row in the map stream,
    number of cells)]; each 8x8 cell of img with pixels gets a tile of pool (stream tile
    numbers, VRAM tile = tile_base + n), empty cells the blank tile; the map words keep
    their high bits (palette, priority)"""
    tiles, tmap = streams.get(tiles_addr), streams.get(map_addr)
    pool = list(pool)
    for ty, (off, cells) in enumerate(map_rows):
        for tx in range(cells):
            block = [r[tx * 8:tx * 8 + 8] for r in img[ty * 8:ty * 8 + 8]]
            i = off + 2 * tx
            word = tmap[i] << 8 | tmap[i + 1]
            if any(any(r) for r in block):
                if not pool:
                    raise SystemExit('blit_map: out of tiles')
                t = pool.pop(0)
                gfx.tile_put(tiles, t, block)
                word = (word & 0xe000) | (tile_base + t)
            else:
                word = (word & 0xe000) | blank
            tmap[i:i + 2] = word.to_bytes(2, 'big')
    for t in pool:                              # the tiles left over: empty
        gfx.tile_put(tiles, t, [[0] * 8 for _ in range(8)])


CONTINUE = "CONTINUE?"


def apply_gameover(streams):
    # コンティニューするかい？ under the game over countdown: 24 x 2 cells, map in stream
    # 0xcc655 at 0x3fc and 0x42c, tiles 0x35f-0x38b of stream 0xcca17 (VRAM tile 0x100 on)
    img = render(CONTINUE, 192, 16, 0xf, 0x1)
    blit_map(streams, 0xcca17, 0x100, range(0x25f, 0x28c), 0xcc655, [(0x3fc, 24), (0x42c, 24)], img)


TINY = {        # 3x5 capitals for the tower's tiny "you are here" icon
    'Y': ["#.#", "#.#", ".#.", ".#.", ".#."],
    'O': ["###", "#.#", "#.#", "#.#", "###"],
    'U': ["#.#", "#.#", "#.#", "#.#", "###"],
    'A': [".#.", "#.#", "###", "#.#", "#.#"],
    'R': ["##.", "#.#", "##.", "#.#", "#.#"],
    'E': ["###", "#..", "##.", "#..", "###"],
    'H': ["#.#", "#.#", "###", "#.#", "#.#"],
    'C': ["###", "#..", "#..", "#..", "###"],
    'I': ["###", ".#.", ".#.", ".#.", "###"],
    'N': ["##.", "#.#", "#.#", "#.#", "#.#"],
}


def apply_chain(streams):
    # れんさ next to the chain count in play: a 3x1 sprite, tiles 0x78-0x7a of stream
    # 0x83f2b (VRAM 0x378); colour 6 with a dark (2) shadow, like the kana
    img = [[0] * 24 for _ in range(8)]
    x0 = 1
    for k, ch in enumerate("CHAIN"):
        for y, row in enumerate(TINY[ch]):
            for x, c in enumerate(row):
                if c == '#':
                    xx, yy = x0 + 4 * k + x, 1 + y
                    img[yy][xx] = 6
                    for dy, dx in ((1, 0), (0, 1), (1, 1)):
                        if img[yy + dy][xx + dx] == 0:
                            img[yy + dy][xx + dx] = 2
    put_tiles(streams.get(0x83f2b), img, [[0x78, 0x79, 0x7a]])


def apply_here(streams):
    # ここにいる (the tower strip's marker of where Arle is): a 24x24 icon, 3x3 tiles from
    # 0x1b of stream 0xc8503, column by column; white frame (f), dark inside (1)
    img = [[0xf] * 24 for _ in range(24)]
    for y in range(1, 23):
        for x in range(1, 23):
            img[y][x] = 1
    for line, word in enumerate(("YOU", "ARE", "HERE")):
        w = 4 * len(word) - 1
        x0, y0 = (24 - w) // 2, 3 + 6 * line
        for k, ch in enumerate(word):
            for y, row in enumerate(TINY[ch]):
                for x, c in enumerate(row):
                    if c == '#':
                        img[y0 + y][x0 + 4 * k + x] = 0xa
    put_tiles(streams.get(0xc8503), img, sprite_order(0x1b, 3, 3, 1))


ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'gfx')


def apply_entry(streams):
    # 参加者募集中 over the entry screen: a 36 x 6 block at 0x2a4 of the map stream 0xff8d4,
    # tiles of stream 0xca599 (the map holds the stream's tile numbers)
    import png
    img = png.read(os.path.join(ASSETS, 'players_wanted.png'))
    gfx.replace_block(streams.get(0xca599), streams.get(0xff8d4), 0x2a4, 36, 6, img)
    # ひとり / ふたり / さんにん / よにん + でぷよぷよ ("<n> players' Puyo Puyo") above it:
    # 6-row blocks of the same map, put side by side on the screen
    blocks = [(off, w, 6, png.read(os.path.join(ASSETS, name + '.png')), None)
              for off, w, name in ((0x454, 12, 'count_1p'), (0x4e4, 12, 'count_2p'),
                                   (0x574, 16, 'count_3p'), (0x634, 12, 'count_4p'),
                                   (0x6c4, 20, 'puyo_puyo'))]
    gfx.replace_blocks(streams.get(0xca599), streams.get(0xff8d4), blocks)


SLOGAN = "COURAGE AND LOVE"


def apply_aids(streams):
    # 勇気と愛気 under the Act Against AIDS logo: 20 x 3 cells at 0x604 of the screen map
    # (stream 0x3eaff, 40 wide), tiles of stream 0x3ee26; grey (b) on white (f), in the
    # thin capitals of the text font
    import font
    glyphs = font.font()
    img = [[0xf] * 160 for _ in range(24)]
    x0 = (160 - 8 * len(SLOGAN)) // 2
    for k, ch in enumerate(SLOGAN):
        for y, row in enumerate(glyphs[ord(ch)]):
            for x in range(8):
                if row >> (7 - x) & 1:
                    img[4 + y][x0 + 8 * k + x] = 0xb
    gfx.replace_block(streams.get(0x3ee26), streams.get(0x3eaff), 0x604, 20, 3, img,
                      row_stride=40, background=0xf, blank=0x01)


ALL_CLEAR = "ALL CLEAR"


def apply_allclear(streams):
    # 全消し in the tutorial's ALL CLEAR page: the box inside is 12 x 3 cells at 0x270 of
    # the map stream 0x45503 (rows 14 words apart), tiles of the tutorial stream 0x91545;
    # yellow (a) outlined (1), the bottom of each letter darker (9)
    img = [[0] * 96 for _ in range(8)] + render(ALL_CLEAR, 96, 16, 0xa, 0x1)
    for x in range(96):          # (the text on cell rows 1 and 2 only: there are 20 tiles)
        for y in range(23, -1, -1):
            if img[y][x] == 0xa:
                img[y][x] = 0x9
                break
    gfx.replace_block(streams.get(0x91545), streams.get(0x45503), 0x270, 12, 3, img,
                      row_stride=14, blank=0x1c)


def apply_crossed(streams, plain):
    # the crossed-out 乱入可能 of the tutorial's JOINING IN page: its middle 6 x 2 tiles
    # (0x19a-0x19f, 0x1a0-0x1a5 of stream 0x91545) are the sign's middle with a red X;
    # the X (the pixels where they differ from the plain sign's tiles 0x14e-0x153,
    # 0x156-0x15b) goes over the English sign
    tiles = streams.get(0x91545)
    crossed = [list(range(0x19a, 0x1a0)), list(range(0x1a0, 0x1a6))]
    orig_plain = [list(range(0x14e, 0x154)), list(range(0x156, 0x15c))]
    for r in range(2):
        for c in range(6):
            xp = gfx.tile_get(streams.original(0x91545), crossed[r][c])
            pp = gfx.tile_get(streams.original(0x91545), orig_plain[r][c])
            new = [row[8 + 8 * c:16 + 8 * c] for row in plain[8 * r:8 * r + 8]]
            out = [[xp[y][x] if xp[y][x] != pp[y][x] else new[y][x] for x in range(8)] for y in range(8)]
            gfx.tile_put(tiles, crossed[r][c], out)


SERVICE = (   # the service menu's Japanese words in romaji, same lengths
    (b"^3SOUSAI", b"^3OFFSET"),
    (b"^3RULE HENKA", b"^3RULE SET  "),
    (b"RANNYU OFF BUTTON", b"NO JOIN-IN BUTTON"),
    (b"^3RANNYU\xfe", b"^3JOINS \xfe"),
)


def apply_service(prog):
    for old, new in SERVICE:
        assert len(old) == len(new)
        i = prog.find(old)
        if i < 0 or prog.find(old, i + 1) >= 0:
            raise SystemExit('service text %r: not found once' % old)
        prog[i:i + len(new)] = new


BADGE = "JOIN!"


def apply_badge(streams):
    # 参加 on the red badge the left rabbit holds on the entry screen: its map is 10 x 8
    # cells at 0x1f4 of the map stream 0xff8d4 (rows 10 words apart), tiles of stream
    # 0xca599. The kanji (white f, shaded a/b/4/5 on the red 3) are painted over with red,
    # then the English drawn in white outlined with 5
    tiles, tmap = streams.get(0xca599), streams.get(0xff8d4)
    img = gfx.block_pixels(tiles, tmap, 0x1f4, 10, 8, 10)
    for y in range(13, 50):
        row = img[y]
        inside = [x for x in range(9, 71) if row[x] == 3]      # (inside the rim)
        if not inside:
            continue
        for x in range(inside[0], inside[-1] + 1):
            if row[x] in (0xf, 0xa, 0xb, 0x4, 0x5):
                row[x] = 3
    text = render(BADGE, 56, 16, 0xf, 0x5)
    for y in range(16):
        for x in range(56):
            if text[y][x]:
                img[23 + y][12 + x] = text[y][x]
    gfx.write_block_pixels(tiles, tmap, 0x1f4, 10, 8, 10, img)


# the rule select screen (map stream 0xfbd02, tiles of stream 0xfbf8f; the map holds the
# stream's tile numbers): its title, 33 x 3 cells at 0x8c0, and the box's line for each
# rule, 28 x 2 cells at 0x986 (ojama puyo score) and 24 x 2 cells at 0xa0e (rows 28 words
# apart; the plain rule), both centred on screen, in white (f) with the words that matter
# in yellow (c); [] mark the yellow part
RULE_LINES = ((0x986, 28, "Nuisance Puyo [score points]!"), (0xa0e, 24, "Plain [Puyo Puyo] battle!"))


def rule_line(text, cells):
    import font
    glyphs = font.font()
    plain = text.replace('[', '').replace(']', '')
    img = [[0] * (8 * cells) for _ in range(16)]
    x = (8 * cells - 8 * len(plain)) // 2
    colour = 0xf
    for ch in text:
        if ch in '[]':
            colour = 0xc if ch == '[' else 0xf
            continue
        for y, row in enumerate(glyphs[ord(ch)]):
            for i in range(8):
                if row >> (7 - i) & 1:
                    img[y][x + i] = colour
        x += 8
    return img


def apply_rules(streams):
    import png
    title = png.read(os.path.join(ASSETS, 'choose_rule.png'))
    blocks = [(0x8c0, 33, 3, title, None)]
    blocks += [(off, cells, 2, rule_line(text, cells), 28) for off, cells, text in RULE_LINES]
    gfx.replace_blocks(streams.get(0xfbf8f), streams.get(0xfbd02), blocks)
