import unittest
from decimal import Decimal
from PIL import Image
from providers.sources import opencode, deepseek, codex_parse
from providers.base import Reading
from display.renderer import render,color,amount
from drivers.pixoo import Pixoo
class Tests(unittest.TestCase):
    def test_percent_boundaries(self):
        for n in [0,19,20,50,100]:
            image=render(Reading('go','GO',remaining_percent=n))
            self.assertEqual((image.mode,image.size),('RGB',(16,16)))
        self.assertEqual(color(19),(255,55,55)); self.assertEqual(color(20),(255,190,0)); self.assertEqual(color(50),(255,190,0)); self.assertEqual(color(100),(0,220,90))
    def test_amount(self):
        for v in [None,-1,0,10,100,1000,10**100]: render(Reading('ds','DS',remaining_value=v,unit='CNY'))
        self.assertEqual(amount(None),'-')
    def test_go(self):
        r=opencode({'usage':{'rolling':{'status':'ok','percent':28,'resetsAt':'x'}}})
        self.assertEqual(r[0].remaining_percent,72); self.assertEqual(r[0].window,'5H')
    def test_ds(self):
        b=lambda c,n:{'currency':c,'total_balance':n,'granted_balance':'0','topped_up_balance':n}
        r=deepseek({'is_available':True,'balance_infos':[b('USD','100'),b('CNY','1.23')]})[0]
        self.assertEqual(r.remaining_value,Decimal('1.23')); self.assertEqual(r.unit,'CNY'); self.assertIsNone(r.remaining_percent)
    def test_codex(self):
        r=codex_parse({'rateLimits':{'primary':{'usedPercent':20,'windowDurationMins':300},'secondary':{'usedPercent':50,'windowDurationMins':10080}}})
        self.assertEqual([x.remaining_percent for x in r],[80,50])
    def test_packet(self):
        class Sock:
            data=b''
            def sendall(self,data): self.data=data
        p=Pixoo('00'); p.sock=Sock(); p.show(Image.new('RGB',(16,16),'red'))
        self.assertEqual(p.sock.data[0],1); self.assertEqual(p.sock.data[-1],2); self.assertEqual(p.sock.data[3],0x44)
if __name__=='__main__': unittest.main()

class IsolationTests(unittest.TestCase):
    def test_codex_bucket_and_duration(self):
        data={'rateLimits':None,'rateLimitsByLimitId':{'codex':{'primary':{'usedPercent':25,'windowDurationMins':60}}}}
        reading=codex_parse(data)[0]
        self.assertEqual(reading.remaining_percent,75)
        self.assertEqual(reading.window,'60M')
        self.assertEqual(reading.details['window_duration_minutes'],60)
    def test_codex_exit_reported_without_timeout(self):
        import io
        from unittest.mock import patch
        from providers.sources import codex
        class Process:
            def __init__(self):
                self.stdin=io.StringIO(); self.stdout=io.StringIO(); self.stderr=io.StringIO('Could not find home directory\n'); self.returncode=1
            def wait(self,timeout=None): return self.returncode
            def poll(self): return self.returncode
        with patch('providers.sources.shutil.which',return_value='codex'), patch('providers.sources.subprocess.Popen',return_value=Process()):
            with self.assertRaisesRegex(RuntimeError,'exited during initialize: exit=1; home unavailable'): codex()
    def test_no_credentials(self):
        from unittest.mock import patch
        from providers.sources import fetch
        with patch('providers.sources.secret',return_value=None):
            self.assertEqual(fetch('go')[0].status,'NOT_CONFIGURED')
            self.assertEqual(fetch('ds')[0].status,'NOT_CONFIGURED')
    def test_stale_and_isolation(self):
        import time
        from unittest.mock import patch
        from app import Monitor,DEFAULT
        from providers.base import Reading
        monitor=Monitor({**DEFAULT,'enabled':['go','ds'],'refresh_seconds':15})
        monitor.data['go']=[Reading('go','GO',remaining_percent=42)]
        def fake(pid):
            if pid=='go': raise OSError('network')
            return [Reading('ds','DS',remaining_value=Decimal('5'))]
        with patch('app.fetch',side_effect=fake):
            monitor.refresh()
            deadline=time.time()+2
            while time.time()<deadline:
                if 'ds' in monitor.data and monitor.data['go'][0].status=='STALE': break
                time.sleep(.01)
            monitor.stop.set()
        self.assertEqual(monitor.data['go'][0].remaining_percent,42)
        self.assertEqual(monitor.data['go'][0].status,'STALE')
        self.assertEqual(monitor.data['ds'][0].status,'OK')
