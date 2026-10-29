"""User-scoped pipe names and capability stored in Windows Credential Manager."""
import os, hashlib, secrets, keyring
from pathlib import Path

def scope(): return hashlib.sha256(str(Path(os.environ.get('PIXOO_V1_DATA','.')).resolve()).lower().encode()).hexdigest()[:16]
def token(create=False):
    if os.environ.get('PIXOO_V1_TEST')=='1': return os.environ.get('PIXOO_V1_TEST_AUTH')
    name='ipc-'+scope(); value=keyring.get_password('Pixoo AI Monitor V1 IPC',name)
    if not value and create:
        value=secrets.token_hex(32); keyring.set_password('Pixoo AI Monitor V1 IPC',name,value)
    return value

def mutex_name(kind):
    if os.environ.get('PIXOO_V1_TEST')=='1': return 'Local\\PixooV1Test'+kind+'_'+scope()
    return 'Local\\PixooAIMonitor'+('Supervisor' if kind=='Supervisor' else 'Singleton')
