"""The game's text and its English replacement.

Original (uncompressed, in the script at 0x1bf94-0x1d608): 16-bit codes, one per 16x16
glyph of a 1 bpp font (glyph of code c at 0x92c65 + c * 32; the font holds only the glyphs
the text uses). Control codes:
  0xff04 n      typing speed (frames per character)
  0xff08 pos    new line at pos (VRAM offset from the first character)
  0xff1c hi lo  jump to the long address hi:lo if the TURN DIRECTION switch is set
  0xffff        end of the page
The script opcodes that open a page (op 03 the tutorial window, op 0b the profile box)
take a long resume address, then the page's text.

English: 8x16 glyphs (patch/text8.s, the text engine at 0x17538), code = the ASCII code,
font at FONT. Each original page starts with 0xfffe + the long address of its English text
(patch/hooks.s), which goes at TEXT_AT on."""
import struct

FONT_BANK_ENTRY = 0x9000e       # bank 0x90000's table: the text font's 16-bit offset
FONT = 0x98300                  # glyph of code c at FONT + c * 16
HOOKS = 0x98b00
TEXT_AT = 0x98c00
TEXT_END = 0x9fff0

PROFILE_ROWS = (0x180, 0x300)   # the profile box's second and third lines
TUT_FIRST, TUT_STEP = 0x1a4, 0x180


def encode_line(s):
    for ch in s:
        if not 0x20 <= ord(ch) < 0x7f:
            raise ValueError('character %r not in the font' % ch)
    return [ord(ch) for ch in s.replace('『', '{').replace('』', '}')]


def page_words(kind, lines, address):
    """the words of one English page; address = where it will be (for IFTURN)"""
    out, row = [], 0
    if kind == 'name':
        out += encode_line('{' + lines[0] + '}')
        out += [0xff04, 0x1e, 0x0000, 0xff04, 0x01]
        lines = lines[1:]
        row = 1
    pending_jump = None
    for line in lines:
        if line == 'PAUSE':
            out += [0xff04, 0x1e, 0x0000, 0xff04, 0x01]
            continue
        if line == 'IFTURN':
            pending_jump = len(out)
            out += [0xff1c, 0, 0]
            continue
        if kind == 'tut':
            out += [0xff08, TUT_FIRST + TUT_STEP * row]
        elif row:
            out += [0xff08, PROFILE_ROWS[row - 1]]
        out += encode_line(line)
        row += 1
    out.append(0xffff)
    if pending_jump is not None:
        end = address + 2 * (len(out) - 1)          # the 0xffff
        out[pending_jump + 1], out[pending_jump + 2] = end >> 16, end & 0xffff
    return out


def apply(prog, text, at=TEXT_AT, end=TEXT_END):
    """write the English pages from at (below end), point the original pages at them; returns the bytes written"""
    start = at
    for orig, kind, lines in text:
        words = page_words(kind, lines, at)
        data = struct.pack('>%dH' % len(words), *words)
        if at + len(data) > end:
            raise SystemExit('the English text does not fit')
        prog[at:at + len(data)] = data
        prog[orig:orig + 6] = struct.pack('>HI', 0xfffe, at)
        at += len(data)
    return at - start
