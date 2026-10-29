from pathlib import Path
import sys
APP_NAME='Pixoo AI 监控'
GITHUB_URL='https://github.com/NoireCase/pixoo-ai-monitor'
APP_ID='NoireCase.PixooAIMonitor.Desktop'
def app_icon():
    from PySide6.QtGui import QIcon
    root=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))
    return QIcon(str(root/'assets/app.ico'))
