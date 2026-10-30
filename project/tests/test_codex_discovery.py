from providers import sources


def test_codex_on_path_takes_priority(monkeypatch):
    monkeypatch.setattr(sources.shutil, 'which', lambda name: 'existing-codex')
    assert sources.find_codex() == 'existing-codex'


def test_desktop_codex_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr(sources.shutil, 'which', lambda name: None)
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path))
    exe = tmp_path / 'OpenAI' / 'Codex' / 'bin' / 'version' / 'codex.exe'
    exe.parent.mkdir(parents=True)
    exe.touch()
    assert sources.find_codex() == str(exe)
    exe.unlink()
    assert sources.find_codex() is None
