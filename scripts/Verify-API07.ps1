#requires -Version 7.4
param(
    [string]$Version = 'api-2.0.0-api07',
    [string]$NextVersion = 'api-2.0.1-api07-test'
)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskName = 'CRM-Churn-API07Verification'
$taskState = Join-Path $taskRoot '.local/api07-verification/state'
$taskManager = Join-Path $taskRoot 'deploy/Service.ps1'
$taskEvidence = Join-Path $taskRoot 'docs/evidencias_api'
$taskArgs = @{ TaskName = $taskName; StateDirectory = $taskState }
$taskResult = [ordered]@{ checked_at_utc = [DateTime]::UtcNow.ToString('o'); platform = 'Windows / Python 3.14.6'; checks = [ordered]@{} }
function Read-ServiceProcess {
    return Get-Content -LiteralPath (Join-Path $taskState 'process.json') -Raw | ConvertFrom-Json
}
function Assert-True([bool]$value, [string]$message) {
    if (-not $value) { throw $message }
}
try {
    $taskDefinition = Get-ScheduledTask -TaskName $taskName
    Assert-True ($taskDefinition.Description -eq "CRM-Churn managed: $taskState") 'La tarea no pertenece a esta verificación.'
    Assert-True ([bool]($taskDefinition.Triggers | Where-Object { $_.Repetition.Interval -eq 'PT1M' })) 'Falta supervisión periódica.'
    Assert-True ($taskDefinition.Settings.MultipleInstances -eq 'IgnoreNew') 'Se permiten instancias simultáneas.'
    $taskXml = Export-ScheduledTask -TaskName $taskName
    $taskXml.Replace('encoding="UTF-16"', 'encoding="utf-8"') | Set-Content -LiteralPath (Join-Path $taskEvidence 'API07_tarea_windows.xml') -Encoding utf8
    $taskInitial = Read-ServiceProcess
    Assert-True ($taskInitial.release_version -eq $Version) 'Versión inicial inesperada.'
    & $taskManager -Action Restart @taskArgs
    $taskRestarted = Read-ServiceProcess
    Assert-True ($taskInitial.pid -ne $taskRestarted.pid) 'El reinicio no creó otro proceso.'
    $taskResult.checks.controlled_restart = $true
    $taskCim = Get-CimInstance Win32_Process -Filter "ProcessId = $($taskRestarted.pid)"
    Assert-True ($taskCim.CommandLine -like '*deploy.runtime*' -and $taskCim.CommandLine.Contains($taskState)) 'No se interrumpirá un proceso ajeno.'
    $taskWatch = [Diagnostics.Stopwatch]::StartNew()
    Stop-Process -Id $taskRestarted.pid -Force
    Write-Output 'Caída simulada del proceso propio; esperando recuperación del Programador de tareas.'
    $taskDeadline = [DateTime]::UtcNow.AddSeconds(100)
    do {
        Start-Sleep -Milliseconds 500
        if ([DateTime]::UtcNow -gt $taskDeadline) { throw 'Windows no reinició la tarea dentro del límite.' }
        $taskAfterCrash = Read-ServiceProcess
    } while ($taskAfterCrash.pid -eq $taskRestarted.pid)
    $taskResult.checks.automatic_restart_after_crash = $true
    $taskResult.checks.recovery_seconds = [Math]::Round($taskWatch.Elapsed.TotalSeconds, 2)
    $taskRelease = Join-Path $taskRoot ".local/releases/$Version"
    Push-Location $taskRelease
    try {
        $taskAcceptance = & (Join-Path $taskRelease '.venv/Scripts/python.exe') -m deploy.acceptance --profile (Join-Path $taskState 'environment.json') --ca (Join-Path $taskRoot '.local/security/cert.pem')
        if ($LASTEXITCODE -ne 0) { throw 'Falló HTTPS después de la recuperación.' }
        $taskResult.checks.acceptance = $taskAcceptance | ConvertFrom-Json
    }
    finally { Pop-Location }
    & $taskManager -Action Switch -ReleasePath (Join-Path $taskRoot ".local/releases/$NextVersion") @taskArgs
    Assert-True ((Read-ServiceProcess).release_version -eq $NextVersion) 'La actualización no cambió de entrega.'
    $taskResult.checks.update_to = $NextVersion
    & $taskManager -Action Rollback @taskArgs
    Assert-True ((Read-ServiceProcess).release_version -eq $Version) 'Rollback no restauró la entrega inicial.'
    $taskResult.checks.rollback_to = $Version
    & $taskManager -Action Stop @taskArgs
    Assert-True (-not (Test-Path -LiteralPath (Join-Path $taskState 'process.json'))) 'La parada no liberó el archivo de proceso.'
    $taskInfo = Get-ScheduledTaskInfo -TaskName $taskName
    Assert-True ($taskInfo.LastTaskResult -eq 0) 'El proceso no terminó normalmente.'
    $taskResult.checks.graceful_stop_exit_code = 0
    $taskResult.checks.scheduler_recovery_interval = 'PT1M'
    $taskResult.scope = 'Entrega y servicio local Windows. Dos versiones de aplicación con el mismo modelo experimental. Sin Krayin ni reinicio del equipo.'
}
finally {
    if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
        & $taskManager -Action Uninstall @taskArgs
    }
}
$taskResult.checks.temporary_task_removed = -not [bool](Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue)
$taskResult | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $taskEvidence '08_despliegue_reversion.json') -Encoding utf8
$taskResult | ConvertTo-Json -Depth 8
