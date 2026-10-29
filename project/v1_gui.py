import base64, ctypes, json, os, subprocess, sys, time
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QUrl, QObject, Signal
from PySide6.QtGui import QDesktopServices, QIcon, QImage, QPixmap
from PySide6.QtNetwork import QLocalSocket
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QSystemTrayIcon, QMenu, QMessageBox, QInputDialog, QFileDialog,
    QComboBox, QSpinBox, QCheckBox, QScrollArea, QLineEdit)
from v1_ipc import NAME
from v1_brand import APP_NAME,APP_ID,app_icon

DATA=Path(os.environ['PIXOO_V1_DATA'])
CONFIG=DATA/'config.json'
from v1_theme import QSS as STYLE, icon


def call(command, timeout=200, args=None):
    if os.environ.get('PIXOO_V1_AUTH_ERROR'): return None
    s=QLocalSocket(); s.connectToServer(NAME)
    if not s.waitForConnected(timeout): return None
    from v1_security import token
    from v1_wire import request, valid
    key=token()
    if not key: return None
    message=request(command,args or {},key)
    s.write((json.dumps(message,ensure_ascii=False)+'\n').encode('utf-8')); s.flush()
    if not s.waitForReadyRead(timeout): return None
    raw=bytes(s.readAll())
    while s.waitForReadyRead(30): raw += bytes(s.readAll())
    try:
        reply=json.loads(raw.decode('utf-8'))
        if not valid(reply,key) or reply.get('nonce')!=message['nonce']: return None
        return reply['data']
    except (ValueError,UnicodeError): return None

def load_config():
    try: return json.loads(CONFIG.read_text(encoding='utf-8-sig'))
    except (OSError,ValueError): return {}

def busy():
    k=ctypes.WinDLL('kernel32',use_last_error=True); k.OpenMutexW.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_wchar_p]; k.OpenMutexW.restype=ctypes.c_void_p
    h=k.OpenMutexW(0x100000,False,__import__('v1_security').mutex_name('Supervisor'))
    if h: k.CloseHandle.argtypes=[ctypes.c_void_p]; k.CloseHandle(h)
    return bool(h)

def card(title):
    f=QFrame(); f.setObjectName('card'); l=QVBoxLayout(f); l.setContentsMargins(18,16,18,16); l.setSpacing(9); l.setAlignment(Qt.AlignmentFlag.AlignTop)
    h=QLabel(title); h.setObjectName('heading'); h.setMaximumHeight(30); l.addWidget(h); return f,l

def label(t='', muted=False):
    x=QLabel(t); x.setWordWrap(True)
    if muted: x.setObjectName('muted')
    return x

def button(text, callback, parent_layout):
    b=QPushButton(text); b.clicked.connect(callback); parent_layout.addWidget(b); return b

class Results(QObject):
    ready=Signal(object)

