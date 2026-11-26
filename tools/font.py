"""The English font: 8x16, 1 bit per pixel, one byte per row (MSB left), 16 bytes a glyph.

From Spleen 8x16 (font/spleen-8x16.bdf, BSD 2-clause, by Frederic Cambus), plus the corner
brackets 『 』 the profiles put around a name, at the codes of '{' and '}'."""
import functools, os

HERE = os.path.dirname(os.path.abspath(__file__))

BRACKET_OPEN = [0x00, 0x00, 0x7e, 0x42, 0x5e, 0x50, 0x50, 0x50,
                0x50, 0x50, 0x50, 0x50, 0x70, 0x00, 0x00, 0x00]
BRACKET_CLOSE = [0x00, 0x00, 0x0e, 0x0a, 0x0a, 0x0a, 0x0a, 0x0a,
                 0x0a, 0x0a, 0x7a, 0x42, 0x7e, 0x00, 0x00, 0x00]


def load_bdf(path):
    glyphs, code, rows, in_bitmap = {}, None, [], False
    for line in open(path, encoding='latin-1'):
        line = line.strip()
        if line.startswith('ENCODING'):
            code = int(line.split()[1])
        elif line == 'BITMAP':
            in_bitmap, rows = True, []
        elif line == 'ENDCHAR':
            in_bitmap = False
            glyphs[code] = rows
        elif in_bitmap:
            rows.append(int(line, 16))
    return glyphs


@functools.lru_cache(None)
def font():
    """{code: 16 row bytes} for the codes 0x20-0x7e"""
    bdf = load_bdf(os.path.join(HERE, '..', 'font', 'spleen-8x16.bdf'))
    out = {c: bytes(bdf[c]) for c in range(0x20, 0x7f)}
    out[ord('{')] = bytes(BRACKET_OPEN)
    out[ord('}')] = bytes(BRACKET_CLOSE)
    return out
