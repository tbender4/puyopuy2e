"""Saturn staff roll: the five 40x50 VDP2 credit maps (one 320x2000 scroll) in the ending
scene blocks of PUYOSHOW.FLD, redrawn in English. Roles and names as MobyGames credits them
(Saturn credits page); credited aliases stay aliases, in western order."""
import game_arts as ga
import gfx, md_credits

# PUYOSHOW entry -> (scene block index in the container, first credit map part)
ENDINGS = {149: (5, 10), 151: (1, 7), 153: (3, 9), 155: (5, 12)}
PAGES, W, H = 5, 40, 50
LEFT, NAME, RIGHT, PITCH = 16, 32, 184, 16

# (heading, [(left, right)]) in screen order; '' = empty cell, a heading of None continues
ROLL = (
    ('Producer', [('MOO Niitani', '')]),
    ('Director', [('MACHAO A', '')]),
    ('Music', [('LMS Music', ''), ('Katsumi Tanaka', ''), ('BA.M', 'Einosuke Nagao'),
               ('Tsuyoshi Matsushima', 'Yamasaki')]),
    ('Featured Songs', [('"Zutto/ soba ni/ iru yo"', ''),
                        ('Lyrics, Comp., Arr.', 'Katsumi Tanaka'),
                        ('Vocal', 'Katsumi Tanaka'), ('', 'Kazuhiro Kōnoue'), ('', '(NEC Avenue)'),
                        ('"Shakunetsu no faiyādansu"', ''),
                        ('Lyrics, Comp., Arr., Vocal', ''), ('', 'Katsumi Tanaka'), ('', '(NEC Avenue)')]),
    ('Planner', [('Kengo Morita (24)', '')]),
    ('Scenario', [('5-5-shiki Uemyzo', 'Kasumi Hakuryūhō'), ('Kenji Kawakita', 'Kengo Morita (24)')]),
    ('Voice Actors', []),
    ('  Arle', [('Mami Inoue', '')]),
    ('  Carbuncle', [('MOO Niitani', '')]),
    ('  All Enemies (by real name)', [
        ('Yasutoshi S. Akiyama', 'A.Kizuki'), ('Inazō Kizukuri', 'Winner'),
        ('Kenji Daoh', 'Kazuto Hisoku'), ('Kenji Kawakita', 'Kazuhiro Kōnoue'),
        ('Dai Gattai Kodama SS', 'Shimeharidzuru'), ('Kemi', 'Sonchō Sawa'),
        ('Kagetora', 'Kyoryu Tansha'), ('Amon', 'Murasaki Syu'), ('Jemini', 'Wa-kun'),
        ('Migaku', 'Guts Nakamatsu'), ('Okogeyukapihime', 'Tachibana'), ('Yamasaki', 'Takin'),
        ('Watanabe (Flame) KIT', 'Kerol')]),
    ('Storyboard', [('Kenji Kawakita', 'RIU'), ('Gennosuke Yumi', 'Nekonyan'),
                    ('Jusaburo Sawatari', 'Kemi'), ('Kengo Morita (24)', '')]),
    ('Drawings', [('RIU', 'Kenji Kawakita'), ('Dai Gattai Kodama SS', 'Nekonyan'),
                  ('Jusaburo Sawatari', 'Kemi')]),
    ('Opening', [('Junus', 'Takuya Hirata'), ('RIU', '')]),
    ('Ending', [('Kenji Kawakita', 'RIU')]),
    ('Recording', [('Studio 5150', '')]),
    ('Casting', [('Sonchō Sawa', 'Yasutoshi S. Akiyama')]),
    ('Manual', [('Fukusaburo Kido', 'Kazuto Hisoku')]),
    ('Package', [('Ichi', '')]),
    ('Cooperation', [('Tatsuo Nakanishi', 'Katsumi Enami')]),
    ('Production Cooperation', []),
    ('  Game Arts', [('Yoichi Miyaji', ''), ('Takuya Osamura', 'Tomoyuki Shimada')]),
    ('  Bits Laboratory', [('Satoru Miyazaki', ''), ('Motoyuki Kanayama', 'Yoshiaki Tsuruoka'),
                           ('Naozumi Honma', 'Masashi Inde'), ('Makoto Ishikawa', '')]),
    ('  Script Arts', [('Kenichiro Ohmi', ''), ('Akira Kojima', 'Hiroyuki Akabane'),
                       ('Shingo Tsuda', '')]),
    ('  Ikusabune Planning Design Studio', [('Toshio Akashi', ''), ('Ken-ichi Iwaida', '')]),
    ('Special Thanks', [('WAO ISSE', '')]),
    ('Co-Producer', [('Kenji Kawakita', '')]),
    ('Supervisor', [('Jemini', '')]),
    ('Produced by', [('Compile', '')]),
)


