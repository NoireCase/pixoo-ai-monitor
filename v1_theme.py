"""Shared visual tokens and native Qt components for all six pages."""
from PySide6.QtCore import Qt,QSize,QRectF
from PySide6.QtGui import QColor,QPainter,QPen,QPixmap,QIcon
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QLabel,QFrame,QVBoxLayout,QHBoxLayout,QCheckBox,QProgressBar,QWidget,QSizePolicy

QSS='''
QWidget {font-family:"Microsoft YaHei UI";font-size:14px;color:#20252e;}
QMainWindow,QWidget#base,QWidget#pageCanvas {background:#f8fafc;}
QLabel {background:transparent;border:0;}
QLabel#appTitle {font-size:23px;font-weight:700;}
QLabel#title {font-size:24px;font-weight:700;}
QLabel#heading {font-size:20px;font-weight:700;}
QLabel#muted {color:#7c8797;font-size:13px;}
QFrame#card {background:#ffffff;border:1px solid #dfe4eb;border-radius:15px;}
QFrame#previewPanel {background:#f3f6f9;border:0;border-radius:16px;}
QFrame#sidebar {border-right:1px solid #e3e8ee;background:#fbfcfe;}
QPushButton {background:#ffffff;border:1px solid #d9e0e9;border-radius:9px;padding:7px 16px;min-height:24px;font-weight:600;}
QPushButton:hover {background:#edf3ff;border-color:#c6d5f5;}
QPushButton:disabled {color:#9da5af;background:#f4f6f8;}
QPushButton#nav {text-align:left;border:0;background:transparent;padding:11px 15px;font-size:17px;font-weight:400;}
QPushButton#nav:checked {background:#eceff3;color:#171d25;font-weight:600;}
QPushButton#stop {background:#ee3f3c;color:white;border:0;font-size:18px;min-height:34px;}
QPushButton#start {background:#316cf4;color:white;border:0;font-size:18px;min-height:34px;}
QPushButton#primary {background:#252d3c;color:white;border:0;}
QCheckBox#pageChoice {background:#f6f8fb;border:1px solid #dfe5ed;border-radius:9px;padding:12px;font-size:15px;font-weight:600;}
QCheckBox#pageChoice:checked {background:#edf8f2;border:1px solid #a8d9bc;}
QCheckBox#pageChoice::indicator {width:12px;height:12px;border:1px solid #b9c3ce;border-radius:3px;background:white;}
QCheckBox#pageChoice::indicator:checked {background:#15ba61;border-color:#15ba61;}
QComboBox,QSpinBox,QLineEdit {background:#f5f7fa;border:1px solid #dce2ea;border-radius:7px;padding:7px 10px;min-height:24px;font-size:14px;}
QSpinBox QLineEdit {padding:0;border:0;min-height:0;background:transparent;}
QSlider::groove:horizontal {height:7px;background:#e4e8ee;border-radius:3px;}
QSlider::sub-page:horizontal {background:#376ef1;border-radius:3px;}
QSlider::handle:horizontal {width:17px;margin:-5px 0;background:#376ef1;border:2px solid white;border-radius:9px;}
QScrollArea {background:transparent;border:0;}
QScrollBar:vertical {width:7px;background:transparent;}
QScrollBar::handle:vertical {background:#ccd3dd;border-radius:3px;min-height:30px;}
'''
PATHS={
'home':'M3 11 L12 3 L21 11 M5 10 V21 H10 V15 H14 V21 H19 V10',
'device':'M12 2 V22 L18 16 L6 6 L12 2 L18 8 L6 20',
'service':'M14 4 A6 6 0 0 0 7 12 L2 18 L6 22 L12 16 A6 6 0 0 0 20 8 L16 12 L12 8 L16 4',
'display':'M3 3 H21 V18 H3 Z M9 22 H15 M12 18 V22',
 'tools':'M14 4 A6 6 0 0 0 7 12 L2 18 L6 22 L12 16 A6 6 0 0 0 20 8 L16 12 L12 8 L16 4',
'settings':'M9 2 H15 L16 6 L20 7 L22 12 L19 15 L19 19 L14 22 L10 20 L6 21 L2 16 L4 12 L3 8 L7 5 Z M15 12 A3 3 0 1 1 9 12 A3 3 0 1 1 15 12',
'health':'M2 12 H7 L10 4 L14 21 L17 12 H22','export':'M12 2 V15 M7 10 L12 15 L17 10 M3 16 V22 H21 V16',
'log':'M5 2 H16 L21 7 V22 H5 Z M9 10 H17 M9 14 H17 M9 18 H15',
'moon':'M19 16 A9 9 0 0 1 9 3 A9 9 0 1 0 19 16'}
def icon(name,color='#526071',size=24):
    path=PATHS.get(name,PATHS['display']); svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path d="{path}" fill="none" stroke="{color}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    pix=QPixmap(size*2,size*2);pix.fill(Qt.GlobalColor.transparent);p=QPainter(pix);QSvgRenderer(svg.encode()).render(p);p.end();pix.setDevicePixelRatio(2);return QIcon(pix)
def text(value='',role=''):
    x=QLabel(value);x.setWordWrap(True)
    if role:x.setObjectName(role)
    return x

