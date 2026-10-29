"""Presentation-only page builders. Worker, IPC and existing actions stay in v1_gui."""
import base64,time
from pathlib import Path
from PySide6.QtCore import Qt,QUrl
from PySide6.QtGui import QDesktopServices,QImage,QPixmap
from PySide6.QtWidgets import QWidget,QFrame,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPushButton,QSlider,QSpinBox,QLineEdit,QComboBox,QCheckBox
from v1_theme import card,text,icon,Switch,QuotaCard

def btn(title,fn,layout,kind=''):
    b=QPushButton(title);b.clicked.connect(fn)
    if kind:b.setObjectName(kind)
    layout.addWidget(b);return b

def heading(l,title,subtitle):
    title_label=text(title,'title');title_label.setFixedHeight(34);sub=text(subtitle,'muted');sub.setFixedHeight(24);l.addWidget(title_label);l.addWidget(sub)

def frame(size=280):
    f=QLabel('暂无成功发送的画面');f.setAlignment(Qt.AlignmentFlag.AlignCenter);f.setFixedSize(size,size);f.setStyleSheet('background:#060b10;color:#8994a3;border:14px solid #111923;border-radius:16px;');return f

def row(l,name,control):
    h=QHBoxLayout();h.addWidget(text(name,'muted'),1);h.addWidget(control,2);l.addLayout(h)

def home(self,l):
    h=QHBoxLayout();h.setSpacing(16);l.addLayout(h,1)
    left=QVBoxLayout();left.setSpacing(12);h.addLayout(left,1)
    panel=QFrame();panel.setObjectName('previewPanel');pv=QVBoxLayout(panel);pv.setContentsMargins(13,13,13,13);self.frame=frame(282);pv.addWidget(self.frame,0,Qt.AlignmentFlag.AlignHCenter)
    self.page=text('当前发送画面：--');self.page.setAlignment(Qt.AlignmentFlag.AlignCenter);pv.addWidget(self.page);left.addWidget(panel)
    self.conn=text('Pixoo 状态未知');self.conn.setAlignment(Qt.AlignmentFlag.AlignCenter);self.conn.setStyleSheet('font-size:18px;color:#8a94a2;');left.addSpacing(16);connection=QHBoxLayout();connection.addStretch();bt=QLabel();bt.setPixmap(icon('device','#2768ff',22).pixmap(22,22));connection.addWidget(bt);connection.addWidget(self.conn);connection.addStretch();left.addLayout(connection);left.addSpacing(16)
    self.sent=text('最近画面：--');self.sent.setAlignment(Qt.AlignmentFlag.AlignCenter);left.addWidget(self.sent)
    self.sendtime=text('更新时间：--','muted');self.sendtime.setAlignment(Qt.AlignmentFlag.AlignCenter);left.addWidget(self.sendtime);left.addStretch(1)
    right=QVBoxLayout();right.setSpacing(14);h.addLayout(right,1.9 if False else 2)
    self.home_cards={};self.provider_labels={}
    for pid,name,windows in [('go','OpenCode Go',['5H','7D','30D']),('cx','Codex / GPT',['5H','7D']),('ds','DeepSeek',[])]:
        c=QuotaCard(name,windows,pid=='ds');right.addWidget(c,5 if pid=='ds' else 6);self.home_cards[pid]=c;self.provider_labels[pid]=QLabel(self)
        self.provider_labels[pid].hide()
    foot=QHBoxLayout();foot.setContentsMargins(0,15,0,0);l.addLayout(foot)
    self.startstop=btn('开始工作',self.toggle,foot,'start');self.startstop.setMinimumWidth(290);self.startstop.setMinimumHeight(48);foot.addStretch();health=btn('健康检查',self.health,foot);health.setIcon(icon('health'));health.setMinimumWidth(274);health.setMinimumHeight(44)

