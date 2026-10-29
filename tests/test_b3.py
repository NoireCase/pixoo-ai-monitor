from datetime import datetime,timedelta,timezone
from decimal import Decimal
from unittest.mock import patch
from PIL import Image
import pytest
from providers.base import Reading
from display.b2 import GREEN,RED,YELLOW,WHITE
from display.b3 import (GRAY,BLUE,HOUR_X,PERCENT,W,render_b3,percentage_text,
                        countdown_colors,quota_length,diagnostics)
from display.time_status import SHANGHAI,aware_time,price_status,reset_seconds
from display.renderer import render,render_configured

NOW=datetime(2026,10,29,10,0,tzinfo=SHANGHAI)
def reading(pid='go',window='5H',p=72,**kw):
    return Reading(pid,pid,remaining_percent=p,window=window,last_updated=NOW.isoformat(),reset_at=(NOW+timedelta(hours=3,minutes=25)).isoformat(),**kw)

@pytest.mark.parametrize('p,label',[(100,'100'),(99,'99%'),(72,'72%'),(8,'8%'),(0,'0%'),(-1,'0%'),(200,'100')])
def test_percentage_labels(p,label):
    assert percentage_text(Decimal(p))==label
    im=render_b3(reading(p=p),now=NOW)
    assert im.mode=='RGB' and im.size==(16,16)
    points=[(x,y) for y in range(6,13) for x in range(16) if im.getpixel((x,y))==WHITE]
    assert points
    if label.endswith('%'):
        digits=label[:-1]; start=(16-(len(digits)*5-1+4))//2
        x=start+len(digits)*5
        for dy,row in enumerate(PERCENT):
            for dx,b in enumerate(row): assert im.getpixel((x+dx,8+dy))==(WHITE if b=='1' else (0,0,0))

@pytest.mark.parametrize('seconds,expected',[
    (3*3600+25*60,[GREEN,GREEN,GREEN,RED,GRAY]),
    (3*3600+35*60,[GREEN,GREEN,GREEN,GREEN,GRAY]),
    (4*3600,[GREEN]*4+[GRAY]),(80*60,[GREEN,RED,GRAY,GRAY,GRAY]),
    (20*60,[RED]+[GRAY]*4),(0,[GRAY]*5),(18000,[GREEN]*5),
    (1800,[RED]+[GRAY]*4),(1801,[GREEN]+[GRAY]*4),
    (3600,[GREEN]+[GRAY]*4),(None,[GRAY]*5)])
def test_countdown(seconds,expected): assert countdown_colors(seconds)==expected

@pytest.mark.parametrize('p,c',[(0,RED),(19,RED),(20,YELLOW),(59,YELLOW),(60,GREEN),(100,GREEN)])
def test_quota_track(p,c):
    im=render_b3(reading(p=p),now=NOW);n=quota_length(p)
    assert [im.getpixel((x,15)) for x in range(1,15)]==[c]*n+[GRAY]*(14-n)
    assert im.getpixel((0,15))==im.getpixel((15,15))==(0,0,0)
    assert [im.getpixel((x,14)) for x in HOUR_X]==[GREEN,GREEN,GREEN,RED,GRAY]
    assert all(im.getpixel((x,14))==(0,0,0) for x in range(16) if x not in HOUR_X)

def test_lengths_monotone():
    counts=[quota_length(p) for p in range(101)]
    assert counts==sorted(counts) and counts[0]==0 and counts[-1]==14
    assert quota_length(70)==10 and quota_length(18)==3

@pytest.mark.parametrize('pid,window,unit',[('go','5H','%'),('go','7D','%'),('go','30D','%'),('cx','5H','%'),('cx','7D','%'),('ds','','CNY')])
def test_six_pages_no_network(pid,window,unit):
    r=reading(pid,window,None if pid=='ds' else 72,unit=unit,remaining_value=Decimal('82.7'))
    with patch('providers.sources.fetch',side_effect=AssertionError('API called by renderer')):
        im=render_b3(r,now=NOW)
    assert im.size==(16,16) and im.mode=='RGB'
    if window!='5H': assert all(im.getpixel((x,14))==(0,0,0) for x in range(16))
    if window=='7D':
        for y,row in enumerate(W):
            for x,b in enumerate(row): assert bool(im.getpixel((10+x,y))!=(0,0,0))==bool(b=='1')

