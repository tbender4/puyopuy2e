"""Builds the English program from the original one (tools/make_puyopuy2e.py runs it)."""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'text'))
import font, text, script_en, gfx, titles, labels, logo, linkmsg


def patch_file(name):
    return open(os.path.join(ROOT, 'patch', name), 'rb').read()


def jmp(prog, at, to, length):
    """jmp to.l at at, the rest of length nops"""
    code = struct.pack('>HI', 0x4ef9, to) + b'\x4e\x71' * ((length - 6) // 2)
    prog[at:at + length] = code


def build(prog):
    prog = bytearray(prog)
    # text engine: 8x16 glyphs
    eng = patch_file('text8.bin')
    assert len(eng) <= 0x17676 - 0x17538
    prog[0x17538:0x17538 + len(eng)] = eng
    # font
    prog[text.FONT_BANK_ENTRY:text.FONT_BANK_ENTRY + 2] = struct.pack('>H', text.FONT & 0xffff)
    for code, rows in font.font().items():
        prog[text.FONT + code * 16:text.FONT + code * 16 + 16] = rows
    # page openers: indirect English text
    hooks = patch_file('hooks.bin')
    prog[text.HOOKS:text.HOOKS + len(hooks)] = hooks
    jmp(prog, 0x171b4, text.HOOKS, 14)          # op 03
    jmp(prog, 0x1720c, text.HOOKS + 0x10, 24)   # op 0b
    used = text.apply(prog, script_en.TEXT)
    print('English text: %d bytes' % used)
    streams = gfx.Streams(prog)
    titles.apply(streams)
    labels.apply(streams)
    logo.apply(prog, streams)
    labels.apply_service(prog)
    end = linkmsg.apply(prog, streams, text.TEXT_AT + used, text.TEXT_END)
    print('join-in messages: %d bytes' % (end - text.TEXT_AT - used))
    streams.write()
    return prog
