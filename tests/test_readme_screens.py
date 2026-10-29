import re
from pathlib import Path
from unittest.mock import patch
from PIL import Image,ImageChops
from scripts.generate_readme_previews import make_previews,groups

ROOT=Path(__file__).resolve().parents[1]

def test_screens_generated_offline_and_pixel_exact(tmp_path):
    with patch('socket.socket',side_effect=AssertionError('documentation must be offline')),patch('keyring.get_password',side_effect=AssertionError('no credential access')):
        files=make_previews(tmp_path)
    assert len(files)==59
    for cases in groups().values():
        for name,_,_,_ in cases:
            with Image.open(tmp_path/(name+'_16.png')) as a,Image.open(tmp_path/(name+'_320.png')) as b:
                assert a.mode==b.mode=='RGB' and a.size==(16,16) and b.size==(320,320)
                assert ImageChops.difference(a.resize((320,320),Image.Resampling.NEAREST),b).getbbox() is None

def test_committed_native_examples_match_renderer():
    from display.renderer import render_configured
    from scripts.generate_readme_previews import CFG
    for cases in groups().values():
        for name,_,reading,now in cases:
            with Image.open(ROOT/'docs'/'screens'/(name+'_16.png')) as image:
                assert image.tobytes()==render_configured(reading,CFG,now).tobytes()

def test_readme_image_links_exist():
    readme=(ROOT/'README.md').read_text(encoding='utf-8-sig')
    links=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',readme)
    assert len(links)==5
    assert all(link.startswith('docs/screens/') and (ROOT/link).is_file() for link in links)
