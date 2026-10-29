"""Read provider timing metadata; never print credentials or raw responses."""
from datetime import datetime,timezone
from app import config
from providers.sources import fetch
from display.b3 import diagnostics

cfg=config()
for pid in ('go','cx','ds'):
    try:
        for r in fetch(pid):
            print(pid,r.window or r.unit,r.status,diagnostics(r,cfg,datetime.now(timezone.utc)),flush=True)
    except Exception as exc:
        print(pid,type(exc).__name__,flush=True)
