"""Export fresh real readings using the same page selection and renderer as app.py.

This is an independent snapshot, not a capture of the running process's memory.
It does not open a Bluetooth socket or write to the running monitor's cache.
"""
from datetime import datetime,timezone
from pathlib import Path
import time
import zipfile

from PIL import Image, ImageDraw, ImageFont
from app import Monitor, config
from display.renderer import render, render_configured

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'visual-review'
ARCHIVE = ROOT / 'visual-review.zip'
EXPECTED = [('go','5H','GO 5H'),('go','7D','GO 7D'),('go','30D','GO 30D'),
            ('cx','5H','CX 5H'),('cx','7D','CX 7D'),('ds','CNY','DS CNY')]

def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--style',choices=['classic','b2','b3'])
    args=parser.parse_args()
    cfg = config()
    if args.style: cfg['display_style']=args.style
    global OUT, ARCHIVE
    if args.style:
        OUT=ROOT/(args.style+'-visual-review')
        ARCHIVE=ROOT/(args.style+'-visual-review.zip')
    monitor = Monitor(cfg)
    monitor.refresh()
    deadline = time.monotonic() + 35
    try:
        while time.monotonic() < deadline:
            with monitor.guard:
                if all(pid in monitor.data for pid in cfg['enabled']):
                    break
            time.sleep(.1)
        with monitor.guard:
            readings = {pid: list(value) for pid,value in monitor.data.items()}
        # Match the live app's enabled-provider and window selection.
        pages = monitor.pages() if readings else []
    finally:
        monitor.stop.set()

    OUT.mkdir(exist_ok=True)
    generated = []
    results = []
    snapshot_time=datetime.now(timezone.utc)
    timing_notes=[]
    for pid, window, label in EXPECTED:
        reading = next((r for r in pages if r.provider_id == pid and
                        (r.window == window if pid != 'ds' else r.unit == window)), None)
        if reading is None or reading.status != 'OK' or reading.source == 'MOCK':
            state = 'NOT AVAILABLE'
            if pid not in cfg['enabled'] or (pid != 'ds' and window not in cfg['windows']):
                state = 'DISABLED'
            elif readings.get(pid):
                state = readings[pid][0].status if readings[pid][0].status != 'OK' else 'WINDOW NOT RETURNED'
            results.append((label, state, None))
            continue
        image = render_configured(reading,cfg,snapshot_time)
        if cfg.get('display_style')=='b3':
            from display.b3 import diagnostics
            diag=diagnostics(reading,cfg,snapshot_time)
            timing_notes.append(f'{label}: {diag}')
        if image.mode != 'RGB' or image.size != (16,16):
            raise ValueError('Renderer must return a 16x16 RGB image')
        name = label.lower().replace(' ', '_')
        original = OUT / (name + '_16.png')
        enlarged = OUT / (name + '_320.png')
        image.save(original)
        image.resize((320,320), Image.Resampling.NEAREST).save(enlarged)
        generated.extend([original,enlarged])
        results.append((label,'OK',image))

    board = Image.new('RGB',(1200, 850),(22,25,32))
    draw = ImageDraw.Draw(board)
    try:
        title_font = ImageFont.truetype('arial.ttf',24)
        note_font = ImageFont.truetype('arial.ttf',17)
    except OSError:
        title_font = note_font = ImageFont.load_default()
    for index,(label,state,image) in enumerate(results):
        x = 30 + (index % 3) * 400
        y = 24 + (index // 3) * 410
        caption=label
        if cfg.get('display_style')=='b3':
            caption={'GO 5H':'O / H','GO 7D':'O / W','GO 30D':'O / M','CX 5H':'G / H','CX 7D':'G / W','DS CNY':'D / YEN'}[label]
        draw.text((x,y),caption,fill='white',font=title_font)
        if image is not None:
            board.paste(image.resize((320,320),Image.Resampling.NEAREST),(x,y+40))
        else:
            draw.rectangle((x,y+40,x+319,y+359),fill=(40,44,54))
            draw.text((x+12,y+180),state,fill=(235,175,175),font=note_font)
        draw.text((x,y+370),state,fill=(180,190,205),font=note_font)
    overview = OUT/'overview.png'
    board.save(overview)
    generated.append(overview)
    note = OUT/'README.txt'
    lines = [
        'Pixoo visual review - real provider snapshot',
        'Captured: ' + datetime.now().astimezone().isoformat(timespec='seconds'),
        'This export independently refreshed providers with the live renderer and configuration.',
        'It is not a direct capture of the running monitor process; values can differ from its cache.',
        'Images intentionally show usage percentages and account balance; no credentials are included.',
        'Missing pages are marked in overview and are not replaced by mock data.',
        '',
    ] + [f'{label}: {state}' for label,state,_ in results] + timing_notes
    note.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    generated.append(note)
    # Include only files generated by this invocation, never configuration or credentials.
    with zipfile.ZipFile(ARCHIVE,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for path in generated:
            archive.write(path, OUT.name + '/' + path.name)
    print('\n'.join(f'{label}: {state}' for label,state,_ in results))
    print(f'Exported {sum(image is not None for _,_,image in results)} real pages to {OUT}')
    print(f'ZIP: {ARCHIVE}')

if __name__ == '__main__':
    main()
