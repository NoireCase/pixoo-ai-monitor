from PIL import Image
from decimal import Decimal
FONT={'0':'111101101101111','1':'010110010010111','2':'111001111100111','3':'111001111001111','4':'101101111001001','5':'111100111001111','6':'111100111101111','7':'111001010010010','8':'111101111101111','9':'111101111001111','A':'010101111101101','B':'110101110101110','C':'111100100100111','D':'110101101101110','E':'111100110100111','G':'111100101101111','H':'101101111101101','K':'101101110101101','M':'101111111101101','O':'111101101101111','P':'110101110100100','R':'110101110101101','S':'111100111001111','T':'111010010010010','U':'101101101101111','X':'101101010101101','Y':'101101010010010','N':'101111111111101','I':'111010010010111','W':'101101111111101','-':'000000111000000','.':'000000000000010','%':'101001010100101',' ':'000000000000000'}
def text(img,s,y,color):
    s=str(s).upper(); width=len(s)*4-1
    if width>15: s=s[:4]; width=len(s)*4-1
    x=(16-width)//2
    for ch in s:
        bits=FONT.get(ch,FONT[' '])
        for i,b in enumerate(bits):
            px=x+i%3; py=y+i//3
            if b=='1' and 0<=px<16 and 0<=py<16: img.putpixel((px,py),color)
        x+=4
def color(p,low=20,warn=50):
    return (255,55,55) if p<low else (255,190,0) if p<=warn else (0,220,90)
def amount(v):
    try:
        v=Decimal(str(v))
        if not v.is_finite(): return '-'
        if v<0: return '-'
        if v>=1000000: return '999K'
        if v>=1000: return str(int(v/1000))+'K'
        if v>=100: return str(int(v))
        if v>=10: return str(int(v))
        return f'{v:.1f}'
    except Exception: return '-'
SMALL={'0':'111101111','1':'010010010','2':'110010011','3':'110011110','4':'101111001','5':'111110011','6':'100111111','7':'111001001','8':'111111111','9':'111111001','H':'101111101','D':'110101110','M':'101111101','C':'111100111','N':'101111101','Y':'101010010','U':'101101111','S':'111110011','-':'000111000'}
def small(im,s,color):
    if len(s)>4: s='----'
    x=(16-(len(s)*4-1))//2
    for ch in s:
        bits=SMALL.get(ch,'000000000')
        for i,b in enumerate(bits):
            if b=='1': im.putpixel((x+i%3,11+i//3),color)
        x+=4

def render_classic(r,low=20,warn=50):
    im=Image.new('RGB',(16,16)); theme={'go':(80,180,255),'cx':(80,230,190),'ds':(90,150,255)}.get(r.provider_id,(170,170,170))
    title={'go':'GO','cx':'CX','ds':'DS'}.get(r.provider_id,'BT'); text(im,title,0,theme)
    if r.status not in ('OK','STALE'):
        text(im,{'NOT_CONFIGURED':'SET','ERROR':'ERR','UNSUPPORTED':'ERR'}.get(r.status,'ERR'),7,(180,80,230)); return im
    if r.remaining_percent is not None:
        p=max(0,min(100,float(r.remaining_percent))); c=color(p,low,warn); text(im,str(round(p)),6,c)
        for x in range(round(16*p/100)): im.putpixel((x,15),c)
    else: text(im,amount(r.remaining_value),6,(240,240,240))
    if r.status=='STALE': text(im,'OLD',11,(180,80,230))
    else:
        if r.window or r.unit: small(im, r.window or r.unit,theme)
        if r.source=='MOCK': im.putpixel((15,0),(255,0,255))
    return im

def render(r,low=20,warn=50,*,style='classic',deepseek_reference_peak_cny=100,now=None,b3_config=None):
    if style=='b3':
        from display.b3 import render_b3
        return render_b3(r,b3_config,now)
    if style=='b2':
        from display.b2 import render_b2
        return render_b2(r,deepseek_reference_peak_cny)
    return render_classic(r,low,warn)

def render_configured(r,cfg,now=None):
    return render(r,cfg.get('low',20),cfg.get('warning',50),
                  style=cfg.get('display_style','classic'),
                  deepseek_reference_peak_cny=cfg.get('deepseek_reference_peak_cny',100),now=now,b3_config=cfg)

