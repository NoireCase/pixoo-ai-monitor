"""B3 pixel layout; B2 remains independently available."""
from datetime import datetime,timezone
from decimal import Decimal
from PIL import Image
from display.b2 import (HEAD,DIGITS,WHITE,PLATFORM,WINDOW,GREEN,RED,
                        draw_glyph,decimal,money,number,percent_color,width)
from display.time_status import freshness,reset_seconds,price_status

GRAY=(36,36,36)
BLUE=(55,137,255)
W=['10001','10001','10101','10101','01010']
PERCENT=['101','001','010','100','101']
HOUR_X=(3,5,7,9,11)

def percentage_text(value):
    p=max(Decimal(0),min(Decimal(100),value));n=str(round(p))
    return n if n=='100' else n+'%'

def draw_percentage(im,value):
    s=percentage_text(value);digits=s.rstrip('%')
    total=width(digits)+(4 if s.endswith('%') else 0);x=(16-total)//2
    for ch in digits:
        draw_glyph(im,DIGITS[ch],x,6,WHITE);x+=len(DIGITS[ch][0])+1
    if s.endswith('%'): draw_glyph(im,PERCENT,x,8,WHITE)

def countdown_colors(seconds):
    out=[GRAY]*5
    if seconds is None: return out
    seconds=max(0,min(18000,seconds));full=int(seconds//3600)
    for i in range(full): out[i]=GREEN
    fraction=seconds-full*3600
    if full<5 and fraction>0: out[full]=GREEN if fraction>1800 else RED
    return out

def quota_length(p):
    p=decimal(p) or Decimal(0)
    return int(max(Decimal(0),min(Decimal(100),p))*14/100+Decimal('.5'))

def diagnostics(reading,cfg=None,now=None):
    cfg=cfg or {};now=now or datetime.now(timezone.utc)
    age=cfg.get('display_data_stale_seconds',max(300,float(cfg.get('refresh_seconds',120))*3))
    fresh,reason=freshness(reading,now,age)
    result={'fresh':fresh,'data_status':reason}
    if reading.window=='5H' and reading.provider_id in ('go','cx'):
        result['reset_seconds'],result['reset_status']=reset_seconds(reading,now,age)
    if reading.provider_id=='ds':
        result['price_status'],result['price_reason']=price_status(now,cfg.get('deepseek_price_rules_file'))
    return result

def render_b3(reading,cfg=None,now=None):
    cfg=cfg or {};now=now or datetime.now(timezone.utc)
    im=Image.new('RGB',(16,16),'black')
    char,color=PLATFORM.get(reading.provider_id,('-',GRAY));draw_glyph(im,HEAD[char],1,0,color)
    char,color=WINDOW.get(reading.window or reading.unit,('-',GRAY))
    rows=W if reading.window=='7D' else HEAD[char]
    draw_glyph(im,rows,15-len(rows[0]),0,color)
    diag=diagnostics(reading,cfg,now);state=reading.status
    if state=='OK' and not diag['fresh']: state='STALE'
    p=decimal(reading.remaining_percent)
    if state=='OK':
        if p is not None: draw_percentage(im,p)
        else: number(im,money(reading.remaining_value))
    else:
        from display.renderer import text
        text(im,{'NOT_CONFIGURED':'SET','STALE':'OLD'}.get(state,'ERR'),7,(180,80,230))
    if reading.window=='5H' and reading.provider_id in ('go','cx'):
        for x,c in zip(HOUR_X,countdown_colors(diag.get('reset_seconds'))): im.putpixel((x,14),c)
    if reading.provider_id in ('go','cx'):
        count=quota_length(p) if p is not None and state=='OK' else 0
        for x in range(1,15): im.putpixel((x,15),percent_color(p) if x<=count else GRAY)
    elif reading.provider_id=='ds':
        c={'PEAK':RED,'OFF_PEAK':BLUE}.get(diag['price_status'],GRAY)
        for x in range(1,15): im.putpixel((x,15),c)
    if reading.source=='MOCK': im.putpixel((0,13),(255,0,255))
    return im