def card(title=None):
    w=QFrame();w.setObjectName('card');l=QVBoxLayout(w);l.setContentsMargins(20,17,20,17);l.setSpacing(12)
    if title:l.addWidget(text(title,'heading'))
    return w,l

class Switch(QCheckBox):
    def __init__(self,parent=None):super().__init__(parent);self.setFixedSize(46,27);self.setCursor(Qt.CursorShape.PointingHandCursor)
    def hitButton(self,pos):return self.rect().contains(pos)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor('#2cc374' if self.isChecked() else '#c7cfd9') if self.isEnabled() or self.isChecked() else QColor('#d7dde5'));p.drawRoundedRect(QRectF(1,2,44,23),12,12)
        p.setBrush(QColor('white'));p.drawEllipse(QRectF(24 if self.isChecked() else 4,5,17,17));p.end()

class QuotaCard(QFrame):
    def __init__(self,title,windows,balance=False,compact=False):
        super().__init__();self.setObjectName('card');self.balance=balance;self.cells={};self.compact=compact
        l=QVBoxLayout(self);l.setContentsMargins(20,16,20,15);l.setSpacing(9)
        header=QHBoxLayout();name=text(title,'heading');name.setStyleSheet('font-size:22px;font-weight:700;');header.addWidget(name);header.addStretch();self.status=text('等待后台');header.addWidget(self.status);self.extra=QHBoxLayout();header.addLayout(self.extra);l.addLayout(header)
        row=QHBoxLayout();row.setSpacing(22);l.addLayout(row,1)
        if balance:
            self.amount=text('--');self.amount.setStyleSheet('font-size:32px;font-weight:700;');row.addWidget(self.amount);row.addStretch();self.price=text('峰谷未知');row.addWidget(self.price)
        else:
            for i,key in enumerate(windows):
                if i:
                    line=QFrame();line.setFixedWidth(1);line.setStyleSheet('background:#e2e7ed;');row.addWidget(line)
                col=QVBoxLayout();col.setSpacing(4);col.addWidget(text(key,'muted'));value=text('--');value.setStyleSheet('font-size:26px;font-weight:700;');col.addWidget(value)
                bar=QProgressBar();bar.setRange(0,1000);bar.setTextVisible(False);bar.setFixedHeight(7);col.addWidget(bar);row.addLayout(col,1);self.cells[key]=(value,bar)
        self.updated=text('最近成功刷新：--','muted');self.updated.setStyleSheet('font-size:11px;color:#8993a1;');l.addWidget(self.updated)
        if compact:
            l.setContentsMargins(18,12,18,10);l.setSpacing(6);self.setFixedHeight(166);self.updated.setMaximumHeight(16);self.updated.hide()
            for value,bar in self.cells.values(): value.setStyleSheet('font-size:23px;font-weight:700;')
    def bind(self,entries,meta,online,enabled,price,low=20,warning=50,stale=False):
        status=meta.get('status','PENDING') if online else 'DISCONNECTED'
        if stale and status=='OK':status='STALE'
        if online and not enabled:status='DISABLED'
        words={'OK':'● 正常','STALE':'● 已过期','ERROR':'● 刷新失败','PENDING':'● 等待刷新','NOT_CONFIGURED':'● 未配置','UNSUPPORTED':'● 不支持','DISCONNECTED':'● 后台未连接','DISABLED':'● 已停用'}
        color='#12b857' if status=='OK' else '#d69a1c' if status in ('STALE','PENDING') else '#dc4b4b' if status=='ERROR' else '#8a94a2'
        self.status.setText(words.get(status,status));self.status.setStyleSheet('color:'+color+';font-size:13px;font-weight:600;')
        import time
        last=meta.get('last_success_at') if online else None;self.updated.setText('最近成功刷新：'+(time.strftime('%H:%M:%S',time.localtime(last)) if last else '--'))
        self.status.setToolTip(self.updated.text())
        by={x.get('window'):x for x in entries} if online else {}
        for key,(label,bar) in self.cells.items():
            value=by.get(key,{}).get('percent');label.setText(f'{value:g}%' if isinstance(value,(int,float)) else '--')
            bar.setValue(round(max(0,min(100,value))*10) if isinstance(value,(int,float)) else 0)
            col='#12be5b' if isinstance(value,(int,float)) and value>warning else '#e8af24' if isinstance(value,(int,float)) and value>=low else '#e84d47'
            bar.setStyleSheet('QProgressBar{background:#e4e7ec;border:0;border-radius:3px;}QProgressBar::chunk{background:'+col+';border-radius:3px;}')
        if self.balance:
            entry=next((e for e in entries if e.get('unit')=='CNY'),None) if online else None
            from decimal import Decimal,InvalidOperation
            try:self.amount.setText('¥'+format(Decimal(entry['value']),'.2f') if entry and entry.get('value') is not None else '--')
            except InvalidOperation:self.amount.setText('--')
            self.price.setText({'PEAK':'峰时时段','OFF_PEAK':'☾ 空闲时段 · 半价'}.get(price,'峰谷状态未知'));self.price.setStyleSheet('color:#3469ff;font-size:15px;')
