| Puyo Puyo 2 English: the script opcodes that open a text page (op 03: the tutorial
| window, op 0b: the profile box) take the text right after their resume pointer. Here
| that text may instead be 0xfffe followed by the long address of the English text.
| Assembled at 0x98b00 (free space); the opcodes jump here (tools/build.py).

        .text
| op 03 (from 0x171b4): a1 = the script, after the opcode
op03:   move.l  (%a1)+,0x32(%a0)        | where the script goes on
        movea.l %a1,%a2                 | the text
        bsr.s   indirect
        moveq   #2,%d2
        jmp     0x17400

| op 0b (from 0x1720c)
op0b:   movea.l 0x32(%a0),%a2
        move.l  (%a2)+,0x32(%a0)
        move.w  -8(%a2),%d1             | the box's position
        addi.w  #0x82,%d1               | its first character
        bsr.s   indirect
        moveq   #2,%d2
        jmp     0x17400

indirect:
        cmpi.w  #0xfffe,(%a2)
        bne.s   1f
        movea.l 2(%a2),%a2
1:      rts