class Window(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle(APP_NAME); self.setWindowIcon(app_icon()); self.resize(1150,750); self.setMinimumSize(950,620); self.state=None; self.results=Results(); self.results.ready.connect(self.action_result)
        root=QWidget(); root.setObjectName('base'); self.setCentralWidget(root); outer=QVBoxLayout(root); outer.setContentsMargins(12,12,12,12); outer.setSpacing(16)
        top=QHBoxLayout(); title=QLabel(APP_NAME); title.setObjectName('appTitle'); logo=QLabel(); logo.setPixmap(app_icon().pixmap(28,28)); top.addWidget(logo); top.addWidget(title); top.addStretch(); self.runlabel=label('●  未连接到 V1 后台',True); top.addWidget(self.runlabel); outer.addLayout(top)
        body=QHBoxLayout(); body.setSpacing(18); outer.addLayout(body,1); sidebar=QFrame(); sidebar.setObjectName('sidebar'); sidebar.setFixedWidth(168); nav=QVBoxLayout(sidebar); nav.setContentsMargins(7,4,12,8); nav.setSpacing(7); body.addWidget(sidebar); self.stack=QStackedWidget(); body.addWidget(self.stack,1); self.nav=[]
        for i,name in enumerate(['首页','设备','服务','显示','工具','设置']):
            b=QPushButton('  '+name); b.setIcon(icon(('home','device','service','display','tools','settings')[i])); b.setIconSize(__import__('PySide6.QtCore',fromlist=['QSize']).QSize(23,23)); b.setObjectName('nav'); b.setCheckable(True); b.clicked.connect(lambda checked=False,n=i:self.navigate(n)); nav.addWidget(b); self.nav.append(b)
        nav.addStretch()
        for builder in [self.home,self.device,self.services,self.display,self.tools,self.settings]:
            page=QWidget(); page.setObjectName('pageCanvas'); lay=QVBoxLayout(page); lay.setContentsMargins(0,2,8,8); lay.setSpacing(14); builder(lay); scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame); scroll.setWidget(page); self.stack.addWidget(scroll)
        self.navigate(0)
        self.tray=QSystemTrayIcon(self); self.tray.setIcon(app_icon()); self.tray.setToolTip(APP_NAME)
        menu=QMenu(); menu.addAction('打开控制中心',self.restore); menu.addAction('开始工作',self.start); menu.addAction('停止工作',self.stop); menu.addSeparator(); menu.addAction('退出控制中心（后台继续）',self.quit_gui); menu.addAction('停止工作并退出',self.stop_quit); self.tray.setContextMenu(menu); self.tray.activated.connect(lambda reason:self.restore() if reason==QSystemTrayIcon.ActivationReason.DoubleClick else None); self.tray.show()
        self.timer=QTimer(self); self.timer.timeout.connect(self.refresh); self.timer.start(2500); self.refresh()
    def navigate(self,i):
        self.stack.setCurrentIndex(i)
        for j,b in enumerate(self.nav): b.setChecked(i==j)
    def home(self,l):
        row=QHBoxLayout(); l.addLayout(row); left,cl=card('当前发送画面'); row.addWidget(left,4); left.setFixedHeight(480); self.frame=label('暂无成功发送的画面'); self.frame.setAlignment(Qt.AlignmentFlag.AlignCenter); self.frame.setStyleSheet('background:#090e15;color:#aab2bf;border:12px solid #16202b;border-radius:14px;'); self.frame.setFixedSize(280,280); cl.addWidget(self.frame,0,Qt.AlignmentFlag.AlignHCenter); self.page=label('当前页面：--'); cl.addWidget(self.page); self.conn=label('Pixoo 未连接'); cl.addWidget(self.conn); self.sent=label('最近画面：--',True); cl.addWidget(self.sent)
        right=QVBoxLayout(); row.addLayout(right,6); self.provider_labels={}
        for pid,name in [('go','OpenCode Go'),('cx','Codex / GPT'),('ds','DeepSeek')]:
            f,c=card(name); f.setFixedHeight(152); right.addWidget(f); self.provider_labels[pid]=label('等待后台数据'); c.addWidget(self.provider_labels[pid])
        foot=QHBoxLayout(); l.addLayout(foot); self.startstop=button('开始工作',self.toggle,foot); self.startstop.setMinimumWidth(220); foot.addStretch(); button('健康检查',self.health,foot)
    def device(self,l):
        f,c=card('Pixoo 设备'); l.addWidget(f); self.devstatus=label('等待后台连接'); c.addWidget(self.devstatus); c.addWidget(label('设备参数沿用旧配置。当前版本不会从控制中心创建第二个蓝牙连接。',True)); button('打开 Windows 蓝牙设置',lambda:QDesktopServices.openUrl(QUrl('ms-settings:bluetooth')),c)
        cfg=load_config(); self.brightness=QSpinBox(); self.brightness.setRange(0,100); self.brightness.setValue(cfg.get('brightness',50)); c.addWidget(label('屏幕亮度（保存后即时应用）')); c.addWidget(self.brightness); button('应用亮度',lambda:self.apply_patch({'brightness':self.brightness.value()}),c)
        button('重新连接',lambda:self.command('reconnect'),c); button('硬件测试（临时显示 RGB）',self.hardware,c)
        self.mac=QLineEdit(cfg.get('mac','')); self.port=QSpinBox(); self.port.setRange(1,30); self.port.setValue(cfg.get('port',1)); c.addWidget(label('高级：设备地址 / RFCOMM 端口')); c.addWidget(self.mac); c.addWidget(self.port); button('保存并重连设备',lambda:self.apply_patch({'mac':self.mac.text().strip(),'port':self.port.value()}),c)
    def services(self,l):
        self.service_checks={}
        for pid,name in [('go','OpenCode Go'),('cx','Codex / GPT'),('ds','DeepSeek API')]:
            f,c=card(name); l.addWidget(f); lab=label('等待后台数据'); c.addWidget(lab); setattr(self,'service_'+pid,lab)
            check=QCheckBox('启用服务'); check.setChecked(pid in load_config().get('enabled',[])); c.addWidget(check); self.service_checks[pid]=check
            if pid in ('go','ds'): button('更新 API Key',lambda checked=False,p=pid:self.set_key(p),c)
        button('应用服务启停',lambda:self.apply_patch({'enabled':[p for p,x in self.service_checks.items() if x.isChecked()]}),l)
        button('检查 Codex 登录环境',self.codex_check,l)
        l.addWidget(label('密钥保存在 Windows 凭据管理器。Codex 使用现有 CLI 登录。',True))
    def display(self,l):
        f,c=card('渲染与轮播'); l.addWidget(f); cfg=load_config(); self.stylebox=QComboBox(); self.stylebox.addItems(['classic','b2','b3']); self.stylebox.setCurrentText(cfg.get('display_style','b3')); c.addWidget(label('显示样式')); c.addWidget(self.stylebox)
        self.rotation=QSpinBox(); self.rotation.setRange(1,3600); self.rotation.setValue(int(cfg.get('rotation_seconds',5))); c.addWidget(label('轮播间隔（秒）')); c.addWidget(self.rotation)
        self.refresh_interval=QSpinBox(); self.refresh_interval.setRange(15,86400); self.refresh_interval.setValue(int(cfg.get('refresh_seconds',120))); c.addWidget(label('数据刷新间隔（秒）')); c.addWidget(self.refresh_interval); c.addWidget(label('运行时保存并即时应用；停止时保存供下次启动。',True));
        from page_selection import PAGE_KEYS
        self.page_checks={}
        for key,title in zip(PAGE_KEYS,['O/H','O/W','O/M','G/H','G/W','D/¥']):
            ch=QCheckBox(title); ch.setChecked(key in cfg.get('enabled_pages',list(PAGE_KEYS))); c.addWidget(ch); self.page_checks[key]=ch
        button('保存并应用',self.save_display,c); button('所选页面设计预览（不发送设备）',self.preview,c)
    def tools(self,l):
        f,c=card('诊断与工具'); l.addWidget(f); button('健康检查',self.health,c); button('导出最后成功发送的画面',self.export_frame,c); button('打开后台日志',self.open_log,c); button('蓝牙诊断',self.diagnose,c); button('导出脱敏诊断包',self.diagnostic_export,c); self.health_result=label('尚未执行健康检查',True); c.addWidget(self.health_result)
    def settings(self,l):
        f,c=card('应用设置'); l.addWidget(f); c.addWidget(label('V1 开发版 · 关闭窗口隐藏到托盘，后台继续工作')); button('读取登录自启状态',lambda:self.startup('query'),c); button('启用登录自启',lambda:self.startup('enable'),c); button('取消登录自启',lambda:self.startup('disable'),c); button('备份配置',self.backup_config,c); button('打开数据目录',lambda:QDesktopServices.openUrl(QUrl.fromLocalFile(str(DATA))),c); button('打开使用说明',self.help,c)
    def refresh(self):
        state=call('status'); rt=(state or {}).get('runtime',{}); age=time.time()-(rt.get('heartbeat_at') or 0); online=bool(state and rt.get('state')=='running' and 0<=age<=rt.get('heartbeat_timeout_seconds',30)); self.state=state if online else None
        self.runlabel.setText(('●  MOCK 测试后台' if rt.get('mode')=='MOCK' else '●  V1 监控运行中') if online else ('●  授权不可用' if os.environ.get('PIXOO_V1_AUTH_ERROR') else '●  V1 后台未连接')); self.startstop.setText('停止工作' if online else '开始工作'); self.startstop.setObjectName('stop' if online else 'start'); self.startstop.style().unpolish(self.startstop); self.startstop.style().polish(self.startstop)
        if not online:
            self.frame.clear(); self.frame.setText('暂无 V1 成功发送的画面'); self.conn.setText('Pixoo 状态未知'); self.page.setText('当前页面：--'); self.sent.setText('最近画面：--'); self.devstatus.setText('V1 后台未连接；旧版后台不会被接管。')
        else:
            rt=state['runtime']; self.conn.setText('Pixoo 已连接' if rt.get('bluetooth_connected') else 'Pixoo 未连接'); self.devstatus.setText(self.conn.text()); self.page.setText('当前发送画面：'+str(rt.get('last_page') or '--')); self.sent.setText('最近画面：'+(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(rt['last_send_at'])) if rt.get('last_send_at') else '--'))
            if rt.get('last_frame_png'):
                try:
                    img=QImage.fromData(base64.b64decode(rt['last_frame_png']),'PNG'); self.frame.setPixmap(QPixmap.fromImage(img).scaled(260,260,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.FastTransformation))
                except (ValueError,TypeError): pass
        for pid in ('go','cx','ds'):
            if not online: text='后台未连接，数据不可用'
            else:
                entries=state.get('readings',{}).get(pid,[]); meta=state.get('providers',{}).get(pid,{}); status=meta.get('status','PENDING'); last=meta.get('last_success_at'); stale=bool(last and time.time()-last>max(300,load_config().get('refresh_seconds',120)*3)); status='STALE' if status=='OK' and stale else status
                labels={'OK':'正常','STALE':'已过期','ERROR':'刷新失败','NOT_CONFIGURED':'未配置','PENDING':'等待刷新','UNSUPPORTED':'不支持'}
                parts=[]
                for x in entries:
                    value=(str(round(x['percent'],1))+'%' if x.get('percent') is not None else (str(x.get('value'))+' '+str(x.get('unit','')) if x.get('value') is not None else '--'))
                    parts.append((x.get('window') or '余额')+'  '+value)

                if pid=='ds':
                    from display.time_status import price_status
                    price=state.get('price_status','UNKNOWN'); parts.append({'PEAK':'峰时','OFF_PEAK':'谷时','UNKNOWN':'峰谷未知'}.get(price,'峰谷未知'))
                text=labels.get(status,status)+'  ·  '+('     '.join(parts) if parts else '暂无数据')+'\n最近成功：'+(time.strftime('%H:%M:%S',time.localtime(last)) if last else '--')
            if online and pid not in state.get('config',{}).get('enabled',[]): text='已停用 · 停止刷新与轮播'
            self.provider_labels[pid].setText(text); getattr(self,'service_'+pid).setText(text)
    def toggle(self): self.stop() if self.state else self.start()
    def start(self):
        if os.environ.get('PIXOO_V1_AUTH_ERROR'): QMessageBox.warning(self,'无法授权',os.environ['PIXOO_V1_AUTH_ERROR']); return
        if call('status'): return
        if busy(): QMessageBox.warning(self,'无法启动','已有 Pixoo 监控后台运行。为避免争抢蓝牙，新版不会接管或停止它。'); return
        try:
            (DATA/'stop.request').unlink(missing_ok=True)
            cmd=[sys.executable,'--supervisor'] if getattr(sys,'frozen',False) else [sys.executable,str(Path(__file__).with_name('v1_main.py')),'--supervisor']
            subprocess.Popen(cmd,env={**os.environ,'PYINSTALLER_RESET_ENVIRONMENT':'1'},stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'DETACHED_PROCESS',0)|getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0),cwd=str(DATA))
            self.runlabel.setText('●  正在启动后台…'); QTimer.singleShot(2000,self.refresh)
        except OSError as e: QMessageBox.critical(self,'启动失败',str(e))
    def stop(self):
        result=call('stop',500)
        if not result or not result.get('ok'): QMessageBox.warning(self,'停止失败','无法连接 V1 后台。旧版后台不会被停止。'); return False
        QMessageBox.information(self,'已请求停止','后台将在当前轮播周期结束后停止。'); QTimer.singleShot(2000,self.refresh); return True
    def stop_quit(self):
        if QMessageBox.question(self,'停止并退出','确定停止 V1 后台并退出控制中心？')==QMessageBox.StandardButton.Yes and self.stop(): self.quit_gui()
    def quit_gui(self): self.tray.hide(); QApplication.instance().exit(0)
    def restore(self): self.showNormal(); self.raise_(); self.activateWindow()
    def closeEvent(self,e):
        if self.tray.isVisible() and QSystemTrayIcon.isSystemTrayAvailable(): e.ignore(); self.hide(); self.tray.showMessage(APP_NAME,'控制中心已隐藏，后台继续运行。')
        else: e.accept(); self.quit_gui()
    def health(self):
        state=call('status',500)
        if not state: msg='未连接 V1 后台。若旧版正在运行，请继续使用旧版健康检查。'
        else:
            rt=state['runtime']; age=time.time()-(rt.get('heartbeat_at') or 0); msg='后台心跳：'+('正常' if 0<=age<=rt.get('heartbeat_timeout_seconds',30) else '过期或未知')+'\n蓝牙：'+('已连接' if rt.get('bluetooth_connected') else '未连接')+'\n最近成功发送：'+('有记录' if rt.get('last_send_at') else '无记录')+'\n发送成功不代表目视确认。'
        self.health_result.setText(msg); QMessageBox.information(self,'健康检查',msg)
    def set_key(self,p):
        if QMessageBox.question(self,'共享凭据','此密钥与旧版 B3 共用，更新后也会影响旧版。是否继续？') != QMessageBox.StandardButton.Yes: return
        key,ok=QInputDialog.getText(self,'更新密钥','输入新的 API Key：',QLineEdit.EchoMode.Password)
        if ok and key:
            try:
                import keyring; keyring.set_password('Pixoo AI Monitor',p,key); QMessageBox.information(self,'已保存','密钥已写入 Windows 凭据管理器，下一次刷新时生效。')
            except Exception as e: QMessageBox.critical(self,'保存失败','无法写入凭据管理器：'+type(e).__name__)
    def save_display(self):
        self.apply_patch({'display_style':self.stylebox.currentText(),'rotation_seconds':self.rotation.value(),'refresh_seconds':self.refresh_interval.value(),'enabled_pages':[p for p,x in self.page_checks.items() if x.isChecked()]})
    def export_frame(self):
        rt=(self.state or {}).get('runtime',{}); data=rt.get('last_frame_png')
        if not data: QMessageBox.warning(self,'无法导出','没有成功发送的画面。'); return
        path,_=QFileDialog.getSaveFileName(self,'导出画面','pixoo-frame.png','PNG (*.png)')
        if path:
            try: Path(path).write_bytes(base64.b64decode(data)); QMessageBox.information(self,'已导出','已保存实际发送帧。')
            except OSError as e: QMessageBox.critical(self,'导出失败',str(e))
    def open_log(self):
        p=DATA/'monitor.log'
        if p.exists(): QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))
        else: QMessageBox.information(self,'日志','尚无 V1 后台日志。')
    def help(self):
        p=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))/'使用说明.txt'
        if p.exists(): QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))
        else: QMessageBox.information(self,'使用说明','使用说明未包含在此版本中。')

    def action_result(self,result):
        box=QMessageBox(self);box.setWindowTitle(result.get('title','操作结果'));box.setText(result.get('message') or ('已执行' if result.get('ok') else result.get('error','操作失败')));box.setIcon(QMessageBox.Icon.Information if result.get('ok') else QMessageBox.Icon.Warning);box.addButton('确定',QMessageBox.ButtonRole.AcceptRole);box.exec();self.refresh()
    def background(self,fn):
        import threading
        def run():
            try: result=fn()
            except Exception as e: result={'ok':False,'error':type(e).__name__+'：'+str(e)}
            self.results.ready.emit(result)
        threading.Thread(target=run,daemon=True).start()
    def command(self,name,args=None):
        self.background(lambda:call(name,6500,args) or {'ok':False,'error':'无法连接后台或命令超时'})
    def apply_patch(self,patch):
        from v1_control import validate,save
        try: cfg=validate({**load_config(),**patch})
        except ValueError as e: QMessageBox.warning(self,'配置无效',str(e)); return
        if self.state: self.command('apply',patch)
        else:
            try: save(DATA,cfg); QMessageBox.information(self,'已保存','下次启动 V1 后台时应用。')
            except OSError as e: QMessageBox.critical(self,'保存失败',str(e))
    def hardware(self):
        if QMessageBox.question(self,'硬件测试','将暂时显示红、绿、蓝，完成后恢复画面。继续？')==QMessageBox.StandardButton.Yes: self.command('hardware')
    def codex_check(self):
        import shutil
        QMessageBox.information(self,'Codex 环境','CLI：'+('已安装' if shutil.which('codex') else '未找到')+'\n登录和额度状态由 Worker 获取，请查看服务卡片。')
    def preview(self):
        if not self.state: QMessageBox.information(self,'预览','需要后台已有的读数；当前不可用。'); return
        from page_selection import PAGE_KEYS
        key=next((p for p,x in self.page_checks.items() if x.isChecked()),None)
        if not key: return
        pid,window=PAGE_KEYS[key]; entry=next((r for r in self.state['readings'].get(pid,[]) if r['window']==window),None)
        if not entry: QMessageBox.information(self,'预览','所选页面暂无后台读数。'); return
        from providers.base import Reading
        from display.renderer import render_configured
        from decimal import Decimal
        import io
        r=Reading(pid,pid,window=window,status=entry['status'],remaining_percent=entry['percent'],remaining_value=Decimal(entry['value']) if entry['value'] is not None else None,unit=entry['unit'])
        buf=io.BytesIO(); render_configured(r,{**load_config(),'display_style':self.stylebox.currentText()}).save(buf,format='PNG')
        box=QMessageBox(self); box.setWindowTitle('设计预览 · 不发送设备'); box.setIconPixmap(QPixmap.fromImage(QImage.fromData(buf.getvalue())).scaled(256,256,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.FastTransformation)); box.exec()
    def backup_config(self):
        path,_=QFileDialog.getSaveFileName(self,'备份配置','pixoo-config.json','JSON (*.json)')
        if path:
            from v1_control import validate
            try: cfg=validate(load_config()); Path(path).write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
            except Exception as e: QMessageBox.warning(self,'备份失败',str(e))
    def diagnose(self):
        from v1_diagnostics import run
        self.background(lambda:run(call('status',1000),load_config().get('mac','')))
    def diagnostic_export(self):
        path,_=QFileDialog.getSaveFileName(self,'脱敏诊断包','pixoo-diagnostic.zip','ZIP (*.zip)')
        if not path: return
        import zipfile
        # Deliberate whitelist: exclude paths, device address, raw logs and all credentials.
        cfg=load_config(); safe={k:cfg.get(k) for k in ('display_style','brightness','enabled','enabled_pages','rotation_seconds','refresh_seconds')}
        rt=(self.state or {}).get('runtime',{}); health={k:rt.get(k) for k in ('state','heartbeat_at','bluetooth_connected','frame_result','mode')}
        try:
            with zipfile.ZipFile(path,'w') as z: z.writestr('diagnostic.json',json.dumps({'config':safe,'health':health},ensure_ascii=False,indent=2))
        except OSError as e: QMessageBox.warning(self,'导出失败',str(e))
    def startup(self,action):
        from v1_startup import update
        self.background(lambda:update(action))

