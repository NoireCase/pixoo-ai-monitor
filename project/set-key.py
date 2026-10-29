try: import keyring
except ImportError:
    print('keyring is not installed; rerun setup.ps1 with internet access.'); raise SystemExit(1)
name=input('Provider (go or ds): ').strip().lower()
if name not in ('go','ds'): raise SystemExit('Invalid provider')
print('The API key will be visible in this window. Paste it and check it before saving.')
key=input('API key (visible): ')
if not key:
    raise SystemExit('No key entered. Nothing was saved.')
if input('Save this key to Windows Credential Manager? (y/N): ').strip().lower() != 'y':
    raise SystemExit('Cancelled. Nothing was saved.')
keyring.set_password('Pixoo AI Monitor',name,key)
print('Saved to Windows Credential Manager.')
