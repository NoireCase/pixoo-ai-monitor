"""Authenticated request/response envelopes; the IPC capability never crosses the pipe."""
import hashlib,hmac,json,secrets,time

def sign(body,key): return hmac.new(key.encode(),json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode(),hashlib.sha256).hexdigest()
def request(command,args,key):
    body={'command':command,'args':args,'nonce':secrets.token_hex(24),'at':time.time()}
    return {**body,'signature':sign(body,key)}
def valid(message,key):
    if not key or not isinstance(message,dict): return False
    body={k:v for k,v in message.items() if k!='signature'}
    return hmac.compare_digest(str(message.get('signature','')),sign(body,key))
def response(data,nonce,key):
    body={'data':data,'nonce':nonce}
    return {**body,'signature':sign(body,key)}
