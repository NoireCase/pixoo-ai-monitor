"""Clearly labelled TEST previews from B3 renderer, never account data."""
from datetime import datetime,timedelta
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from providers.base import Reading
from display.b3 import render_b3
from display.time_status import SHANGHAI

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'b3-visual-review'/'test-samples'
OUT.mkdir(parents=True,exist_ok=True)
now=datetime(2026,10,29,10,tzinfo=SHANGHAI)
cases=[]
for p in (100,99,72,8,0,59,60,19,20):
    cases.append((f'TEST quota {p}',Reading('go','GO',remaining_percent=p,window='5H',last_updated=now.isoformat(),reset_at=(now+timedelta(hours=3,minutes=25)).isoformat()),now))
for seconds in (12300,12900,14400,4800,1200,0,18000,1800,1801):
    cases.append((f'TEST reset {seconds}s',Reading('cx','CX',remaining_percent=72,window='5H',last_updated=now.isoformat(),reset_at=(now+timedelta(seconds=seconds)).timestamp()),now))
for label,t in [('PEAK',now),('OFF_PEAK',now.replace(hour=12)),('UNKNOWN',now.replace(year=2027))]:
    cases.append(('TEST DS '+label,Reading('ds','DS',remaining_value=82,unit='CNY',last_updated=t.isoformat()),t))
for label,kw in [('missing',{'reset_at':None}),('stale',{'status':'STALE'})]:
    cases.append(('TEST reset '+label,Reading('go','GO',remaining_percent=72,window='5H',last_updated=now.isoformat(),**kw),now))
rows=(len(cases)+2)//3
board=Image.new('RGB',(1080,rows*390),(22,25,32));draw=ImageDraw.Draw(board);font=ImageFont.truetype('arial.ttf',18)
for i,(label,r,t) in enumerate(cases):
    image=render_b3(r,now=t);name=label.lower().replace(' ','_')
    image.save(OUT/(name+'_16.png'));large=image.resize((320,320),Image.Resampling.NEAREST);large.save(OUT/(name+'_320.png'))
    x=20+(i%3)*360;y=12+(i//3)*390
    draw.text((x,y),label,font=font,fill='white');board.paste(large,(x,y+36))
board.save(OUT/'TEST_overview.png')
print('Generated explicitly labelled TEST B3 samples.')
