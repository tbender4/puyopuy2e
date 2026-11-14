| Puyo Puyo 2 English: the text engine draws 8x16 glyphs, one column of two tiles per code.
| Replaces the routine at 0x17538 (the original draws 16x16 glyphs, two columns per code).
|
| In: d0.w the text code (0: nothing drawn, the pause after a name), a0 the text task:
|   $12(a0) VRAM address of the cursor (the name table), $16(a0) the font,
|   $2c(a0) 4 x the glyphs already in VRAM (their codes at 0xffaa00), $38(a0) first tile.
| A glyph is 16 bytes (16 rows of 8 pixels, MSB left) at font + code * 16; it gets two
| tiles, the upper one first, at tile $38(a0) + 2 x its index.

        .text
        .globl  text_put
text_put:
        tst.w   %d0
        beq.w   space
        lea     0xffaa00,%a1            | codes of the glyphs in VRAM
        move.w  0x2c(%a0),%d5
        lsr.w   #1,%d5                  | 2 x count: end of the code list
        clr.w   %d1
find:   cmp.w   %d1,%d5
        beq.s   new
        cmp.w   (%a1,%d1.w),%d0
        beq.s   name                    | d1 = 2 x index = tile offset
        addq.w  #2,%d1
        bra.s   find

new:    move.w  %d0,(%a1,%d5.w)
        asl.w   #4,%d0
        movea.l 0x16(%a0),%a2
        lea     (%a2,%d0.w),%a2         | the glyph
        add.w   0x38(%a0),%d5           | its first tile
        andi.w  #0x7ff,%d5
        asl.w   #5,%d5                  | VRAM address
        move.l  #0x01011010,%d4         | the box's dotted background
        lea     nib(%pc),%a1
        clr.w   %d1
row:    clr.w   %d0
        move.b  (%a2,%d1.w),%d0
        andi.b  #0xf0,%d0
        lsr.b   #3,%d0
        move.w  (%a1,%d0.w),%d2
        or.w    %d4,%d2
        swap    %d2
        move.b  (%a2,%d1.w),%d0
        andi.b  #0x0f,%d0
        add.b   %d0,%d0
        move.w  (%a1,%d0.w),%d2
        or.w    %d4,%d2
        ori.w   #0x700,%sr
        jsr     0x1056                  | VDP write address d5
        move.l  %d2,0xc00000
        andi.w  #0xf8ff,%sr
        swap    %d4
        addq.w  #4,%d5
        addq.w  #1,%d1
        cmpi.w  #16,%d1
        bcs.s   row
        move.w  0x2c(%a0),%d1
        lsr.w   #1,%d1                  | tile offset of the new glyph
        addq.w  #4,0x2c(%a0)

name:   add.w   0x38(%a0),%d1
        move.w  0x12(%a0),%d5
        ori.w   #0x700,%sr
        jsr     0x1056
        move.w  %d1,0xc00000            | upper tile
        andi.w  #0xf8ff,%sr
        add.w   0xfff014,%d5            | one row down
        addq.w  #1,%d1
        ori.w   #0x700,%sr
        jsr     0x1056
        move.w  %d1,0xc00000            | lower tile
        andi.w  #0xf8ff,%sr
        addq.w  #2,0x12(%a0)            | one column on
        rts

space:  addq.w  #2,0x12(%a0)            | code 0 (the profiles' pause): nothing drawn
        rts

nib:    .word   0x0000,0x000f,0x00f0,0x00ff,0x0f00,0x0f0f,0x0ff0,0x0fff
        .word   0xf000,0xf00f,0xf0f0,0xf0ff,0xff00,0xff0f,0xfff0,0xffff
