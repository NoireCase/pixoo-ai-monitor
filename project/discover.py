import json, winreg
from pathlib import Path
path=Path(__file__).resolve().parent/'config.json'
if not path.exists(): path.write_text((path.parent/'config.example.json').read_text(encoding='utf-8-sig'),encoding='utf-8')
c=json.loads(path.read_text(encoding='utf-8-sig'))
if c.get('mac'):
    print('Existing MAC kept.'); raise SystemExit
matches=[]
try:
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices') as root:
        for i in range(winreg.QueryInfoKey(root)[0]):
            name=winreg.EnumKey(root,i)
            try:
                with winreg.OpenKey(root,name) as dev: raw=winreg.QueryValueEx(dev,'Name')[0]
                label=raw.decode('utf-8','replace').rstrip('\0') if isinstance(raw,bytes) else str(raw)
                if ('pixoo' in label.lower() or 'divoom' in label.lower()) and len(name)==12:
                    matches.append((label,':'.join(name[j:j+2] for j in range(0,12,2)).upper()))
            except OSError: pass
except OSError: print('Paired-device registry unavailable; enter MAC manually.')
if len(matches)==1:
    c['mac']=matches[0][1]; path.write_text(json.dumps(c,indent=2),encoding='utf-8'); print('Registry device candidate found:',matches[0][0],matches[0][1][:8]+':**:**:**', '(pairing/transport not confirmed)')
elif len(matches)>1: print('Multiple Divoom devices found; enter the correct MAC manually:',matches)
else: print('No paired Pixoo found; pair in Windows Settings and retry.')