from v1_views import install
install(Window)

def main():
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    app=QApplication(sys.argv);app.setApplicationName(APP_NAME);app.setApplicationDisplayName(APP_NAME);app.setWindowIcon(app_icon()); app.setStyle('Fusion'); app.setQuitOnLastWindowClosed(False); app.setStyleSheet(STYLE)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True); kernel.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_wchar_p]; kernel.CreateMutexW.restype=ctypes.c_void_p
    gui_name='Local\\PixooAIMonitorV1GUI'
    if os.environ.get('PIXOO_V1_TEST')=='1':
        from v1_security import scope
        gui_name+='Test_'+scope()
    gui_mutex=kernel.CreateMutexW(None,False,gui_name)
    if not gui_mutex or ctypes.get_last_error()==183:
        QMessageBox.information(None,APP_NAME,'控制中心已打开，请使用系统托盘恢复窗口。'); return 1
    w=Window(); w.navigate(int(os.environ.get('PIXOO_SCREENSHOT_PAGE','0'))); w.show()
    if os.environ.get('PIXOO_GUI_TEST'):
        def gui_test():
            output=Path(os.environ['PIXOO_GUI_TEST']); output.mkdir(parents=True,exist_ok=True)
            w.close(); hidden=not w.isVisible(); w.restore(); restored=w.isVisible()
            for i in range(6):
                w.navigate(i); app.processEvents(); w.grab().save(str(output/('page-'+str(i)+'.png')))
            (output/'gui-results.json').write_text(json.dumps({'hidden':hidden,'restored':restored,'connected':bool(w.state),'mode':((w.state or {}).get('runtime') or {}).get('mode')}),encoding='utf-8')
            w.quit_gui()
        QTimer.singleShot(1800,gui_test)
    if os.environ.get('PIXOO_SCREENSHOT'):
        def screenshot(): w.grab().save(os.environ['PIXOO_SCREENSHOT']); w.quit_gui()
        QTimer.singleShot(1200,screenshot)
    return app.exec()
