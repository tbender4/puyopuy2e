# Puyo Puyo 2 (Sega C2): technical notes

Working notes from the analysis of the MAME set `puyopuy2` (Compile 1994, Sega C2 board).

## Program

`epr-17241.ic32` (even bytes) and `epr-17240.ic31` (odd bytes) make the 1 MB 68000
program (`tools/romset.py`). `epr-17239.ic4` is the UPD7759 sound ROM.

## Text

The text is not compressed (`tools/text.py`): 16-bit codes, one per 16x16 glyph of a
1 bpp font in the ROM (glyph of code `c` at `0x92c65 + c * 32`). The font holds only the
glyphs the text uses (kana and kanji, in order of first use). Line breaks are `ff08 pos`,
the end of a page `ffff`.

Two kinds of text, all in `0x1bf94`-`0x1d630`:

- the character profiles shown in a box before each match (38, pointer table at `0x1bf0c`);
- the attract mode's tutorial pages (きほんそうさのひみつ, おじゃまぷよのひみつ, そうさいのひみつ,
  ぜんけしのひみつ, ...).

The game draws a page by giving each distinct glyph two VRAM tiles (8x16 each, tiles
`0x780` on).

## Compressed graphics

Most tiles are packed with a small LZ (`tools/lz.py`, decompressor at `0x1e72`):

- `00` ends the stream;
- `01`-`7f`: that many literal bytes follow;
- `80 | k`, `b`: copy `k + 3` bytes from a 256-byte ring buffer, starting `b + 1` bytes
  back.

The streams are loaded through lists of 6-byte entries (flags, count, VRAM destination,
16-bit offset of the stream inside the list's 64 KB bank; `0xff` ends a list), read at
`0x1b70`. `tools/lz.py` packs the same format; on every stream checked it gives back the
original size exactly.

## Japanese on screen (found so far)

Graphics: 参加者募集中, 参加, ひとりでぷよぷよ, 乱入可能, 相手をえらんでね, ここにいる,
コンティニューするかい？ (game over), 全消し, the tutorial page titles, 勇気と愛気 under the
Act Against AIDS logo, the title logo ぷよぷよ通.
