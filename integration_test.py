"""Show one bounded rotation of real provider data on the configured Pixoo."""
import time
from app import Monitor, config, lock
from drivers.pixoo import Pixoo
from display.renderer import render, render_configured

if not lock():
    raise SystemExit('Another monitor instance is running; stop it before this test.')

c = config()
monitor = Monitor(c)
monitor.refresh()
device = Pixoo(c['mac'], int(c['port']))
try:
    deadline = time.monotonic() + 35
    while time.monotonic() < deadline:
        with monitor.guard:
            if all(pid in monitor.data for pid in c['enabled']):
                break
        time.sleep(.1)
    pages = monitor.pages()
    device.connect()
    device.brightness(c['brightness'])
    for reading in pages:
        device.show(render_configured(reading,c))
        print(f'{reading.display_name}: {reading.window or reading.unit} {reading.status}', flush=True)
        time.sleep(max(1, float(c['rotation_seconds'])))
    print('Rotation sent; visual confirmation required.', flush=True)
finally:
    monitor.stop.set()
    device.close()
