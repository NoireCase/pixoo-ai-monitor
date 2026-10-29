"""Perform one bounded refresh of enabled providers and print only states."""
import time
from app import Monitor, config

monitor=Monitor(config())
monitor.refresh()
deadline=time.monotonic()+35
try:
    while time.monotonic()<deadline:
        with monitor.guard:
            if all(provider in monitor.data for provider in monitor.c['enabled']):
                break
        time.sleep(.1)
    with monitor.guard:
        for provider in monitor.c['enabled']:
            print(provider,[(r.status,r.window,r.error_message) for r in monitor.data.get(provider,[])])
finally:
    monitor.stop.set()
