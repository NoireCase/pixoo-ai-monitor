"""Offline time/price evaluation; no credentials or network operations."""
from datetime import datetime, timezone, timedelta, date
from functools import lru_cache
import json
import math
from pathlib import Path

DATA=Path(__file__).resolve().parents[1]/'data'
try:
    from zoneinfo import ZoneInfo
    SHANGHAI=ZoneInfo('Asia/Shanghai')
except (ImportError, KeyError):
    # Windows may lack IANA tzdata; modern Shanghai is UTC+08 without DST.
    SHANGHAI=timezone(timedelta(hours=8),name='Asia/Shanghai')

def aware_time(value):
    try:
        if isinstance(value,datetime): result=value
        elif isinstance(value,(int,float)) and not isinstance(value,bool):
            if not math.isfinite(value): return None
            result=datetime.fromtimestamp(value,timezone.utc)
        elif isinstance(value,str): result=datetime.fromisoformat(value.replace('Z','+00:00'))
        else: return None
        return result if result.tzinfo is not None and result.utcoffset() is not None else None
    except (ValueError,OverflowError,OSError,TypeError): return None

def freshness(reading,now,max_age=360):
    now=aware_time(now); updated=aware_time(reading.last_updated)
    if reading.status!='OK': return False,reading.status
    if now is None or updated is None: return False,'update time unavailable'
    age=(now-updated).total_seconds()
    if age < -60: return False,'clock moved backwards or future update time'
    if age>max_age: return False,'data expired'
    return True,'OK'

def reset_seconds(reading,now,max_age=360):
    fresh,reason=freshness(reading,now,max_age)
    if not fresh: return None,reason
    reset=aware_time(reading.reset_at)
    if reset is None: return None,'reset time unavailable'
    seconds=(reset-aware_time(now)).total_seconds()
    if seconds<0: return 0,'reset already passed; awaiting API refresh'
    if seconds>18000: return None,'reset exceeds five hours or clock changed'
    return seconds,'OK'

@lru_cache(maxsize=8)
def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def price_status(now=None,rules_path=None):
    """PEAK/OFF_PEAK/UNKNOWN and a diagnostic explanation."""
    now=aware_time(now if now is not None else datetime.now(timezone.utc))
    if now is None: return 'UNKNOWN','timezone-aware current time required'
    local=now.astimezone(SHANGHAI)
    try:
        path=Path(rules_path) if rules_path else DATA/'deepseek_price_rules.json'
        rules=load_json(str(path))
        if rules.get('timezone')!='Asia/Shanghai': return 'UNKNOWN','unsupported rule timezone'
        calendar=load_json(str(path.parent/rules['holiday_calendar']))
        holidays=calendar['years'].get(str(local.year))
        if holidays is None: return 'UNKNOWN',f'calendar coverage missing for {local.year}'
        dates={date.fromisoformat(d) for d in holidays}
        if any(d.year!=local.year for d in dates): return 'UNKNOWN','invalid calendar year'
        if local.date() in dates: return 'OFF_PEAK','statutory holiday'
        if local.weekday()>=5: return 'OFF_PEAK','weekend (including adjusted work weekends)'
        minute=local.hour*60+local.minute
        intervals=[]
        for start,end in rules['peak_intervals']:
            def minutes(v):
                h,m=map(int,v.split(':'))
                if not (0<=h<24 and 0<=m<60): raise ValueError('invalid time')
                return h*60+m
            a,b=minutes(start),minutes(end)
            if a>=b: raise ValueError('invalid interval')
            intervals.append((a,b))
        return ('PEAK','weekday peak interval') if any(a<=minute<b for a,b in intervals) else ('OFF_PEAK','outside peak interval')
    except (OSError,ValueError,KeyError,TypeError): return 'UNKNOWN','price rules/calendar unavailable or invalid'
