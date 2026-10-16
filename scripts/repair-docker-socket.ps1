$ErrorActionPreference = 'Stop'
& docker.exe info --format '{{.ServerVersion}}' 2>$null
if ($LASTEXITCODE -eq 0) { Write-Output 'Docker is healthy; no repair performed.'; exit 0 }
if (Get-Process -Name 'Docker Desktop','com.docker.backend','com.docker.proxy' -ErrorAction SilentlyContinue) { throw 'Quit Docker Desktop before repairing its runtime directory. Images and settings must not be reset.' }
$dockerRoot = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Docker'))
$runtimePath = [IO.Path]::GetFullPath((Join-Path $dockerRoot 'run'))
$backupName = 'run.backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
$backupPath = [IO.Path]::GetFullPath((Join-Path $dockerRoot $backupName))
if (-not $runtimePath.StartsWith($dockerRoot+'\',[StringComparison]::OrdinalIgnoreCase) -or -not $backupPath.StartsWith($dockerRoot+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Paths escaped the intended Docker directory.' }
foreach ($checkedPath in @($dockerRoot,$runtimePath)) { if ((Get-Item -LiteralPath $checkedPath -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'A repair directory is a link; refusing to rename it.' } }
Rename-Item -LiteralPath $runtimePath -NewName $backupName
New-Item -ItemType Directory -Path $runtimePath | Out-Null
Write-Output "Runtime preserved at $backupPath. Start Docker Desktop and verify docker version. No images, containers or settings were reset."
