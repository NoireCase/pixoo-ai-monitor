# Adapted from PixooCtrl, Copyright (c) 2026 Andreas Schiffler, MIT; see LICENSE-PixooCtrl.
import socket, time, math, logging
from datetime import datetime

def mask_mac(mac):
    parts = mac.replace('-', ':').split(':')
    return ':'.join(parts[:3] + ['**'] * 3) if len(parts) == 6 else '<invalid>'

def error_details(exc):
    return f'{type(exc).__name__}: errno={getattr(exc, "errno", None)} winerror={getattr(exc, "winerror", None)} message={str(exc)}'

class Pixoo:
    def __init__(self,mac,port=1): self.mac,self.port,self.sock=mac,port,None
    def connect(self):
        logging.info('RFCOMM connect start=%s target=%s channel=%s timeout=8s', datetime.now().isoformat(), mask_mac(self.mac), self.port)
        s=None
        try:
            s=socket.socket(socket.AF_BLUETOOTH,socket.SOCK_STREAM,socket.BTPROTO_RFCOMM)
            s.settimeout(8); s.connect((self.mac,self.port)); s.settimeout(5); time.sleep(.5); self.sock=s
            logging.info('RFCOMM connect end=%s connected=true', datetime.now().isoformat())
        except Exception as exc:
            logging.warning('RFCOMM connect end=%s connected=false %s', datetime.now().isoformat(), error_details(exc))
            if s: s.close()
            raise
    def close(self):
        if self.sock: self.sock.close(); self.sock=None
    def send(self,cmd,args):
        size=len(args)+3; frame=[1,size&255,size>>8,cmd]+args; checksum=sum(frame[1:])&65535
        try:
            self.sock.sendall(bytes(frame+[checksum&255,checksum>>8,2]))
            logging.info('RFCOMM send command=0x%02X success=true bytes=%d', cmd, len(frame)+3)
        except OSError as exc:
            logging.warning('RFCOMM send command=0x%02X success=false %s', cmd, error_details(exc))
            raise
    def brightness(self,n): self.send(0x74,[max(0,min(100,int(n)))])
    def show(self,img):
        if img.size!=(16,16) or img.mode!='RGB': raise ValueError('Expected 16x16 RGB')
        palette=[]; indexes=[]; lookup={}
        for color in img.getdata():
            if color not in lookup: lookup[color]=len(palette); palette.append(color)
            indexes.append(lookup[color])
        bits=max(1,math.ceil(math.log2(len(palette)))); acc=0; count=0; pixels=[]
        for i in indexes:
            acc|=i<<count; count+=bits
            while count>=8: pixels.append(acc&255); acc>>=8; count-=8
        if count: pixels.append(acc&255)
        colors=[v for rgb in palette for v in rgb]; size=7+len(colors)+len(pixels)
        self.send(0x44,[0,10,10,4,0xaa,size&255,size>>8,0,0,0,len(palette)%256]+colors+pixels)
