# Puyo Puyo 2 (Sega C2): technical notes

Notes from the analysis of the MAME set `puyopuy2` (Compile 1994, Sega C2 board) and on
how `puyopuy2e` changes it. Addresses are in the 1 MB program.

## Program

`epr-17241.ic32` (even bytes) and `epr-17240.ic31` (odd bytes) make the 1 MB 68000
program (`tools/romset.py`). `epr-17239.ic4` is the UPD7759 sound ROM, unchanged. The
protection chip (read at `$800001`) does not check the program: the modified ROM runs in
MAME 0.264 and in mame2003-plus.

## Text

The text is not compressed: 16-bit codes, one per 16x16 glyph of a 1 bpp font (glyph of
code `c` at `0x92c65 + c * 32`; the font holds only the glyphs the text uses, kana and
kanji in order of first use). Control codes:

- `ff04 n`: typing speed;
- `ff08 pos`: new line (`pos` is the VRAM offset of the line from the box's corner);
- `ff1c hi lo`: jump by the TURN DIRECTION DIP switch;
- `ffff`: end of the page.

Two kinds of pages, all in `0x1bf94`-`0x1d630`: the character profiles shown in a box
before each match (32 characters x 3 rows) and the tutorial pages of the attract mode (18
characters x 7 rows). They are opened by two script operations: op 03 (`0x171a4`, the
tutorial window) and op 0b (`0x1720a`, the profile box); both take a long resume pointer,
then the text inline.

The text task is at `0x17432`. It gets the font from the word at `0x9000e` (the table of
bank `0x90000`) and draws each glyph with the routine at `0x17538`, which keeps the codes
already drawn at `0xffaa00` and gives each new one two columns of two tiles (from the
tile number at `$38` of the task).

In `puyopuy2e`:

- `0x17538` is replaced by `patch/text8.s`: 8x16 glyphs (16 bytes, one column of two
  tiles per code), ASCII codes; code 0 draws nothing (the pause after a name);
- the font (Spleen 8x16, `{` and `}` drawn as the corner brackets 『』) is at `0x98300`,
  and `0x9000e` points at it;
- `patch/hooks.s` at `0x98b00` (jumped to from `0x171b4` and `0x1720c`): when the inline
  text starts with `0xfffe`, the long that follows is where the text really is;
- the English pages are at `0x98c00`-`0x9fff0`; each original page starts with
  `0xfffe` and a pointer to its English page.

## Compressed graphics

Most tiles and maps are packed with a small LZ (`tools/lz.py`, unpacker at `0x1e72`):

- `00` ends the stream;
- `01`-`7f`: that many literal bytes follow;
- `80 | k`, `b`: copy `k + 3` bytes from a 256-byte ring buffer, starting `b + 1` bytes
  back.

The streams are loaded through lists of 6-byte entries (flags, count, VRAM or RAM
destination, 16-bit offset of the stream inside the list's 64 KB bank; `0xff` ends a
list), read at `0x1b70`. `tools/lz.py` packs the same format; on every stream checked it
gives back the original size exactly. A stream that grows is moved to free space (`0xff`)
of its bank and its list entries are updated (`tools/gfx.py`, `Streams.write`).

A map stream holds the tile numbers of its tile stream (the VRAM base is added when it
is drawn), so a block of the map can be redrawn with the tiles only that block uses
(`gfx.replace_block`, `gfx.replace_blocks`).

## Graphics changed

| Screen | Japanese | Where |
|---|---|---|
| Title | ぷよぷよ通 logo: ぷ and よ | sprite groups at `0x2a802` and `0x2aa3e`, tiles `0xb7511` from `0x4e0` (`tools/logo.py`) |
| Tutorial | page titles | tiles `0x91545`, map `0x44ec8` (`tools/titles.py`) |
| Tutorial, play | 乱入可能 | sprite tiles `0x900be` 0-15, tutorial tiles `0x91545` `0x14d`- |
| Tutorial | 全消し | map `0x45503` at `0x270`, tiles `0x91545` |
| Play | 連鎖 | tiles `0x83f2b` `0x78`-`0x7a` |
| Play, four players | 相殺 | 4x2 sprite, tiles `0x83f2b` `0x70`-`0x77` |
| Tower | 相手を / えらんでね, ここにいる | tiles `0xc62d1`, `0xc8503` |
| Continue | コンティニューするかい？ | map `0xcc655`, tiles `0xcca17` |
| Entry | 参加者募集中, 参加, ひとり/ふたり/さんにん/よにん + でぷよぷよ | map `0xff8d4` (`0x2a4`, `0x1f4`, `0x454`-`0x6c4`), tiles `0xca599` |
| Entry | 1Pの / 2Pの スタートボタンを押してね | sprite lists `0x2e8fc` (1P), `0x2e91e` (2P); tiles `0xca599` `0x1a`-`0x49` (loaded at tile `0x100`) |
| AIDS logo | 勇気と愛気 | map `0x3eaff` at `0x604`, tiles `0x3ee26` |
| Rule select | ルールを選んでください and the two rule lines | map `0xfbd02` (`0x8c0`, `0x986`, `0xa0e`), tiles `0xfbf8f` |
| Level select | 激甘 甘口 中辛 辛口 激辛 | sprite lists at `0x1e96c`, tiles `0x86339` (`tools/levels.py`) |
| Win | やった | sprite list `0x1e542`, tiles `0x86f09` |
| Join-in, link | 乱入されたよ, はい/いいえ, 回線が切れました ... | byte strings (`tools/linkmsg.py`), glyphs `0x8cb5e` |

Sprite lists (level labels, win): a count word, then for each sprite y, size and link,
attribute, x (y and x relative to the object). The level labels became lists of 16x8
sprites made of 10 pieces of three 4x7 letters.

The join-in messages are drawn by `0x15be`: a VRAM offset word, then one byte per 16x16
glyph (tile `4 x byte`, column by column), `80 hh` to set the high byte of the tile
words, `fe` for another line, `ff` for the end; an offset `ffff` is followed by a long
pointer. The 32 glyphs became pairs of 8x16 letters; the strings are new and the old
ones point at them.

## Service menu

The service menu is in romaji; the words still in Japanese (SOUSAI, RULE HENKA, RANNYU)
and MAX RENSA in the ending's playing record are replaced in place, same lengths.

## Rivals

The rival of a stage is chosen at `0x4aac`: `0xffa101` (copied to `0xffa05d`) gets an
entry of the table at `0x4b02`, 8 floors of rivals by character number (the order of the
profiles: 0 Will-o'-Wisp ... 31 Satan, 32 Masked Satan). On the last floor Satan becomes
Masked Satan (0x20) when the score is at least 180000 and `0xffa0ef` is 0. When
`0xff4810` is not 0 the rival is `0xff4810 - 1` instead: a debug override, used for the
fighter screenshots of the README.

## Debug

TCRF documents a debug MODE SELECT menu (`maincpu.mb@002AF6=09`) with a stage select.
For quick tests, the boards are at `0xff8000` (player 1) and `0xff8800` (player 2), 168
bytes; filling one with `0xe0` (nuisance puyo) ends the match.
