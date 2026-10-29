"""Test transport: never constructs a Bluetooth socket or calls a provider."""
class TestPixoo:
    def __init__(self,mac,port): self.mac=mac; self.port=port; self.sock=None
    def connect(self): self.sock=True
    def close(self): self.sock=None
    def brightness(self,n): pass
    def show(self,img):
        assert img.mode=='RGB' and img.size==(16,16)