def layout():
    """[(y, x, text)] of the English roll"""
    items, y = [], 0
    for heading, rows in ROLL:
        sub = heading.startswith('  ')
        if not sub and items:
            y += PITCH                          # blank row between sections
        items.append((y, LEFT + (8 if sub else 0), heading.strip()))
        y += PITCH
        for left, right in rows:
            if right and RIGHT + len(md_credits.text_columns(right)) > 8 * W:     # too wide: own row
                if left:
                    items.append((y, NAME, left))
                    y += PITCH
                left, right = right, ''
            if left:
                items.append((y, NAME, left))
            if right:
                items.append((y, RIGHT, right))
            y += PITCH
    assert items[-1][0] + PITCH <= PAGES * 8 * H, 'English staff roll too tall'
    return items                                # starts on row 0, as the Japanese roll does


def roll_image():
    img = [[0] * (8 * W) for _ in range(PAGES * 8 * H)]
    items = layout()
    right_rows = {y for y, x, _ in items if x == RIGHT}
    for y, x, text in items:
        cols = md_credits.text_columns(text)
        limit = RIGHT - 4 if x < RIGHT and y in right_rows else 8 * W
        assert x + len(cols) <= limit, 'staff roll line too wide: ' + text
        for c, col in enumerate(cols):
            for r, v in enumerate(col):
                if v:
                    img[y + r][x + c] = 15
    return img


def apply(puyoshow_ents):
    img = roll_image()
    for entry, (block, first) in ENDINGS.items():
        head, blocks, order = ga.container_parse(puyoshow_ents[entry])
        scene = ga.scene_parse(blocks[block])
        tiles = bytearray(ga.lzss_decompress(scene['parts'][1])[0])
        maps = [ga.map_decode(scene['parts'][first + p], 0)[:3] for p in range(PAGES)]
        cell = maps[0][2][0] & 0xF07F0000      # palette bits of the credit pages
        assert all(m[:2] == (W, H) for m in maps)
        others = {c & 0x7fff for j, part in enumerate(scene['parts'][2:], 2)
                  if not first <= j < first + PAGES for c in map_cells(part)}
        free = sorted({c & 0x7fff for m in maps for c in m[2]} - others - {0})
        made = {bytes(32): 0}
        for p in range(PAGES):
            cells = []
            for ty in range(H):
                for tx in range(W):
                    block8 = [row[tx * 8:tx * 8 + 8] for row in img[(p * H + ty) * 8:(p * H + ty) * 8 + 8]]
                    data = bytearray(32)
                    gfx.tile_put(data, 0, block8)
                    key = bytes(data)
                    if key not in made:
                        assert free, 'staff roll: not enough free tiles in PUYOSHOW %d' % entry
                        t = free.pop(0)
                        tiles[t * 32:t * 32 + 32] = key
                        made[key] = t
                    cells.append(cell | made[key])
            scene['parts'][first + p] = ga.map_encode(W, H, cells)
        for t in free:                          # leftover Japanese-only tiles
            tiles[t * 32:t * 32 + 32] = bytes(32)
        scene['parts'][1] = ga.lzss_compress(bytes(tiles))
        blocks[block] = ga.scene_pack(scene)
        puyoshow_ents[entry] = ga.container_pack(head, blocks, order)


def map_cells(part):
    """cells of a map part, or nothing for the non-map tables"""
    try:
        w, h, cells, end = ga.map_decode(part, 0)
    except Exception:
        return []
    return cells if 0 < w <= 128 and 0 < h <= 128 and end <= len(part) else []
