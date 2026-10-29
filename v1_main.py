"""Single entry point for GUI, detached supervisor and worker."""
import os, sys, shutil
from pathlib import Path

def prepare():
    data = Path(os.environ.get('PIXOO_V1_DATA') or (Path(os.environ.get('LOCALAPPDATA', Path.home()))/'Pixoo AI Monitor V1'))
    data.mkdir(parents=True, exist_ok=True)
    os.environ['PIXOO_V1_DATA']=str(data)
    config=data/'config.json'
    if not config.exists():
        # Explicitly retain existing production configuration, without altering it.
        old=Path(r'D:\software\pixoo\pixoo-ai-monitor\config.json')
        source=old if old.is_file() else Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))/'config.example.json'
        if source.is_file(): shutil.copyfile(source, config)
    from v1_security import token
    try: token(create=True)
    except Exception: os.environ['PIXOO_V1_AUTH_ERROR']='凭据管理器不可用：请在交互式 Windows 登录会话中运行'
    return data

def main():
    prepare()
    if '--supervisor' in sys.argv:
        sys.argv=[sys.argv[0]]
        import supervisor; supervisor.main()
    elif '--worker' in sys.argv:
        sys.argv=[sys.argv[0]]
        from PySide6.QtCore import QCoreApplication
        app=QCoreApplication(sys.argv)
        import app as worker; worker.main()
    else:
        from v1_gui import main as gui
        gui()
if __name__ == '__main__': main()
