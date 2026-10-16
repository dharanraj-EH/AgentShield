$ErrorActionPreference = 'Stop'
$projectPath = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectPath
if (-not $env:AGENTSHIELD_MODEL) { $env:AGENTSHIELD_MODEL = 'qwen3:0.6b' }
$pythonPath = Join-Path $projectPath '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Run scripts\setup.ps1 first.' }
foreach ($port in 8765,8766,5173) {
    if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) { throw "Port $port is already in use. Stop that service or use the existing AgentShield session." }
}
$services = @()
$ollamaWasStarted = $false
try {
    if ((Test-Path -LiteralPath 'D:\Softwares\AgentShield-Downloads\ollama-install.json') -and -not (Get-NetTCPConnection -State Listen -LocalPort 11434 -ErrorAction SilentlyContinue)) {
        & (Join-Path $PSScriptRoot 'start-ollama.ps1')
        $ollamaWasStarted = $true
    }
    $services += Start-Process -FilePath $pythonPath -ArgumentList '-m uvicorn backend.receiver:app --host 127.0.0.1 --port 8766' -WorkingDirectory $projectPath -WindowStyle Hidden -PassThru
    $services += Start-Process -FilePath $pythonPath -ArgumentList '-m uvicorn backend.app:app --host 127.0.0.1 --port 8765' -WorkingDirectory $projectPath -WindowStyle Hidden -PassThru
    # Run Vite directly to avoid cmd / npm quoting problems in paths containing spaces.
    $services += Start-Process -FilePath 'node.exe' -ArgumentList 'node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173' -WorkingDirectory (Join-Path $projectPath 'frontend') -WindowStyle Hidden -PassThru
    Write-Host 'AgentShield: http://127.0.0.1:5173'
    Write-Host 'Keep this terminal open. Press Ctrl+C to stop all three services.'
    while ($true) {
        Start-Sleep -Seconds 2
        foreach ($service in $services) { if ($service.HasExited) { throw "Service $($service.Id) exited. Use the manual startup commands in README.md for diagnostics." } }
    }
} finally {
    foreach ($service in $services) { if (-not $service.HasExited) { Stop-Process -Id $service.Id -ErrorAction SilentlyContinue } }
    if ($ollamaWasStarted) {
        $ownedPidPath = Join-Path $projectPath 'work\ollama-server.pid'
        if (Test-Path -LiteralPath $ownedPidPath) {
            $ownedProcess = Get-Process -Id ([int](Get-Content -LiteralPath $ownedPidPath)) -ErrorAction SilentlyContinue
            if ($ownedProcess -and $ownedProcess.Path.StartsWith('D:\Softwares\Ollama\',[StringComparison]::OrdinalIgnoreCase)) { Stop-Process -Id $ownedProcess.Id }
        }
    }
}
