import pytest
from v1_control import validate
from app import DEFAULT
from page_selection import PAGE_KEYS

def cfg(): return {**DEFAULT,'display_style':'b3','enabled_pages':list(PAGE_KEYS)}
@pytest.mark.parametrize('patch',[{'brightness':101},{'mac':'bad'},{'enabled':[]},{'enabled_pages':[]},{'api_key':'secret'},{'rotation_seconds':True}])
def test_reject_invalid_config(patch):
    with pytest.raises(ValueError): validate({**cfg(),**patch})
def test_valid_config(): assert validate(cfg())['display_style']=='b3'
