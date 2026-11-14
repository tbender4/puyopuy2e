from PIL import Image, ImageDraw, ImageFont
FONT='/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
def mask(text,W,H,size,track=-2,font=FONT,dy=0):
    ft=ImageFont.truetype(font,size*2)
    m=Image.new('L',(W*2,H*2),0); d=ImageDraw.Draw(m)
    ls=[d.textlength(ch,font=ft) for ch in text]
    total=sum(ls)+2*track*(len(text)-1)
    bb=d.textbbox((0,0),text,font=ft)
    x=(W*2-total)/2; y=(H*2-(bb[3]-bb[1]))/2-bb[1]+dy*2
    for ch,l in zip(text,ls):
        d.text((x,y),ch,font=ft,fill=255); x+=l+2*track
    return m.resize((W,H),Image.LANCZOS)
def indexed(m,fill,edge,outline,thick=1):
    W,H=m.size
    img=[[0]*W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            v=m.getpixel((x,y))
            if v>=140: img[y][x]=fill
            elif v>=60 and edge is not None: img[y][x]=edge
            elif v>=60: img[y][x]=fill
    out=[r[:] for r in img]
    for y in range(H):
        for x in range(W):
            if img[y][x]: continue
            if any(0<=y+dy<H and 0<=x+dx<W and img[y+dy][x+dx] for dy in range(-thick,thick+1) for dx in range(-thick,thick+1)):
                out[y][x]=outline
    return out
