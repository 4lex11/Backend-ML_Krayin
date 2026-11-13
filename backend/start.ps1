param([ValidateRange(1, 65535)][int]$Port = 8443)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskPython = Join-Path $taskRoot '.venv-clean/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
    throw 'Falta .venv-clean. Siga README.md para instalar requirements-lock.txt.'
}
$taskPreviousPort = $env:CHURN_PORT
$env:CHURN_PORT = [string]$Port
Push-Location $taskRoot
try {
    & $taskPython -m backend.serve
    if ($LASTEXITCODE -ne 0) { throw "La API finalizó con código $LASTEXITCODE" }
}
finally {
    $env:CHURN_PORT = $taskPreviousPort
    Pop-Location
}
