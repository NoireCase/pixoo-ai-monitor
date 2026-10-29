"""Detached, per-user-session monitor supervisor. Never opens Bluetooth itself."""
import ctypes
import logging
import logging.handlers
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(os.environ.get('PIXOO_V1_DATA', Path(__file__).resolve().parent))
STOP = ROOT / 'stop.request'
BACKOFF = (5, 15, 60)
STABLE_SECONDS = 600
mutex = None


def acquire():
    global mutex
    if os.name != 'nt':
        return True
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
    kernel.CreateMutexW.restype = ctypes.c_void_p
    mutex = kernel.CreateMutexW(None, False, __import__('v1_security').mutex_name('Supervisor'))
    return bool(mutex) and ctypes.get_last_error() != 183


def supervise(stop, launch, sleep=time.sleep, monotonic=time.monotonic):
    failures = 0
    while not stop.exists():
        started = monotonic()
        try:
            child = launch()
            logging.info('Monitor started pid=%s', child.pid)
            code = child.wait()
        except OSError:
            logging.exception('Could not start monitor')
            code = None
        elapsed = monotonic() - started
        logging.info('Monitor exited code=%s elapsed=%.1fs stop_requested=%s', code, elapsed, stop.exists())
        if stop.exists():
            return
        if elapsed >= STABLE_SECONDS:
            failures = 0
        if failures >= len(BACKOFF):
            logging.error('Monitor restart limit reached; manual start required')
            return
        delay = BACKOFF[failures]
        failures += 1
        logging.warning('Unexpected exit; restart %s/%s in %ss', failures, len(BACKOFF), delay)
        deadline = monotonic() + delay
        while not stop.exists() and monotonic() < deadline:
            sleep(min(1, max(0, deadline - monotonic())))


def main():
    os.chdir(ROOT)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
                        handlers=[logging.handlers.RotatingFileHandler(ROOT / 'supervisor.log', maxBytes=500000, backupCount=2, encoding='utf-8')])
    if not acquire():
        logging.info('Supervisor already running or mutex unavailable')
        return
    python = ROOT / '.venv' / 'Scripts' / 'python.exe'
    with (ROOT / 'monitor-stderr.log').open('a', encoding='utf-8') as errors:
        def launch():
            command = [sys.executable, '--worker'] if getattr(sys, 'frozen', False) else [sys.executable, str(Path(__file__).resolve().parent / 'v1_main.py'), '--worker']
            return subprocess.Popen(command, env={**os.environ, 'PYINSTALLER_RESET_ENVIRONMENT':'1'}, cwd=str(ROOT),
                                    stdin=subprocess.DEVNULL, stdout=errors, stderr=errors,
                                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        supervise(STOP, launch)


if __name__ == '__main__':
    main()
