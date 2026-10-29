from v1_wire import request,valid,response

def test_wire_tamper_wrong_key_and_nonce():
    message=request('stop',{},'a'*64)
    assert valid(message,'a'*64)
    assert not valid(message,'b'*64)
    changed={**message,'command':'hardware'}
    assert not valid(changed,'a'*64)
    reply=response({'ok':True},message['nonce'],'a'*64)
    assert valid(reply,'a'*64) and reply['nonce']==message['nonce']
