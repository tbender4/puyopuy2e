"""Saturn Milestone D: Game Arts cutscene art (EFFECT.DAT, PUYOSHOW.FLD) in English."""
import functools, os
import game_arts as ga
import font, gfx, labels, md_credits, saturn_credits

EFFECT_CAPTION = 3      # EFFECT.DAT part: the 64x15 30分経過 caption map (palette bank 1, colour 15)


def _draw_scaled(img, mask, scale, x0, y0, colour):
    """draw mask into img blown up scale times at (x0, y0)"""
    for y, row in enumerate(mask):
        for x, v in enumerate(row):
            if v:
                for dy in range(scale):
                    img[y0 + y * scale + dy][x0 + x * scale:x0 + (x + 1) * scale] = [colour] * scale


def _sprite_get(pixels, addr, w, h):
    return [[pixels[addr * 8 + (y * w + x) // 2] >> (4 if x % 2 == 0 else 0) & 15 for x in range(w)] for y in range(h)]


def _sprite_put(pixels, addr, img):
    w = len(img[0])
    for y, row in enumerate(img):
        for x in range(0, w, 2):
            pixels[addr * 8 + (y * w + x) // 2] = row[x] << 4 | row[x + 1]


@functools.lru_cache(None)
def _font6():
    return font.load_bdf(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'font', 'spleen-6x12.bdf'))


def _small_text(s, colour=1, tall=False):
    """columns of s in Spleen 6x12 (12 rows; tall: row 5 doubled, 13 rows), glyphs trimmed to
    their ink + 1 px, spaces 3 px"""
    cols = []
    for ch in s:
        if ch == ' ':
            cols += [[0] * (13 if tall else 12)] * 3
            continue
        rows = _font6()[ord(ch)]
        rows = rows[:6] + rows[5:] if tall else rows
        ink = [c for c in range(8) if any(r >> (7 - c) & 1 for r in rows)]
        for c in range(ink[0], ink[-1] + 1):
            cols.append([colour if rows[y] >> (7 - c) & 1 else 0 for y in range(len(rows))])
        cols.append([0] * len(rows))
    return cols[:-1]


def _text_mask(text, gap=1):
    masks = [labels.letter_mask(ch) for ch in text]
    out = [[] for _ in range(13)]
    for k, m in enumerate(masks):
        for y in range(13):
            out[y] += ([0] * gap if k else []) + m[y]
    return out


def _redraw_map(scene, part, img, colour_bits, grow=0):
    """redraw map `part` as img: unchanged cells keep their words (flips included), changed
    ones get tiles freed by the old art (tiles no kept cell and no other map uses)"""
    tiles = bytearray(ga.lzss_decompress(scene['parts'][1])[0])
    w, h, cells, _ = ga.map_decode(scene['parts'][part], 0)
    old = _map_pixels(tiles, w, h, cells)
    cut = lambda im, tx, ty: [row[tx * 8:tx * 8 + 8] for row in im[ty * 8:ty * 8 + 8]]
    keep = [cut(img, k % w, k // w) == cut(old, k % w, k // w) for k in range(w * h)]
    used = {c & 0x7fff for k, c in enumerate(cells) if keep[k]}
    for j, p in enumerate(scene['parts'][2:], 2):
        if j != part:
            used |= {c & 0x7fff for c in saturn_credits._cells(p)}
    tiles += bytes(32 * grow)
    blank = next(t for t in range(len(tiles) // 32) if not any(tiles[t * 32:t * 32 + 32]))
    used.add(blank)                             # blank cells must stay blank
    free = sorted(({c & 0x7fff for c in cells} | set(range(len(tiles) // 32 - grow, len(tiles) // 32))) - used)
    made, new = {bytes(32): blank}, []
    for k in range(w * h):
        if keep[k]:
            new.append(cells[k])
            continue
        data = bytearray(32)
        gfx.tile_put(data, 0, cut(img, k % w, k // w))
        if bytes(data) not in made:
            t = free.pop(0)                     # IndexError: the new art needs more tiles than the old
            tiles[t * 32:t * 32 + 32] = data
            made[bytes(data)] = t
        new.append(colour_bits | made[bytes(data)])
    for t in free:
        tiles[t * 32:t * 32 + 32] = bytes(32)
    while grow and len(tiles) // 32 > blank + 1 and not any(tiles[-32:]):     # unused added tiles
        del tiles[-32:]
        grow -= 1
    scene['parts'][1] = ga.lzss_compress(bytes(tiles))
    scene['parts'][part] = ga.map_encode(w, h, new)


def apply_effect(effect):
    """EFFECT.DAT: 30分経過 -> THIRTY MINUTES / LATER in the title font, 4x (8 px strokes like the kanji)"""
    scene = ga.scene_parse(effect)
    w, h, cells, _ = ga.map_decode(scene['parts'][EFFECT_CAPTION], 0)
    assert (w, h) == (64, 15)
    img = [[0] * (w * 8) for _ in range(h * 8)]
    for line, y0 in (('THIRTY MINUTES', 4), ('LATER', 64)):     # the title font has no digits
        m = _text_mask(line)
        x0 = (w * 8 - 4 * len(m[0])) // 2 // 4 * 4     # on the 4 px grid: few distinct tiles
        _draw_scaled(img, m, 4, x0, y0, 15)
    _redraw_map(scene, EFFECT_CAPTION, img, max(cells) & 0x007F0000)    # palette bank bits
    return ga.scene_pack(scene)


SLOT = 45056            # work RAM slot of a regular PUYOSHOW sprite set
# PUYOSHOW entry -> {sprite: lines}: Nomi's signs (ここにいる as I'M HERE, as on the tower; ってば as I SAID I'M HERE!)
SIGNS = {
    69: {15: ("I'M", 'HERE'), 16: ('I SAID', "I'M HERE!")},
    71: {14: ("I'M", 'HERE'), 15: ('SHOULD', 'BE HERE'), 16: ('FOUND', 'IT!'), 17: ('MAYBE', "I'M HERE")},
}


def _sign(px, lines, palette):
    """redraw a sign in the title font with a black outline, lit from the top: its brightest
    colour on the top rows of each line, then the middle, then the darkest"""
    h, w = len(px), len(px[0])
    used = {v for row in px for v in row if v > 1}
    by_light = sorted(used, key=lambda v: -sum(palette[v]))
    ramp = (by_light[0], by_light[1], by_light[len(by_light) // 2])   # the bright half, like the kana
    out = [[0] * w for _ in range(h)]
    pitch = (h - 2) // len(lines)
    for k, line in enumerate(lines):
        m = _text_mask(line, 1)
        x0 = max(1, (w - len(m[0])) // 2)       # FOUND fills 40 px: its right outline is clipped
        y0 = 1 + k * pitch + (pitch - 13) // 2
        for y in range(13):
            for x, v in enumerate(m[y]):
                if v and x0 + x < w:
                    out[y0 + y][x0 + x] = ramp[0 if y < 4 else 1 if y < 9 else 2]
    return labels.ring(out, 1, set(ramp))


def apply_signs(ents):
    for entry, signs in SIGNS.items():
        table, pixels = ga.sprites_parse(ents[entry])
        palette = ga.sprites_palette(ents[entry])
        for k, lines in signs.items():
            _, w, h, addr = table[k]
            _sprite_put(pixels, addr, _sign(_sprite_get(pixels, addr, w, h), lines, palette[table[k][0]:]))
        ents[entry] = ga.sprites_pack(ents[entry], pixels)
        assert len(ents[entry]) <= SLOT, 'PUYOSHOW %d: %d bytes' % (entry, len(ents[entry]))


# PUYOSHOW 9 (Cockadoodle): the two vertical caption strips, as wrapped horizontal lines
CAPTIONS = {9: {30: "Why would you say something like that?! It's terrible! Just terrible!",
                31: "Sorry, but it's the Puyo Under- world with you!"}}
# where the Japanese text sat in each strip: (centre x, centre y)
CAPTION_CENTRE = {30: (26, 95), 31: (22, 112)}
# caption 31's lines already touch its sprite's left edge; the sprite's screen position comes from
# the skit script (widening it grows it to the right), so moving it further left needs a script edit
CAPTION_WIDTH = {}
# script entry 8 shows caption 30 for 0x78 frames, then nothing for about 117 frames before
# caption 31: hold it the whole time (English takes longer to read)
CAPTION_HOLD = (8, bytes.fromhex('01091e7800'), bytes.fromhex('01091eee00'))


def _wrap(text, width):
    lines, cur = [], ''
    for word in text.split(' '):
        trial = (cur + ' ' + word).strip() if not cur.endswith('-') else cur + word
        if cur and len(md_credits._text(trial)) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur]


def _caption(w, h, text, fill, edge, centre):
    out = [[0] * w for _ in range(h)]
    cx, cy = centre
    lines = _wrap(text, w - 2)
    y0 = cy - 8 * len(lines)
    for k, line in enumerate(lines):
        cols = md_credits._text(line)
        x0 = min(max(1, cx - len(cols) // 2), w - 1 - len(cols))   # near cx, inside the strip
        for x, col in enumerate(cols):
            for y, v in enumerate(col):
                if v:
                    out[y0 + 16 * k + y][x0 + x] = fill
    return labels.ring(out, edge, {fill})


def apply_captions(ents):
    for entry, caps in CAPTIONS.items():
        table, pixels = ga.sprites_parse(ents[entry])
        b = ents[entry]
        for k, text in caps.items():
            _, w, h, addr = table[k]
            W = CAPTION_WIDTH.get(k, w)
            img = _caption(W, h, text, 7, 8, CAPTION_CENTRE[k])     # white, black edge
            if W == w:
                _sprite_put(pixels, addr, img)
            else:
                data = bytearray(W * h // 2)
                _sprite_put(data, 0, img)
                b = ga.sprites_resize(b, pixels, k, W, h, data)
        ents[entry] = ga.sprites_pack(b, pixels)
        assert len(ents[entry]) <= SLOT, 'PUYOSHOW %d: %d bytes' % (entry, len(ents[entry]))
    entry, old, new = CAPTION_HOLD
    assert ents[entry].count(old) == 1
    ents[entry] = ents[entry].replace(old, new)


AIDS = 157              # PUYOSHOW entry: the Act Against AIDS card (one 40x28 scene map)
AIDS_TEXT = ('COURAGE AND LOVE', ('Learn about AIDS', 'Prevent AIDS', 'Support people with AIDS'))


def _map_pixels(tiles, w, h, cells):
    img = [[0] * (w * 8) for _ in range(h * 8)]
    for k, c in enumerate(cells):
        px = gfx.tile_get(tiles, c & 0x7fff)
        for y in range(8):
            for x in range(8):
                img[k // w * 8 + (7 - y if c >> 31 & 1 else y)][k % w * 8 + (7 - x if c >> 30 & 1 else x)] = px[y][x]
    return img


def apply_aids(ents):
    """勇気と愛気 and the three エイズ… bullets -> the arcade's COURAGE AND LOVE and English bullets
    (no official English exists for エイズとつきあおう; 'Support people with AIDS')"""
    head, blocks, order = ga.container_parse(ents[AIDS])
    scene = ga.scene_parse(blocks[0])
    tiles = ga.lzss_decompress(scene['parts'][1])[0]
    w, h, cells, _ = ga.map_decode(scene['parts'][2], 0)
    img = _map_pixels(tiles, w, h, cells)
    paper, ink = 15, 10                         # the card's white and black
    for y in range(146, h * 8):                 # the Japanese text: rows 147-201
        img[y] = [paper] * (w * 8)
    # as the Japanese: the slogan (rows 147-165) centred on x 157, the three lines a size smaller
    # (Spleen 6x12 a row taller, capitals 9 rows) centred on 172/184/195, ending at x 230 as the
    # Japanese does, 10 px before the bar under the logo
    slogan = _text_mask(AIDS_TEXT[0], 1)
    x0 = 157 - len(slogan[0]) // 2
    for y, row in enumerate(slogan):
        for x, v in enumerate(row):
            if v:
                img[150 + y][x0 + x] = ink
    lines = [_small_text(t, tall=True) for t in AIDS_TEXT[1]]
    left = 230 - (9 + max(map(len, lines)))     # bullet 5 px + 4 px gap; ends at x 230 like the Japanese
    for cols, centre in zip(lines, (172, 184, 195)):
        for y in range(5):                      # the bullet, a 5x5 disc
            for x in range(5):
                if (x - 2) ** 2 + (y - 2) ** 2 <= 5:
                    img[centre - 2 + y][left + x] = ink
        for x, col in enumerate(cols):
            for y, v in enumerate(col):
                if v:
                    img[centre - 6 + y][left + 9 + x] = ink    # capitals on glyph rows 1-9
    _redraw_map(scene, 2, img, max(cells) & 0x007F0000, grow=256)   # the card is alone on screen
    blocks[0] = ga.scene_pack(scene)
    ents[AIDS] = ga.container_pack(head, blocks, order)


SCHEZO = 107            # PUYOSHOW entry: Arle calls Schezo ヘンタイ, the sign flips to タイヘン
SCHEZO_SIGNS = {52: 'PERVERT', 53: 'TERRIBLE'}
SCHEZO_NOTE = ('TL: HENTAI (PERVERT)', 'FLIPS INTO', 'TAIHEN (TERRIBLE)')
SCHEZO_STYLE = 'b'      # a: kana + TL note, b: small English above the kana, c: both
# the sign is drawn centred on its actor (measured in game: a taller sprite grows both ways),
# whose centre is about (220, 93) on screen; the note goes to the bottom right of the screen
NOTE_DX, NOTE_BOTTOM = 64, 112          # note right edge / bottom from the sign's centre: on the floor between Arle and Schezo


def _spleen(img, text, x0, y0, fill, edge):
    """draw text in Spleen 8x16 (capital rows 2-11) at (x0, y0), with an edge ring"""
    layer = [[0] * len(img[0]) for _ in img]
    for x, col in enumerate(md_credits._text(text)):
        for y, v in enumerate(col):
            if v:
                layer[y0 + y][x0 + x] = fill
    layer = labels.ring(layer, edge, {fill})
    for y, row in enumerate(layer):
        for x, v in enumerate(row):
            if v:
                img[y][x] = v


def apply_schezo(ents, style=None):
    """keep the kana (the swap is the joke); b: PERVERT / TERRIBLE small above them, a: a TL
    note at the bottom right instead, c: both. The canvas grows symmetrically so the kana stay put."""
    style = style or SCHEZO_STYLE
    b = ents[SCHEZO]
    table, pixels = ga.sprites_parse(b)
    for k, word in SCHEZO_SIGNS.items():
        _, w, h, addr = table[k]
        old = _sprite_get(pixels, addr, w, h)
        top = 12 if style in 'bc' else 0        # room for one Spleen capital line + edge
        half_h, half_w = h // 2 + top, 40
        note = style in 'ac' and k == 52       # the first sign shows once (the flipped one three times); one canvas fits the slot
        if note:
            half_h, half_w = NOTE_BOTTOM + 2, NOTE_DX + 2
        W, H = 2 * half_w, 2 * half_h
        W += -W % 8
        img = [[0] * W for _ in range(H)]
        ox, oy = W // 2 - w // 2, H // 2 - h // 2
        for y in range(h):
            img[oy + y][ox:ox + w] = old[y]
        if style in 'bc':
            cols = len(md_credits._text(word))
            _spleen(img, word, W // 2 - cols // 2, oy - 13, 12, 1)    # the kana's yellow, black edge
        if note:
            for n, line in enumerate(SCHEZO_NOTE):
                cols = len(md_credits._text(line))
                _spleen(img, line, W // 2 + NOTE_DX - cols - 1, H // 2 + NOTE_BOTTOM - 13 * (3 - n) - 2, 15, 1)
        data = bytearray(W * H // 2)
        _sprite_put(data, 0, img)
        b = ga.sprites_resize(b, pixels, k, W, H, data)
    ents[SCHEZO] = ga.sprites_pack(b, pixels)
    assert len(ents[SCHEZO]) <= SLOT
