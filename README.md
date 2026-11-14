# Puyo Puyo 2 English (Sega C2 arcade)

An English translation of the arcade *Puyo Puyo 2* (ぷよぷよ通, Compile 1994, Sega C2
board, MAME set `puyopuy2`), as a bootleg clone set `puyopuy2e` for
[mame2003-plus](https://github.com/zanac/mame2003-plus-libretro) (branch `puyopuy2e`).

Everything Japanese on screen is translated: the character profiles before each match,
the attract mode's tutorial pages, the title logo, the entry screen, the tower, the rule
and level select screens, the join-in messages, the continue and win screens and the
service menu. The character names follow the English names of the Super Puyo Puyo 2 fan
translation by J2e Translations (Skeleton-T, Mini Zombie, Sukiyapodes, ...).

![Puyo Puyo 2 English in mame2003-plus](screenshots/core_title.png)
![a tutorial page in mame2003-plus](screenshots/core_tutorial.png)

*`puyopuy2e` in the mame2003-plus core: the title and a tutorial page.*

## For dummies

You need one file you already have from your MAME/RetroArch ROM collection:
`puyopuy2.zip` (Puyo Puyo 2, the MAME set). This project does not give it to you.

1. Install Python 3 (Windows: [python.org](https://www.python.org/downloads/), tick
   "Add python.exe to PATH" during the setup; macOS and Linux usually have it already).
   Nothing else is needed.
2. Download this project: green **Code** button on GitHub, **Download ZIP**, and unpack
   it. Or with git:
   ```
   git clone https://github.com/zanac/puyopuy2e
   ```
3. Put `puyopuy2.zip` in the `puyopuy2e` folder you just unpacked (next to this README).
4. Open a terminal in that folder (Windows: type `cmd` in the address bar of the folder
   window and press Enter) and run:
   ```
   python3 make_puyopuy2e.py
   ```
   On Windows, if `python3` is not found, use `python` or `py` instead:
   ```
   py make_puyopuy2e.py
   ```
5. You get `puyopuy2e.zip` in the same folder, the full English ROM set (all three chips,
   it does not need `puyopuy2.zip` any more). The script prints "written ...
   puyopuy2e.zip", the CRC of every file and "CRCs match the mame2003-plus driver".
6. Copy `puyopuy2e.zip` into your ROM folder and start it with the **mame2003-plus**
   core (RetroArch: Load Content, pick `puyopuy2e.zip`, choose "Arcade (MAME
   2003-Plus)"). The core must be a build with the `puyopuy2e` entry (branch
   `puyopuy2e` of [zanac/mame2003-plus-libretro](https://github.com/zanac/mame2003-plus-libretro)).

The zip can also be somewhere else: `python3 make_puyopuy2e.py FOLDER [OUT_FOLDER]`, or
the path of the zip itself. If the script says a chip is not found, your `puyopuy2.zip`
is a different dump: check it against the input table below (the chips are found by CRC,
the names inside the zip do not matter).

## Support
Hey dude! Help me out for a couple of :beers: or a :coffee:!<br/>
[![coffee](https://www.buymeacoffee.com/assets/img/custom_images/black_img.png)](https://bmc.link/zanac)

## Status

| Part | State |
|---|---|
| Character profiles before each match: 33 characters, 58 pages | English, new 8x16 text engine and font (all pages below) |
| Attract mode tutorial pages (15) and their titles | English |
| Title logo ぷよぷよ通 | redrawn as "Puyo Puyo", the gold 2 stays |
| Entry screen: 参加者募集中, 参加, ひとりでぷよぷよ ... | PLAYERS WANTED!, JOIN!, 1P/2P PUYO PUYO |
| Tower: 相手をえらんでね, ここにいる | PICK YOUR RIVAL, YOU ARE HERE |
| 乱入可能 sign, 連鎖 counter, 全消し | JOIN IN!, CHAIN, ALL CLEAR |
| Rule select screen | CHOOSE A RULE! and both rule lines |
| Level select: 激甘 ... 激辛 | EXTRA MILD, MILD, MEDIUM, HOT, EXTRA HOT |
| Join-in and link messages, はい / いいえ | NEW CHALLENGER!, YES / NO, ... |
| Continue screen, win screen (やった) | CONTINUE?, YAY! |
| Act Against AIDS slogan 勇気と愛気 | COURAGE AND LOVE |
| Service menu romaji, ending record (MAX RENSA) | English |
| ROM set `puyopuy2e`, driver entry | done; checked in MAME 0.264 and in the mame2003-plus core |
| Full game, start to ending, 1 player and 2 players | played in MAME: every screen in English |

Known limits:

- The ending is the same at every Difficulty setting (played to the end at Easy, Medium
  and Hardest in MAME: same frames) and has no text; its playing record keeps the game's own romaji names of the
  rivals (SUKETOUDARA, SHEZO WEGEY, ...), already in Latin letters.
- The link messages (two cabinets joined by a cable) cannot be seen in an emulator; they
  are checked by drawing them from the new ROM the way the game does.

## Screenshots

Japanese arcade original on the left, `puyopuy2e` on the right (MAME).

| | Original | English |
|---|---|---|
| Title | ![](screenshots/title_jp.png) | ![](screenshots/title_en.png) |
| Act Against AIDS | ![](screenshots/aids_jp.png) | ![](screenshots/aids_en.png) |
| Tutorial | ![](screenshots/tutorial_jp.png) | ![](screenshots/tutorial_en.png) |
| Tutorial | ![](screenshots/tutorial2_jp.png) | ![](screenshots/tutorial2_en.png) |
| Entry | ![](screenshots/entry_jp.png) | ![](screenshots/entry_en.png) |
| Entry, game mode | ![](screenshots/mode_jp.png) | ![](screenshots/mode_en.png) |
| Tower | ![](screenshots/tower_jp.png) | ![](screenshots/tower_en.png) |
| Tower | ![](screenshots/tower2_jp.png) | ![](screenshots/tower2_en.png) |
| Profile | ![](screenshots/profile_jp.png) | ![](screenshots/profile_en.png) |
| Join-in | ![](screenshots/challenger_jp.png) | ![](screenshots/challenger_en.png) |
| Rule select | ![](screenshots/rule_jp.png) | ![](screenshots/rule_en.png) |
| Level select | ![](screenshots/level_jp.png) | ![](screenshots/level_en.png) |
| Win | ![](screenshots/win_jp.png) | ![](screenshots/win_en.png) |
| Continue | ![](screenshots/continue_jp.png) | ![](screenshots/continue_en.png) |

Every English text page, drawn from the built ROM with its own font and layout
(`tools/text_sheet.py`): the profiles of the 33 characters (a character's second page
follows its first) and the tutorial pages, the TURN DIRECTION variant of the controls
page among them.

![all the English text pages](screenshots/all_text.png)

## The ROM set

Input, the chips of `puyopuy2.zip`:

| File | Size | CRC32 | SHA1 |
|---|---|---|---|
| epr-17241.ic32 | 524288 | 1cad1149 | 77fb0482fa35e615c0bed65f4d7f4dd89b241f23 |
| epr-17240.ic31 | 524288 | beecf96d | c2bdad4b6184c11f81f2a5db409cb4ea186205a7 |
| epr-17239.ic4 | 524288 | 020ff6ef | 6095b8277b47a6fd7a9721f15a70ae5bf6be9b1a |

Output, the files of `puyopuy2e.zip`:

| File | Size | CRC32 | SHA1 | From |
|---|---|---|---|---|
| pp2e-17241.ic32 | 524288 | 6a1c9865 | d067d991be92d051da440d32640a4fb12333e82a | epr-17241.ic32, changed |
| pp2e-17240.ic31 | 524288 | 384bcad2 | 569510f45b3bcbd1d191524de78e6b47c2b1cc47 | epr-17240.ic31, changed |
| epr-17239.ic4 | 524288 | 020ff6ef | 6095b8277b47a6fd7a9721f15a70ae5bf6be9b1a | copied |

These names and CRCs are the ones the `puyopuy2e` driver entry of mame2003-plus expects
(a clone of `puyopuy2`, same board and protection). To try the set in a recent MAME
instead, put the two `pp2e` files in a copy of `puyopuy2.zip` under the names
`epr-17241.ic32` and `epr-17240.ic31` and start `puyopuy2`.

## How it is built

`make_puyopuy2e.py` reads the program of `puyopuy2.zip` and runs `tools/build.py`, which
redoes the whole translation from the original program every time; the result is the
same byte for byte. The English text is `text/script_en.py`; the PNGs in `assets/gfx`
are the big lettering. Only the Python 3 standard library is used.

| File | Purpose |
|---|---|
| `make_puyopuy2e.py` | the ROM set from `puyopuy2.zip` |
| `tools/build.py` | the whole build, step by step |
| `text/script_en.py` | the English profiles and tutorial pages |
| `tools/text.py` | writes the pages and points the original ones at them |
| `patch/text8.s`, `patch/hooks.s` | the new text engine (8x16 glyphs) and the page hooks (68000; `patch/assemble.sh` rebuilds the `.bin`) |
| `tools/font.py`, `font/spleen-8x16.bdf` | the text font |
| `font/title_font.py` | the capitals of the tutorial titles and small labels |
| `tools/titles.py` | the tutorial page titles |
| `tools/labels.py` | the other screens' graphics and the service menu words |
| `tools/logo.py` | the title logo |
| `tools/linkmsg.py` | the join-in and link messages |
| `tools/levels.py` | the level select labels |
| `tools/gfx.py` | tiles, maps, the compressed graphics streams and where they go |
| `tools/lz.py` | the game's LZ format, unpacker and packer |
| `tools/text_sheet.py` | draws every English page from a built `puyopuy2e.zip` (the sheet above) |
| `tools/png.py` | reads and writes the PNGs |
| `tools/romset.py` | the chips of the MAME set |
| `tools/make_gfx_assets.py`, `tools/bigtext.py` | draw `assets/gfx` (maintainers only: Pillow and the Poppins Bold font) |

Technical notes on the game: [docs/notes.md](docs/notes.md).

## Credits and license

- Translation and hacking: Zanac (Vanni Brutto).
- Character names: from the Super Puyo Puyo 2 English translation by J2e Translations.
- Text font: [Spleen](https://github.com/fcambus/spleen) 8x16 by Frederic Cambus, BSD
  2-clause license (`font/LICENSE-spleen`).
- Title logo: the "Puyo Puyo" lettering is cut from `assets/puyopuyo_logo.jpg`
  (`logo_puyo.png`, in the colours of the original logo).
- Big lettering of `assets/gfx`: drawn with Poppins Bold (SIL Open Font License) by the
  maintainer script; the font itself is not part of the project.
- *Puyo Puyo 2* © Compile 1994, Sega. This project distributes no game data: the build
  starts from your own `puyopuy2.zip`.
