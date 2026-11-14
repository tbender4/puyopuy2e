#!/bin/sh
# Reassembles the 68000 patches (needs binutils for m68k: m68k-linux-gnu-as / -ld).
# The .bin files are in the repository, so building the ROM set does not need this.
set -e
cd "$(dirname "$0")"
for p in text8:0x17538 hooks:0x98b00; do
    name=${p%%:*}; addr=${p##*:}
    m68k-linux-gnu-as -m68000 -o "$name.o" "$name.s"
    m68k-linux-gnu-ld -e 0 -Ttext="$addr" --oformat=binary -o "$name.bin" "$name.o"
    rm "$name.o"
done