def device(self,l):
    from v1_gui import load_config
    cfg=load_config();heading(l,'Pixoo 设备','硬件连接、屏幕亮度与安全诊断。')
    c,cl=card();l.addWidget(c);h=QHBoxLayout();cl.addLayout(h)
    devicepic=text('PIXOO\n\n16 × 16');devicepic.setAlignment(Qt.AlignmentFlag.AlignCenter);devicepic.setFixedSize(156,156);devicepic.setStyleSheet('background:#0c141d;border:20px solid #121d27;border-radius:18px;color:#73d89a;font-size:20px;font-weight:600;');h.addWidget(devicepic);h.addSpacing(22)
    info=QVBoxLayout();h.addLayout(info,1);title=QHBoxLayout();title.addWidget(text('Divoom Pixoo','heading'));title.addStretch();self.devstatus=text('状态未知');title.addWidget(self.devstatus);info.addLayout(title)
    address=cfg.get('mac','');masked=':'.join(address.split(':')[:2]+['••','••','••']+address.split(':')[-1:]) if address else '未配置'
    for k,v in [('连接方式','Bluetooth Classic / RFCOMM'),('设备地址',masked),('RFCOMM 端口',str(cfg.get('port',1)))]:
        r=QHBoxLayout();r.addWidget(text(k,'muted'),1);r.addWidget(text(v),2);info.addLayout(r)
    bright,bl=card('屏幕亮度');l.addWidget(bright);r=QHBoxLayout();r.addWidget(text('由后台即时应用，不新增蓝牙连接','muted'),1);self.brightvalue=text(str(cfg.get('brightness',50))+'%');r.addWidget(self.brightvalue);bl.addLayout(r)
    self.brightness=QSlider(Qt.Orientation.Horizontal);self.brightness.setRange(0,100);self.brightness.setValue(cfg.get('brightness',50));self.brightness.valueChanged.connect(lambda v:self.brightvalue.setText(str(v)+'%'));bl.addWidget(self.brightness)
    br=QHBoxLayout();br.addWidget(text('0%','muted'));br.addStretch();btn('应用亮度',lambda:self.apply_patch({'brightness':self.brightness.value()}),br);br.addStretch();br.addWidget(text('100%','muted'));bl.addLayout(br)
    actions,al=card('连接与诊断');l.addWidget(actions);al.addWidget(text('硬件测试将临时显示红、绿、蓝，然后恢复轮播。','muted'));r=QHBoxLayout();al.addLayout(r)
    btn('重新连接',lambda:self.command('reconnect'),r);btn('Windows 蓝牙设置',lambda:QDesktopServices.openUrl(QUrl('ms-settings:bluetooth')),r);btn('硬件测试',self.hardware,r)
    advanced=QWidget();ad=QHBoxLayout(advanced);ad.setContentsMargins(0,0,0,0);self.mac=QLineEdit(address);self.mac.setPlaceholderText('设备地址');self.port=QSpinBox();self.port.setRange(1,30);self.port.setValue(cfg.get('port',1));ad.addWidget(self.mac,3);ad.addWidget(self.port);btn('保存并重连',lambda:self.apply_patch({'mac':self.mac.text().strip(),'port':self.port.value()}),ad);advanced.hide()
    toggle=QPushButton('高级设备设置 ▸');toggle.setCheckable(True);toggle.toggled.connect(advanced.setVisible);al.addWidget(toggle);al.addWidget(advanced)

def services(self,l):
    from v1_gui import load_config
    heading(l,'AI 服务管理','管理额度来源、密钥与登录状态；停用服务将停止对应刷新与轮播。');self.service_cards={};self.service_checks={}
    for pid,name,windows in [('go','OpenCode Go',['5H','7D','30D']),('cx','Codex / GPT',['5H','7D']),('ds','DeepSeek API',[])]:
        c=QuotaCard(name,windows,pid=='ds',True);l.addWidget(c,1);self.service_cards[pid]=c
        check=Switch();check.setAccessibleName(name+' 启用服务');check.setChecked(pid in load_config().get('enabled',[]));self.service_checks[pid]=check;c.extra.addWidget(check)
        footer=QHBoxLayout();c.layout().addLayout(footer);footer.addWidget(text('当前 CLI 登录环境' if pid=='cx' else '凭据保存于 Windows 凭据管理器','muted'),1);btn('检查登录' if pid=='cx' else '更新密钥',self.codex_check if pid=='cx' else lambda checked=False,p=pid:self.set_key(p),footer)
        lab=QLabel(self);lab.hide();setattr(self,'service_'+pid,lab)
    foot=QHBoxLayout();foot.addStretch();btn('应用服务启停',lambda:self.apply_patch({'enabled':[p for p,x in self.service_checks.items() if x.isChecked()]}),foot,'primary');l.addLayout(foot)

