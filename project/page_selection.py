"""V1 page selection, independent from transport and GUI.

Absent enabled_pages keeps the legacy B3 selection path unchanged.
"""
PAGE_KEYS = {
    'go_5h': ('go', '5H'), 'go_7d': ('go', '7D'), 'go_30d': ('go', '30D'),
    'cx_5h': ('cx', '5H'), 'cx_7d': ('cx', '7D'), 'ds_cny': ('ds', ''),
}


def validate_pages(enabled_providers, enabled_pages):
    """Require at least one selectable page belonging to an enabled provider."""
    if not isinstance(enabled_pages, list) or any(p not in PAGE_KEYS for p in enabled_pages):
        raise ValueError('轮播页面配置无效')
    if len(set(enabled_pages)) != len(enabled_pages):
        raise ValueError('轮播页面存在重复项')
    if not any(PAGE_KEYS[p][0] in enabled_providers for p in enabled_pages):
        raise ValueError('请至少启用一个已启用服务的轮播页面')


def select_readings(readings, enabled_providers, enabled_pages):
    """Select real readings only; retain provider errors lacking a window."""
    validate_pages(enabled_providers, enabled_pages)
    selected = {PAGE_KEYS[p] for p in enabled_pages if PAGE_KEYS[p][0] in enabled_providers}
    providers = {p for p, _ in selected}
    return [r for r in readings if r.provider_id in providers and
            ((r.provider_id, r.window or '') in selected or
             (not r.window and r.provider_id != 'ds' and r.status != 'OK'))]
