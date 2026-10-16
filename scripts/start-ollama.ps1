$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$manifestPath = 'D:\Softwares\AgentShield-Downloads\ollama-install.json'
if (-not (Test-Path -LiteralPath $manifestPath)) { throw 'Run scripts\install-ollama.ps1 first.' }
$ollamaManifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if (-not (Test-Path -LiteralPath $ollamaManifest.executable)) { throw 'Verified runtime executable is missing.' }
New-Item -ItemType Directory -Force -Path $ollamaManifest.models,(Join-Path $projectRoot 'work') | Out-Null
$env:OLLAMA_MODELS = $ollamaManifest.models
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_NUM_PARALLEL = '1'
$env:OLLAMA_MAX_LOADED_MODELS = '1'
$env:OLLAMA_CONTEXT_LENGTH = '2048'
if (Get-NetTCPConnection -State Listen -LocalPort 11434 -ErrorAction SilentlyContinue) {
    Write-Output 'A service is already listening on 11434. Verify it is your intended Ollama instance.'
    exit 0
}
$server = Start-Process -FilePath $ollamaManifest.executable -ArgumentList 'serve' -WorkingDirectory (Split-Path $ollamaManifest.executable -Parent) -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $projectRoot 'work\ollama-server.stdout.log') -RedirectStandardError (Join-Path $projectRoot 'work\ollama-server.stderr.log')
$server.Id | Set-Content -LiteralPath (Join-Path $projectRoot 'work\ollama-server.pid')
Write-Output "Ollama started as process $($server.Id); readiness must be checked with /api/tags. Models: $($ollamaManifest.models)"
