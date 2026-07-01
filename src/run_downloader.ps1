$ProjectDir = Split-Path -Parent $PSScriptRoot
$LogFile = Join-Path $ProjectDir "download\download.log"
$Script = Join-Path $PSScriptRoot "download_tg_channel.py"

Set-Location -LiteralPath $ProjectDir

cmd /c "python `"$Script`" 2>&1" | Out-File -FilePath $LogFile -Append -Encoding utf8
