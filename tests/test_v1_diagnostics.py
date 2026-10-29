from v1_diagnostics import summarize

def test_user_diagnosis_hides_raw_and_unicode_escapes():
    lines=["Radio: name='pc' status=0","Device: name='Pixoo' authenticated=True connected=True",r'PnP adapters: [{"FriendlyName":"\u84dd\u7259","Status":"OK"}]']
    result=summarize(lines,{'runtime':{'state':'running','bluetooth_connected':True,'last_send_at':1}})
    assert '工作正常' in result and '已配对' in result and '当前连接正常' in result
    assert '\\u' not in result and 'manufacturer_id' not in result and 'authenticated' not in result

def test_unknown_diagnosis_is_not_claimed_healthy():
    result=summarize(['PnP inventory unavailable: permission denied'])
    assert '暂时无法确认' in result and '当前连接正常' not in result

def test_disconnected_diagnosis_has_action():
    result=summarize([],{'runtime':{'state':'running','bluetooth_connected':False}})
    assert '尚未连接' in result and '重新连接' in result
