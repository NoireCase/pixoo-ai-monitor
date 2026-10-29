"""B2 layout: native pixel glyphs, no scaled text or provider access."""
from decimal import Decimal, InvalidOperation, ROUND_DOWN
from PIL import Image

WHITE=(246,248,252)
PLATFORM={'go':('O',(244,247,252)),'cx':('G',(39,222,207)),'ds':('D',(55,137,255))}
WINDOW={'5H':('H',(255,186,78)),'7D':('D',(120,178,255)),
        '30D':('M',(188,131,255)),'CNY':('¥',(255,195,79)),'USD':('$',(255,195,79))}
DARK=(8,10,14)
GREEN=(40,222,111)
YELLOW=(255,195,47)
RED=(255,72,104)
NEUTRAL=(80,85,95)
HEAD={
 'O':['111','101','101','101','111'],
 'G':['111','100','101','101','111'],
 'D':['110','101','101','101','110'],
 'H':['101','101','111','101','101'],
 'M':['10001','11011','10101','10001','10001'],
 '¥':['10001','01010','11111','00100','01110'],
 '$':['011','110','010','011','110'],
 '-':['000','000','111','000','000']}
DIGITS={
 '0':['0110','1001','1001','1001','1001','1001','0110'],
 '1':['0010','0110','0010','0010','0010','0010','0111'],
 '2':['1110','0001','0001','0110','1000','1000','1111'],
 '3':['1110','0001','0001','0110','0001','0001','1110'],
 '4':['1001','1001','1001','1111','0001','0001','0001'],
 '5':['1111','1000','1000','1110','0001','0001','1110'],
 '6':['0110','1000','1000','1110','1001','1001','0110'],
 '7':['1111','0001','0010','0010','0100','0100','0100'],
 '8':['0110','1001','1001','0110','1001','1001','0110'],
 '9':['0110','1001','1001','0111','0001','0001','1110'],
 '.':['0','0','0','0','0','0','1'],
 'K':['1001','1010','1100','1000','1100','1010','1001'],
 'M':['10001','11011','10101','10101','10001','10001','10001'],
 'B':['1110','1001','1001','1110','1001','1001','1110'],
 'T':['111','010','010','010','010','010','010'],
 '-':['000','000','000','111','000','000','000']}

def draw_glyph(im,rows,x,y,c):
    for dy,row in enumerate(rows):
        for dx,bit in enumerate(row):
            if bit=='1':
                if not (0<=x+dx<16 and 0<=y+dy<16):
                    raise ValueError('B2 glyph exceeds canvas')
                im.putpixel((x+dx,y+dy),c)

def width(value):
    return sum(len(DIGITS[ch][0]) for ch in value)+len(value)-1

def number(im,value):
    x=(16-width(value))//2
    for ch in value:
        draw_glyph(im,DIGITS[ch],x,6,WHITE)
        x+=len(DIGITS[ch][0])+1

def decimal(value):
    try:
        n=Decimal(str(value))
        return n if n.is_finite() else None
    except (InvalidOperation,ValueError,TypeError): return None

def money(value):
    n=decimal(value)
    if n is None: return '-'
    # Negative balances remain negative rather than being shown as zero.
    sign='-' if n<0 else ''
    n=abs(n)
    for scale,suffix in [(Decimal(1),''),(Decimal(1000),'K'),(Decimal(10)**6,'M'),
                         (Decimal(10)**9,'B'),(Decimal(10)**12,'T')]:
        v=n/scale
        for places in (2,1,0):
            if v.adjusted()>10: continue
            value=format(v.quantize(Decimal(1).scaleb(-places),rounding=ROUND_DOWN),'f')
            if '.' in value: value=value.rstrip('0').rstrip('.')
            value=sign+value+suffix
            if width(value)<=16: return value
    return '-' # Value is still retained in the provider, but cannot fit this canvas.

def percent_color(p):
    return GREEN if p>=60 else YELLOW if p>=20 else RED

def fill_count(p):
    return round(16*max(0,min(100,float(p)))/100)

def peak_ratio(value,peak):
    n=decimal(value); peak=decimal(peak)
    if n is None or peak is None or peak<=0: return None
    return max(Decimal(0),min(Decimal(1),n/peak))

def spectrum(x):
    stops=[(41,142,255),(150,76,210),(255,72,104)]
    position=x/15*2; segment=min(1,int(position)); f=position-segment
    return tuple(round(a+(b-a)*f) for a,b in zip(stops[segment],stops[segment+1]))

def render_b2(r,peak=100):
    im=Image.new('RGB',(16,16),'black')
    letter,c=PLATFORM.get(r.provider_id,('-',NEUTRAL))
    draw_glyph(im,HEAD[letter],1,0,c)
    letter,c=WINDOW.get(r.window or r.unit,('-',NEUTRAL))
    draw_glyph(im,HEAD[letter],15-len(HEAD[letter][0]),0,c)
    if r.status not in ('OK','STALE'):
        from display.renderer import text
        text(im,'SET' if r.status=='NOT_CONFIGURED' else 'ERR',7,(180,80,230))
        return im
    p=decimal(r.remaining_percent)
    if p is not None:
        p=max(Decimal(0),min(Decimal(100),p))
        number(im,str(round(p)))
        count=fill_count(p)
        for x in range(16): im.putpixel((x,15),percent_color(p) if x<count else DARK)
    else:
        number(im,money(r.remaining_value))
        ratio=peak_ratio(r.remaining_value,peak) if r.unit=='CNY' else None
        for x in range(16):
            im.putpixel((x,15),NEUTRAL if ratio is None else spectrum(x) if x<fill_count(ratio*100) else DARK)
    if r.status=='STALE':
        # OLD replaces the main value; stale data cannot look like a live balance.
        from display.renderer import text
        for y in range(6,13):
            for x in range(16): im.putpixel((x,y),(0,0,0))
        text(im,'OLD',7,(180,80,230))
    if r.source=='MOCK': im.putpixel((0,14),(255,0,255))
    return im
