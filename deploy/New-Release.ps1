#requires -Version 7.4
param(
    [Parameter(Mandatory)][ValidatePattern('^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$')][string]$Version,
    [string]$Python = 'C:\Python314\python.exe',
    [string]$Wheelhouse
)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskDestination = Join-Path $taskRoot '.local/releases'
Push-Location $taskRoot
try {
    & $Python -m deploy.release build --destination $taskDestination --version $Version
    if ($LASTEXITCODE -ne 0) { throw 'Falló la construcción de la entrega.' }
    $taskRelease = Join-Path $taskDestination $Version
    & $Python -m venv (Join-Path $taskRelease '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno aislado.' }
    $taskRuntime = Join-Path $taskRelease '.venv/Scripts/python.exe'
    $taskPipArgs = @('-m', 'pip', 'install', '--disable-pip-version-check', '-r', (Join-Path $taskRelease 'requirements-lock.txt'))
    if ($Wheelhouse) { $taskPipArgs += @('--no-index', '--find-links', (Resolve-Path -LiteralPath $Wheelhouse).Path) }
    & $taskRuntime @taskPipArgs
    if ($LASTEXITCODE -ne 0) { throw 'Instalación incompleta. La entrega no se habilitó.' }
    Push-Location $taskRelease
    try {
        & $taskRuntime -m pip check
        if ($LASTEXITCODE -ne 0) { throw 'Dependencias incompatibles.' }
        & $taskRuntime -m deploy.release verify $taskRelease
        if ($LASTEXITCODE -ne 0) { throw 'Entrega alterada.' }
        & $taskRuntime -c 'import json; from ML.inference import ChurnPredictor; from pathlib import Path; p=ChurnPredictor.load(); print(p.version, p.predict_probability(json.loads(Path("deploy/acceptance_request.json").read_text())["features"]))'
        if ($LASTEXITCODE -ne 0) { throw 'El artefacto no funciona en el entorno limpio.' }
        $taskInstalled = @{ installed_at_utc = [DateTime]::UtcNow.ToString('o'); manifest_sha256 = (Get-FileHash -LiteralPath 'release.json' -Algorithm SHA256).Hash }
        $taskInstalled | ConvertTo-Json | Set-Content -LiteralPath 'installed.json' -Encoding utf8
    }
    finally { Pop-Location }
    Write-Output "Entrega lista: $taskRelease"
}
finally { Pop-Location }
