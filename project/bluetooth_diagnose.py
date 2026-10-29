"""Read-only Windows Bluetooth Classic inventory; no active inquiry or pairing."""
import ctypes
import json
import os
import subprocess
from ctypes import wintypes

bt = ctypes.WinDLL('Bthprops.cpl', use_last_error=True)
kernel = ctypes.WinDLL('kernel32', use_last_error=True)

class SystemTime(ctypes.Structure):
    _fields_ = [(x, wintypes.WORD) for x in ('year','month','dayofweek','day','hour','minute','second','milliseconds')]
class Address(ctypes.Union):
    _fields_ = [('value', ctypes.c_ulonglong), ('bytes', ctypes.c_ubyte * 6)]
class FindRadio(ctypes.Structure):
    _fields_ = [('size', wintypes.DWORD)]
class RadioInfo(ctypes.Structure):
    _fields_ = [('size', wintypes.DWORD), ('address', Address), ('name', wintypes.WCHAR * 248), ('class_of_device', wintypes.ULONG), ('subversion', wintypes.USHORT), ('manufacturer', wintypes.USHORT)]
class Search(ctypes.Structure):
    _fields_ = [('size', wintypes.DWORD), ('authenticated', wintypes.BOOL), ('remembered', wintypes.BOOL), ('unknown', wintypes.BOOL), ('connected', wintypes.BOOL), ('inquiry', wintypes.BOOL), ('timeout', ctypes.c_ubyte), ('radio', wintypes.HANDLE)]
class DeviceInfo(ctypes.Structure):
    _fields_ = [('size', wintypes.DWORD), ('address', Address), ('class_of_device', wintypes.ULONG), ('connected', wintypes.BOOL), ('remembered', wintypes.BOOL), ('authenticated', wintypes.BOOL), ('last_seen', SystemTime), ('last_used', SystemTime), ('name', wintypes.WCHAR * 248)]

bt.BluetoothFindFirstRadio.argtypes = [ctypes.POINTER(FindRadio), ctypes.POINTER(wintypes.HANDLE)]
bt.BluetoothFindFirstRadio.restype = wintypes.HANDLE
bt.BluetoothFindNextRadio.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.HANDLE)]
bt.BluetoothFindNextRadio.restype = wintypes.BOOL
bt.BluetoothFindRadioClose.argtypes = [wintypes.HANDLE]
bt.BluetoothGetRadioInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(RadioInfo)]
bt.BluetoothGetRadioInfo.restype = wintypes.DWORD
bt.BluetoothFindFirstDevice.argtypes = [ctypes.POINTER(Search), ctypes.POINTER(DeviceInfo)]
bt.BluetoothFindFirstDevice.restype = wintypes.HANDLE
bt.BluetoothFindNextDevice.argtypes = [wintypes.HANDLE, ctypes.POINTER(DeviceInfo)]
bt.BluetoothFindNextDevice.restype = wintypes.BOOL
bt.BluetoothFindDeviceClose.argtypes = [wintypes.HANDLE]
kernel.CloseHandle.argtypes = [wintypes.HANDLE]

def masked(address):
    value = f'{address.value:012X}'
    return ':'.join([value[i:i+2] for i in range(0,6,2)] + ['**','**','**'])

def inventory():
    lines=[]
    params=FindRadio(ctypes.sizeof(FindRadio)); radio=wintypes.HANDLE()
    handle=bt.BluetoothFindFirstRadio(ctypes.byref(params),ctypes.byref(radio))
    if not handle: return [f'BluetoothFindFirstRadio failed: Windows error {ctypes.get_last_error()}']
    try:
        while True:
            try:
                info=RadioInfo(); info.size=ctypes.sizeof(info)
                error=bt.BluetoothGetRadioInfo(radio,ctypes.byref(info))
                lines.append(f'Radio: name={info.name!r} address={masked(info.address)} manufacturer_id={info.manufacturer} class=0x{info.class_of_device:06X} status={error}')
                search=Search(ctypes.sizeof(Search),True,True,False,True,False,0,radio)
                device=DeviceInfo(); device.size=ctypes.sizeof(device)
                found=bt.BluetoothFindFirstDevice(ctypes.byref(search),ctypes.byref(device))
                if found:
                    try:
                        while True:
                            if 'pixoo' in device.name.lower() or 'divoom' in device.name.lower():
                                lines.append(f'Device: name={device.name!r} address={masked(device.address)} authenticated={bool(device.authenticated)} remembered={bool(device.remembered)} connected={bool(device.connected)} class=0x{device.class_of_device:06X} last_seen={device.last_seen.year:04}-{device.last_seen.month:02}-{device.last_seen.day:02}')
                            device=DeviceInfo(); device.size=ctypes.sizeof(device)
                            if not bt.BluetoothFindNextDevice(found,ctypes.byref(device)): break
                    finally: bt.BluetoothFindDeviceClose(found)
                else: lines.append(f'BluetoothFindFirstDevice: Windows error {ctypes.get_last_error()}')
            finally: kernel.CloseHandle(radio)
            radio=wintypes.HANDLE()
            if not bt.BluetoothFindNextRadio(handle,ctypes.byref(radio)): break
    finally: bt.BluetoothFindRadioClose(handle)
    return lines

def pnp_inventory(mac):
    """Best-effort PnP status; never emit instance IDs or full addresses."""
    script = r'''$ErrorActionPreference='Stop'
$devices=@(Get-PnpDevice -PresentOnly -Class Bluetooth)
$adapters=@($devices | Where-Object { $_.InstanceId -match '^USB\\VID_' })
$drivers=@(Get-CimInstance Win32_PnPSignedDriver -Filter "DeviceClass='BLUETOOTH'" | Where-Object { $_.DeviceID -match '^USB\\VID_' })
$target=@($devices | Where-Object { $_.InstanceId -like ('*'+$env:PIXOO_DIAG_TARGET+'*') } | Select-Object FriendlyName,Status,Class,@{n='Transport';e={($_.InstanceId -split '\\')[0]}})
@{adapters=@($adapters | Select-Object FriendlyName,Status,Problem); drivers=@($drivers | Select-Object DeviceName,DriverVersion,Manufacturer); target=$target} | ConvertTo-Json -Depth 4 -Compress'''
    try:
        raw=mac.replace(':','').replace('-','')
        env={**os.environ,'PIXOO_DIAG_TARGET':raw}
        result=subprocess.run(['powershell','-NoProfile','-Command',script],capture_output=True,text=True,timeout=10,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if result.returncode: return ['PnP inventory unavailable: permission denied or query failed']
        data=json.loads(result.stdout)
        return [f'PnP {name}: {json.dumps(data.get(name,[]),ensure_ascii=True)}' for name in ('adapters','drivers','target')]
    except (OSError,ValueError,subprocess.TimeoutExpired): return ['PnP inventory unavailable: query failed or timed out']

if __name__=='__main__':
    print('\n'.join(inventory()))
