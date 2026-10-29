"""Explicit test data only: threshold samples and design-reference comparison."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from providers.base import Reading
from display.renderer import render

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'b2-visual-review'/'test-samples'
OUT.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype('arial.ttf',18)
samples=[]
for value in (100,60,59,20,19,0):
    samples.append((f'TEST quota {value}',Reading('cx','Codex',remaining_percent=value,window='5H',source='TEST SAMPLE')))
for value in (15,50,95):
    samples.append((f'TEST DS {value} / ref 100',Reading('ds','DeepSeek',remaining_value=value,unit='CNY',source='TEST SAMPLE')))
board=Image.new('RGB',(1080,1170),(22,25,32)); d=ImageDraw.Draw(board)
for i,(label,r) in enumerate(samples):
    image=render(r,style='b2'); name=label.replace(' / ','_').replace(' ','_').lower()
    image.save(OUT/(name+'_16.png')); large=image.resize((320,320),Image.Resampling.NEAREST);large.save(OUT/(name+'_320.png'))
    x=20+(i%3)*360;y=15+(i//3)*390
    d.text((x,y),label,font=font,fill='white');board.paste(large,(x,y+36))
board.save(OUT/'TEST_samples_overview.png')

print('B2 test samples generated (not account data).')