@pytest.mark.parametrize('clock,state',[('08:59:59','OFF_PEAK'),('09:00:00','PEAK'),('11:59:59','PEAK'),('12:00:00','OFF_PEAK'),('13:59:59','OFF_PEAK'),('14:00:00','PEAK'),('17:59:59','PEAK'),('18:00:00','OFF_PEAK')])
def test_price_boundary(clock,state):
    t=datetime.fromisoformat('2026-10-29T'+clock+'+08:00')
    assert price_status(t)[0]==state
    assert price_status(t.astimezone(timezone.utc))[0]==state

@pytest.mark.parametrize('day,state',[
    ('2026-01-01','OFF_PEAK'),('2026-02-16','OFF_PEAK'),('2026-02-19','OFF_PEAK'),
    ('2026-04-05','OFF_PEAK'),('2026-05-01','OFF_PEAK'),('2026-05-02','OFF_PEAK'),
    ('2026-06-19','OFF_PEAK'),('2026-09-25','OFF_PEAK'),('2026-10-01','OFF_PEAK'),
    ('2026-10-03','OFF_PEAK'),('2026-10-31','OFF_PEAK'),('2026-02-14','OFF_PEAK'),
    ('2026-10-10','OFF_PEAK'),('2026-05-04','PEAK'),('2026-10-05','PEAK'),
    ('2027-01-04','UNKNOWN')])
def test_statutory_vs_compensation_and_unknown(day,state):
    assert price_status(datetime.fromisoformat(day+'T10:00:00+08:00'))[0]==state

def test_ds_status_and_peak_ignored():
    r=reading('ds','',None,unit='CNY',remaining_value=Decimal('82.7'))
    for t,c in [(NOW,RED),(NOW.replace(hour=12),BLUE),(NOW.replace(year=2027),GRAY)]:
        a=render_b3(r,{'deepseek_reference_peak_cny':0},t)
        b=render_b3(r,{'deepseek_reference_peak_cny':100000},t)
        assert a.tobytes()==b.tobytes()
        assert [a.getpixel((x,15)) for x in range(1,15)]==[c]*14

@pytest.mark.parametrize('reset',[None,'bad','2026-10-29T11:00:00'])
def test_reset_missing_or_naive(reset):
    r=reading();r.reset_at=reset
    assert reset_seconds(r,NOW)[0] is None
    assert [render_b3(r,now=NOW).getpixel((x,14)) for x in HOUR_X]==[GRAY]*5

def test_epoch_reset_stale_and_clock_change():
    r=reading();r.reset_at=(NOW+timedelta(hours=1)).timestamp()
    assert reset_seconds(r,NOW)[0]==3600
    assert reset_seconds(r,NOW+timedelta(minutes=1))[0]==3540
    assert reset_seconds(r,NOW+timedelta(hours=2))[0] is None # data expired
    r.last_updated=(NOW+timedelta(hours=2)).isoformat()
    assert reset_seconds(r,NOW+timedelta(hours=2))==(0,'reset already passed; awaiting API refresh')
    r=reading(); assert reset_seconds(r,NOW-timedelta(hours=1))[0] is None
    r.reset_at=(NOW+timedelta(hours=6)).isoformat(); assert reset_seconds(r,NOW)[0] is None
    r=reading();r.status='STALE';assert reset_seconds(r,NOW)[0] is None

def test_invalid_calendar_rules(tmp_path):
    assert price_status(NOW,tmp_path/'missing.json')[0]=='UNKNOWN'
    assert price_status(datetime(2026,10,29))[0]=='UNKNOWN'

def test_old_styles_unchanged():
    r=reading()
    for style in ('classic','b2'):
        assert render(r,style=style).tobytes()==render_configured(r,{'display_style':style},NOW).tobytes()
