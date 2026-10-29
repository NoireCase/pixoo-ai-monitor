import pytest
from providers.base import Reading
from display.renderer import FONT,render

def test_all_status_message_characters_have_glyphs():
    for ch in set('SET ERROLD'):
        assert ch in FONT
        if ch!=' ': assert '1' in FONT[ch]

@pytest.mark.parametrize('style',['classic','b2','b3'])
def test_old_displays_middle_l(style):
    r=Reading('go','OpenCode Go',remaining_percent=72,window='5H',status='STALE')
    im=render(r,style=style)
    y=11 if style=='classic' else 7
    purple=(180,80,230)
    assert all(im.getpixel((6,y+dy))==purple for dy in range(5))
    assert all(im.getpixel((x,y+4))==purple for x in range(6,9))
