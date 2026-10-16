param([string]$Model = 'qwen3:0.6b')
$ErrorActionPreference = 'Stop'
$ollamaManifest = Get-Content -LiteralPath 'D:\Softwares\AgentShield-Downloads\ollama-install.json' -Raw | ConvertFrom-Json
$env:OLLAMA_MODELS = $ollamaManifest.models
$env:OLLAMA_HOST = '127.0.0.1:11434'
& $ollamaManifest.executable pull $Model
if ($LASTEXITCODE -ne 0) { throw 'Model download failed.' }
& $ollamaManifest.executable list
