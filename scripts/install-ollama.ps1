$ErrorActionPreference = 'Stop'
$softwareRoot = 'D:\Softwares'
$downloadRoot = Join-Path $softwareRoot 'AgentShield-Downloads'
New-Item -ItemType Directory -Force -Path $downloadRoot | Out-Null
$release = Invoke-RestMethod -Uri 'https://api.github.com/repos/ollama/ollama/releases/latest'
$asset = $release.assets | Where-Object name -eq 'ollama-windows-amd64.zip'
if (-not $asset -or $asset.digest -notmatch '^sha256:[a-f0-9]{64}$') { throw 'Official release lacks a usable SHA256 digest.' }
$archivePath = Join-Path $downloadRoot ($release.tag_name + '-ollama-windows-amd64.zip')
$runtimeRoot = Join-Path $softwareRoot ('Ollama\runtime-' + $release.tag_name)
if (-not (Test-Path -LiteralPath $archivePath) -or (Get-Item -LiteralPath $archivePath).Length -ne $asset.size) {
    Write-Output "Downloading official Ollama $($release.tag_name) into $downloadRoot"
    & curl.exe --location --fail --retry 3 --continue-at - --speed-limit 1024 --speed-time 60 --max-time 1800 --silent --show-error --output $archivePath $asset.browser_download_url
    if ($LASTEXITCODE -ne 0) { throw 'Ollama download failed.' }
}
$expectedHash = $asset.digest.Substring(7)
if ((Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash) { throw 'SHA256 verification failed. Archive was not executed.' }
if (-not (Test-Path -LiteralPath (Join-Path $runtimeRoot 'ollama.exe'))) {
    New-Item -ItemType Directory -Force -Path $runtimeRoot | Out-Null
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [System.IO.Compression.ZipFile]::OpenRead($archivePath)
    try {
        $checkedRoot = [System.IO.Path]::GetFullPath($runtimeRoot).TrimEnd('\') + '\'
        foreach ($entry in $archive.Entries) {
            $checkedEntry = [System.IO.Path]::GetFullPath((Join-Path $runtimeRoot $entry.FullName))
            if (-not $checkedEntry.StartsWith($checkedRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Archive entry escapes installation directory.' }
        }
    } finally { $archive.Dispose() }
    Expand-Archive -LiteralPath $archivePath -DestinationPath $runtimeRoot
}
$manifest = @{version=$release.tag_name; executable=(Join-Path $runtimeRoot 'ollama.exe'); models=(Join-Path $softwareRoot 'Ollama\Models'); archive=$archivePath; sha256=$expectedHash; source=$asset.browser_download_url}
$manifest | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $downloadRoot 'ollama-install.json') -Encoding utf8
& $manifest.executable --version
if ($LASTEXITCODE -ne 0) { throw 'Ollama executable verification failed.' }
Write-Output "Verified portable runtime installed at $runtimeRoot"
