param([string]$OutputDirectory='dist-user-update')
$ErrorActionPreference='Stop'
$python=if ($env:PIXOO_BUILD_PYTHON) { $env:PIXOO_BUILD_PYTHON } else { 'python' }
$dist=Join-Path $PSScriptRoot $OutputDirectory
$target=Join-Path $dist 'Pixoo-AI-Monitor'
& $python -m PyInstaller --noconfirm --clean --onedir --windowed --name 'Pixoo-AI-Monitor' --icon "$PSScriptRoot\assets\app.ico" --version-file "$PSScriptRoot\version_info.txt" --add-data "$PSScriptRoot\assets;assets" --distpath $dist --workpath (Join-Path $PSScriptRoot 'build\stage2') --specpath (Join-Path $PSScriptRoot 'build') --add-data "$PSScriptRoot\config.example.json;." --add-data "$PSScriptRoot\使用说明.txt;." --add-data "$PSScriptRoot\LICENSE-PixooCtrl;." --add-data "$PSScriptRoot\data;data" --collect-all keyring --hidden-import keyring.backends.Windows --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.QtWebEngineWidgets --exclude-module PySide6.QtWebEngineQuick (Join-Path $PSScriptRoot 'v1_main.py')
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed: $LASTEXITCODE" }
Copy-Item -LiteralPath (Join-Path $target 'Pixoo-AI-Monitor.exe') -Destination (Join-Path $target 'Pixoo AI 监控.exe') -Force
Remove-Item -LiteralPath (Join-Path $target 'Pixoo-AI-Monitor.exe')
foreach($name in @('icuuc.dll','icudt78.dll')) {
 $file=Join-Path $target ('_internal\'+$name)
 for($attempt=0; $attempt -lt 10 -and (Test-Path -LiteralPath $file); $attempt++){
  try { Remove-Item -LiteralPath $file -ErrorAction Stop } catch { if($attempt -eq 9){throw}; Start-Sleep -Milliseconds 200 }
 }
}
$licenses=Join-Path $target 'licenses'
New-Item -Path $licenses -ItemType Directory -Force | Out-Null
$site=(& $python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])').Trim()
Get-ChildItem -LiteralPath $site -Directory -Filter '*.dist-info' | ForEach-Object {
 $destination=Join-Path $licenses $_.Name
 New-Item -Path $destination -ItemType Directory -Force | Out-Null
 foreach($item in @('licenses','LICENSE','LICENSE.txt','COPYING.txt','METADATA')) {
  $source=Join-Path $_.FullName $item
  if(Test-Path -LiteralPath $source){Copy-Item -LiteralPath $source -Destination $destination -Recurse -Force}
 }
}
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'THIRD_PARTY_V1.txt') -Destination $target -Force