def display(self,l):
    from v1_gui import load_config
    from page_selection import PAGE_KEYS
    cfg=load_config();heading(l,'显示设置','调整渲染、轮播节奏与展示页面；设计预览不影响实体屏幕。')
    h=QHBoxLayout();l.addLayout(h,1);p,pl=card('当前屏幕预览');h.addWidget(p,4);pl.addWidget(text('后台最近一次成功发送的原始帧','muted'));self.display_frame=frame(228);pl.addWidget(self.display_frame,0,Qt.AlignmentFlag.AlignCenter);pl.addStretch()
    c,cl=card('渲染与轮播');h.addWidget(c,6);self.stylebox=QComboBox();self.stylebox.addItems(['classic','b2','b3']);self.stylebox.setCurrentText(cfg.get('display_style','b3'));row(cl,'显示样式',self.stylebox)
    self.rotation=QSpinBox();self.rotation.setRange(1,3600);self.rotation.setSuffix(' 秒');self.rotation.setValue(int(cfg.get('rotation_seconds',5)));row(cl,'每页轮播间隔',self.rotation)
    self.refresh_interval=QSpinBox();self.refresh_interval.setRange(15,86400);self.refresh_interval.setSuffix(' 秒');self.refresh_interval.setValue(int(cfg.get('refresh_seconds',120)));row(cl,'额度刷新间隔',self.refresh_interval)
    cl.addWidget(text('保存后由后台校验并应用；后台停止时保存供下次启动。','muted'));cl.addStretch();btn('设计预览 · 不发送设备',self.preview,cl)
    c,cl=card('轮播页面');l.addWidget(c);grid=QGridLayout();grid.setSpacing(10);cl.addLayout(grid);self.page_checks={}
    for i,(key,title) in enumerate(zip(PAGE_KEYS,['O / H','O / W','O / M','G / H','G / W','D / ¥'])):
        ch=QCheckBox(title);ch.setObjectName('pageChoice');ch.setChecked(key in cfg.get('enabled_pages',list(PAGE_KEYS)));self.page_checks[key]=ch;grid.addWidget(ch,i//3,i%3)
    foot=QHBoxLayout();foot.addStretch();btn('保存并应用',self.save_display,foot,'primary');l.addLayout(foot)

def tools(self,l):
    heading(l,'诊断与工具','检查结果在控制中心内显示，帮助定位连接和刷新问题。')
    grid=QGridLayout();grid.setSpacing(14);l.addLayout(grid)
    for i,(title,desc,ico,callback) in enumerate([('健康检查','进程心跳、蓝牙和额度刷新状态','health',self.health),('蓝牙诊断','检查电脑蓝牙与 Pixoo 的连接','device',self.diagnose),('图片导出','保存最近成功发送的 16 × 16 帧','export',self.export_frame),('查看日志','打开连接、刷新与错误记录','log',self.open_log)]):
        c,cl=card();r=QHBoxLayout();cl.addLayout(r);im=QLabel();im.setPixmap(icon(ico,'#3873f4',30).pixmap(30,30));im.setFixedSize(48,48);im.setStyleSheet('background:#edf3ff;border-radius:10px;');im.setAlignment(Qt.AlignmentFlag.AlignCenter);r.addWidget(im);v=QVBoxLayout();r.addLayout(v,1);v.addWidget(text(title,'heading'));v.addWidget(text(desc,'muted'));foot=QHBoxLayout();foot.addStretch();btn('运行 / 打开',callback,foot);cl.addLayout(foot);grid.addWidget(c,i//2,i%2)
    c,cl=card('最近诊断结果');l.addWidget(c,1);self.health_result=text('尚未执行健康检查。\n运行检查后将在这里显示结果。','muted');cl.addWidget(self.health_result,1);r=QHBoxLayout();r.addStretch();btn('导出诊断包',self.diagnostic_export,r);cl.addLayout(r)

def settings(self,l):
    from v1_gui import DATA,load_config
    heading(l,'应用设置','按你的习惯使用，让 Pixoo 随时陪伴。')
    c,cl=card('启动与关闭');l.addWidget(c)
    self.login_switch=Switch();self.login_switch.setEnabled(False);self.startup_note=text('自动启动状态：尚未检查','muted')
    for title,desc,sw in [('登录电脑后自动开始','登录 Windows 后，自动更新额度并显示到 Pixoo。',self.login_switch),('关闭窗口后继续显示','点击右上角 × 只收起窗口，可从托盘再次打开。',Switch()),('开始工作时连接 Pixoo','点击“开始工作”后，自动连接已设置的设备。',Switch())]:
        r=QHBoxLayout();v=QVBoxLayout();v.setSpacing(3);v.addWidget(text(title));v.addWidget(text(desc,'muted'));r.addLayout(v,1);r.addWidget(sw);cl.addLayout(r)
        if sw is not self.login_switch:sw.setChecked(True);sw.setEnabled(False);sw.setToolTip('已开启 · 默认始终生效')
    r=QHBoxLayout();r.addWidget(self.startup_note,1);btn('检查自动启动',lambda:self.startup('query'),r);cl.addLayout(r);self.login_switch.clicked.connect(lambda checked:self.startup('enable' if checked else 'disable'))
    c,cl=card('程序信息');l.addWidget(c);self.version_style=text(load_config().get('display_style','b3').upper())
    for name,w in [('产品版本',text('V1.0 · 用户体验更新')),('显示样式',self.version_style),('数据目录',text(str(DATA),'muted'))]:row(cl,name,w)
    c,cl=card();l.addWidget(c);r=QHBoxLayout();r.addWidget(text('维护操作','heading'));r.addStretch();cl.addLayout(r);btn('打开使用说明',self.help,r);btn('备份配置',self.backup_config,r);btn('打开数据目录',lambda:QDesktopServices.openUrl(QUrl.fromLocalFile(str(DATA))),r)
    from v1_brand import GITHUB_URL
    footer=QHBoxLayout();footer.addStretch();link=QLabel('<a href=\"'+GITHUB_URL+'\" style=\"color:#6e7d91;text-decoration:none;\">GitHub 项目主页 ↗</a>');link.setOpenExternalLinks(True);link.setToolTip('查看项目说明、更新与反馈');footer.addWidget(link);l.addLayout(footer)

def bind(self):
    from v1_gui import load_config
    cfg=load_config();state=self.state or {};online=bool(self.state);rt=state.get('runtime',{});last=rt.get('last_send_at');meta=state.get('providers',{});entries=state.get('readings',{})
    for pid in ('go','cx','ds'):
        pm=meta.get(pid,{});updated=pm.get('last_success_at');stale=bool(updated and time.time()-updated>max(300,cfg.get('refresh_seconds',120)*3))
        for group in (self.home_cards,self.service_cards):group[pid].bind(entries.get(pid,[]),pm,online,pid in state.get('config',{}).get('enabled',[]),state.get('price_status','UNKNOWN'),cfg.get('low',20),cfg.get('warning',50),stale)
    self.runlabel.setStyleSheet('color:'+('#a47720' if rt.get('mode')=='MOCK' else '#14b959' if online else '#8a94a2')+';font-size:14px;')
    connected=online and rt.get('bluetooth_connected');self.conn.setStyleSheet('font-size:18px;color:'+('#14b959' if connected else '#8b95a4')+';');self.devstatus.setStyleSheet('color:'+('#14b959' if connected else '#8b95a4')+';font-weight:600;')
    raw=rt.get('last_page','') or '';mapping={'go:5H':'O / H','go:7D':'O / W','go:30D':'O / M','cx:5H':'G / H','cx:7D':'G / W','ds:CNY':'D / ¥'};self.page.setText('当前发送画面：'+mapping.get(raw,raw or '--'))
    self.sent.setText('最近画面：'+(('刚刚发送' if time.time()-last<10 else f'{max(0,int(time.time()-last))} 秒前发送') if last else '暂无成功发送'))
    self.sendtime.setText('更新时间：'+(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(last)) if last else '--'))
    for target in (self.frame,self.display_frame):
        if online and rt.get('last_frame_png'):
            image=QImage.fromData(base64.b64decode(rt['last_frame_png']),'PNG');target.setPixmap(QPixmap.fromImage(image).scaled(target.width()-28,target.height()-28,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.FastTransformation))
        else:target.clear();target.setText('暂无成功发送的画面')
    self.version_style.setText(cfg.get('display_style','b3').upper())

def install(Window):
    for fn in (home,device,services,display,tools,settings):setattr(Window,fn.__name__,fn)
    refresh=Window.refresh
    def themed_refresh(self):refresh(self);bind(self)
    Window.refresh=themed_refresh
    result=Window.action_result
    def themed_result(self,data):
        if data.get('_startup'):
            message=data.get('message','');self.startup_note.setText(('自动启动：已开启' if data.get('_startup_enabled',message.startswith('已安装')) else '自动启动：已关闭') if data.get('ok') else '暂时无法检查自动启动状态，请稍后重试');self.login_switch.blockSignals(True);self.login_switch.setChecked(data.get('ok') and data.get('_startup_enabled',message.startswith('已安装')));self.login_switch.setEnabled(bool(data.get('ok')));self.login_switch.blockSignals(False)
        self.health_result.setText(data.get('message') or ('操作成功' if data.get('ok') else data.get('error','操作失败')));result(self,data)
    Window.action_result=themed_result
    def startup(self,action):
        from v1_startup import update
        self.login_switch.setEnabled(False)
        def work():
            outcome=update(action);enabled=outcome.get('ok') and outcome.get('message','').startswith('已安装')
            if outcome.get('ok'): outcome['message']='已开启：登录电脑后会自动开始显示。' if enabled else '已关闭：需要时可手动开始工作。'
            else: outcome['error']='暂时无法检查或修改自动启动设置，请稍后重试。'
            return {**outcome,'title':'自动开始设置','_startup':True,'_startup_enabled':enabled}
        self.background(work)
    Window.startup=startup
