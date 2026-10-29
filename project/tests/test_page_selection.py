import pytest
from page_selection import select_readings, validate_pages
from providers.base import Reading


def test_selects_only_enabled_provider_and_page():
    readings = [Reading('go', 'go', window='5H'), Reading('go', 'go', window='7D'),
                Reading('cx', 'cx', window='5H'), Reading('ds', 'ds', unit='CNY')]
    assert select_readings(readings, ['go', 'ds'], ['go_7d', 'cx_5h', 'ds_cny']) == [readings[1], readings[3]]


def test_preserves_provider_error_without_a_window():
    error = Reading('go', 'go', status='ERROR')
    assert select_readings([error], ['go'], ['go_5h']) == [error]


@pytest.mark.parametrize('providers,pages', [([], ['go_5h']), (['go'], []), (['go'], ['unknown']), (['go'], ['go_5h', 'go_5h'])])
def test_invalid_or_empty_configuration_rejected(providers, pages):
    with pytest.raises(ValueError):
        validate_pages(providers, pages)
