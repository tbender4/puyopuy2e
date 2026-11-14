def decompress(p, a):
    """Compile LZ (puyopuy2 0x1e72): 0 ends; 1-0x7f: that many literal bytes;
    0x80|k, b: copy k+3 bytes from 256-byte ring at pos-b-1. Returns (data, end)"""
    ring=bytearray(256); pos=0; out=bytearray()
    while True:
        n=p[a]; a+=1
        if n==0: return bytes(out), a
        if n<0x80:
            for _ in range(n):
                c=p[a]; a+=1; out.append(c); ring[pos]=c; pos=(pos+1)&255
        else:
            k=(n&0x7f)+3; src=(pos-p[a]-1)&255; a+=1
            for _ in range(k):
                c=ring[src]; out.append(c); ring[pos]=c; pos=(pos+1)&255; src=(src+1)&255
def compress(data):
    """greedy-optimal-ish LZ for the same format"""
    out=bytearray(); i=0; lit=bytearray()
    def flush():
        nonlocal lit
        while lit:
            ch=lit[:0x7f]; out.append(len(ch)); out.extend(ch); lit=lit[len(ch):]
    n=len(data)
    while i<n:
        best=0; bo=0
        lo=max(0,i-256)
        maxl=min(0x7f+3,n-i)
        for j in range(i-1,lo-1,-1):
            l=0
            while l<maxl and data[j+l]==data[i+l]: l+=1   # overlap allowed (j+l may reach i..)
            if l>best: best=l; bo=i-j-1
            if best==maxl: break
        if best>=3:
            flush(); out.append(0x80|(best-3)); out.append(bo); i+=best
        else:
            lit.append(data[i]); i+=1
    flush(); out.append(0)
    return bytes(out)
