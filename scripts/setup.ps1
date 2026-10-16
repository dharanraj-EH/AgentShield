$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
& node.exe -e "const [major,minor]=process.versions.node.split('.').map(Number);if(!((major===22&&minor>=12)||major===24||major>=26))process.exit(1)"
if ($LASTEXITCODE -ne 0) { throw 'Node 22.12+, Node 24, or Node 26+ is required by the verified frontend tooling. This laptop has Node 22.14.0.' }
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    py -3 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.11 or later and retry.' }
}
& .\.venv\Scripts\python.exe -c "import sys; assert sys.version_info >= (3,11), 'Python 3.11+ required'"
if ($LASTEXITCODE -ne 0) { throw 'Python version check failed.' }
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
Push-Location frontend
try { npm.cmd ci; if ($LASTEXITCODE -ne 0) { throw 'npm install failed.' } } finally { Pop-Location }
Write-Host 'Setup complete. Run scripts\start.ps1.'
