from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
import pytest
from PIL import Image
from providers.base import Reading
from display.renderer import render,render_classic,render_configured
from display.b2 import (WHITE,GREEN,YELLOW,RED,DARK,NEUTRAL,DIGITS,
                        fill_count,peak_ratio,money,width)

@pytest.mark.parametrize('pid,window,unit', [('go','5H','%'),('go','7D','%'),('go','30D','%'),('cx','5H','%'),('cx','7D','%'),('ds','','CNY')])
def test_six_pages(pid,window,unit):
    r=Reading(pid,pid,window=window,unit=unit,remaining_percent=72 if pid!='ds' else None,remaining_value=Decimal('82.23'))
    with patch('providers.sources.fetch',side_effect=AssertionError('render called provider')):
        im=render(r,style='b2')
    assert im.size==(16,16) and im.mode=='RGB'
    assert all(im.getpixel((x,y))==(0,0,0) for y in (5,13,14) for x in range(16))

@pytest.mark.parametrize('p,c',[(100,GREEN),(60,GREEN),(59,YELLOW),(20,YELLOW),(19,RED),(0,RED),(-9,RED),(200,GREEN)])
def test_bar(p,c):
    im=render(Reading('go','GO',remaining_percent=p,window='5H'),style='b2')
    count=fill_count(p)
    assert [im.getpixel((x,15)) for x in range(16)]==[c]*count+[DARK]*(16-count)
    assert {im.getpixel((x,y)) for y in range(6,13) for x in range(16)} <= {(0,0,0),WHITE}

@pytest.mark.parametrize('value',[0,7,19,60,100])
def test_number_center(value):
    im=render(Reading('go','GO',remaining_percent=value),style='b2')
    x=(16-width(str(value)))//2
    expected=Image.new('RGB',(16,16))
    from display.b2 import draw_glyph
    for ch in str(value):
        draw_glyph(expected,DIGITS[ch],x,6,WHITE); x+=len(DIGITS[ch][0])+1
    assert im.crop((0,6,16,13)).tobytes()==expected.crop((0,6,16,13)).tobytes()

@pytest.mark.parametrize('peak',[None,0,-1,'invalid','NaN','Infinity'])
def test_invalid_peak(peak):
    assert peak_ratio(12,peak) is None
    im=render(Reading('ds','DS',remaining_value=12,unit='CNY'),style='b2',deepseek_reference_peak_cny=peak)
    assert all(im.getpixel((x,15))==NEUTRAL for x in range(16))

def test_reference_peak():
    assert peak_ratio(25,100)==Decimal('.25')
    assert peak_ratio(200,100)==1 and peak_ratio(-1,100)==0
    assert peak_ratio(25,50)==Decimal('.5')
    im=render(Reading('ds','DS',remaining_value=50,unit='CNY'),style='b2')
    assert sum(im.getpixel((x,15))!=DARK for x in range(16))==8

@pytest.mark.parametrize('value',[None,-12,0,Decimal('.23'),Decimal('8.25'),Decimal('82.34'),999,1000,1000000,10**100])
def test_money(value):
    r=Reading('ds','DS',remaining_value=value,unit='CNY')
    im=render(r,style='b2'); assert width(money(value))<=16
    assert r.remaining_value==value
    assert im.size==(16,16)
    if value==Decimal('8.25'): assert money(value)=='8.25'

@pytest.mark.parametrize('state',['NOT_CONFIGURED','ERROR','UNSUPPORTED','STALE'])
def test_states(state):
    r=Reading('cx','CX',remaining_percent=72,status=state,window='5H')
    im=render(r,style='b2'); assert im.size==(16,16)
    assert (180,80,230) in set(im.getdata())
    assert im.crop((0,6,16,13)).tobytes()!=render(Reading('cx','CX',remaining_percent=72),style='b2').crop((0,6,16,13)).tobytes()

def test_classic_unchanged():
    r=Reading('go','GO',remaining_percent=72,window='5H')
    assert render(r,style='classic').tobytes()==render_classic(r).tobytes()
    assert render_configured(r,{}).tobytes()==render_classic(r).tobytes()

@pytest.mark.parametrize('name,pid,window,value', [('o_h','go','5H',100),('o_d','go','7D',100),('o_m','go','30D',72),('g_h','cx','5H',81),('g_d','cx','7D',97),('d_yen','ds','',82)])
def test_reference_structure(name,pid,window,value):
    path=Path(__file__).with_name('b2_layout_masks.json')
    r=Reading(pid,pid,window=window,unit='CNY' if pid=='ds' else '%',remaining_value=value,remaining_percent=value if pid!='ds' else None)
    actual=render(r,style='b2'); reference=__import__('json').loads(path.read_text(encoding='utf-8'))[name]
    assert [actual.getpixel((x,y))!=(0,0,0) for y in range(15) for x in range(16)]==[reference[y][x]=='1' for y in range(15) for x in range(16)]
