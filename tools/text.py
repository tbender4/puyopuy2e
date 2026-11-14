"""The game's text (uncompressed): 16-bit codes, one per 16x16 glyph of the ROM font.

  code 0x0011..       glyph (code - 0x11) of the font at FONT (32 bytes each, 1 bpp, 16 rows
                      of 16 pixels, MSB left); the font only holds the glyphs the text uses
  0xff08 pos          new line at position pos
  0xff04 n            (wait / effect, seen in the character profiles)
  0xffff              end of a page

The character profiles (shown before each match) and the attract mode's tutorial pages
(…のひみつ) are at 0x1bf94-0x1d630, behind a table of 38 long pointers at 0x1bf0c."""
FONT = 0x92c65 + 0x11 * 32 - 0x11 * 32   # glyph of code c at FONT + c * 32
TEXT_START, TEXT_END = 0x1bf94, 0x1d630
POINTERS = 0x1bf0c


def glyph_rows(prog, code):
    """the 16 rows (16-bit) of the glyph of a text code"""
    a = FONT + code * 32
    return [prog[a + 2 * y] << 8 | prog[a + 2 * y + 1] for y in range(16)]
