#requires -Version 7.4
param(
    [Parameter(Mandatory)][ValidateSet('Install', 'Start', 'Stop', 'Restart', 'Status', 'Switch', 'Rollback', 'Uninstall')][string]$Action,
    [ValidatePattern('^CRM-Churn-[a-zA-Z0-9_-]+$')][string]$TaskName = 'CRM-Churn-API',
    [string]$StateDirectory,
    [string]$ReleasePath,
    [string]$Profile,
    [string]$ProbeHost = '127.0.0.1',
    [string]$CAFile,
    [switch]$ManualOnly
)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
if (-not $StateDirectory) { $StateDirectory = Join-Path $taskRoot '.local/deployment' }
$StateDirectory = [IO.Path]::GetFullPath($StateDirectory)
# Todas las señales y el descriptor quedan en el espacio de este proyecto.
$taskLocal = [IO.Path]::GetFullPath((Join-Path $taskRoot '.local')) + [IO.Path]::DirectorySeparatorChar
if (-not $StateDirectory.StartsWith($taskLocal, [StringComparison]::OrdinalIgnoreCase)) { throw 'StateDirectory debe estar dentro de .local del proyecto.' }
New-Item -ItemType Directory -Path $StateDirectory -Force | Out-Null
$taskLock = [IO.File]::Open((Join-Path $StateDirectory 'control.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
$taskDescriptor = Join-Path $StateDirectory 'current.json'
$taskStop = Join-Path $StateDirectory 'stop.request'
$taskProfile = Join-Path $StateDirectory 'environment.json'
$taskTag = "CRM-Churn managed: $StateDirectory"

function Read-Descriptor {
    if (-not (Test-Path -LiteralPath $taskDescriptor)) { throw 'Instale primero el servicio.' }
    return Get-Content -LiteralPath $taskDescriptor -Raw | ConvertFrom-Json
}
function Write-Descriptor($value) {
    $taskTemporary = Join-Path $StateDirectory 'current.next.json'
    $value | ConvertTo-Json | Set-Content -LiteralPath $taskTemporary -Encoding utf8
    [IO.File]::Move($taskTemporary, $taskDescriptor, $true)
}
function Get-OwnedTask {
    $taskItem = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    if ($taskItem.Description -ne $taskTag) { throw 'La tarea pertenece a otro despliegue; no se modificará.' }
    return $taskItem
}
function Assert-Release([string]$path) {
    $taskResolved = (Resolve-Path -LiteralPath $path).Path
    $taskPython = Join-Path $taskResolved '.venv/Scripts/python.exe'
    $taskInstalled = Get-Content -LiteralPath (Join-Path $taskResolved 'installed.json') -Raw | ConvertFrom-Json
    if ($taskInstalled.manifest_sha256 -ne (Get-FileHash -LiteralPath (Join-Path $taskResolved 'release.json') -Algorithm SHA256).Hash) { throw 'La entrega cambió después de instalarse.' }
    Push-Location $taskResolved
    try {
        & $taskPython -m deploy.release verify $taskResolved | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'Entrega no válida.' }
        & $taskPython -m pip check | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'Dependencias incompatibles.' }
    }
    finally { Pop-Location }
    return $taskResolved
}
function New-ServiceAction([string]$path) {
    if (($path + $StateDirectory).Contains('"')) { throw 'Ruta no admitida.' }
    $taskArguments = '-m deploy.runtime --profile "' + $taskProfile + '" --state "' + $StateDirectory + '"'
    return New-ScheduledTaskAction -Execute (Join-Path $path '.venv/Scripts/python.exe') -Argument $taskArguments -WorkingDirectory $path
}
function Stop-ServiceTask {
    $null = Get-OwnedTask
    Disable-ScheduledTask -TaskName $TaskName | Out-Null
    [IO.File]::WriteAllText($taskStop, 'stop')
    $taskDeadline = [DateTime]::UtcNow.AddSeconds(45)
    while ((Get-OwnedTask).State -eq 'Running') {
        if ([DateTime]::UtcNow -ge $taskDeadline) { throw 'No se confirmó la parada en 45 s. La tarea queda deshabilitada; revisar logs antes de forzarla.' }
        Start-Sleep -Milliseconds 250
    }
}
function Start-ServiceTask {
    $taskCurrent = Read-Descriptor
    $null = Assert-Release $taskCurrent.current
    $taskExisting = Get-OwnedTask
    if ($taskExisting.State -eq 'Running') { throw 'La tarea ya está ejecutándose; use Restart.' }
    Remove-Item -LiteralPath $taskStop -ErrorAction SilentlyContinue
    Enable-ScheduledTask -TaskName $TaskName | Out-Null
    Start-ScheduledTask -TaskName $TaskName
    Push-Location $taskCurrent.current
    try {
        & (Join-Path $taskCurrent.current '.venv/Scripts/python.exe') -m deploy.acceptance --profile $taskProfile --host $taskCurrent.probe_host --ca $taskCurrent.ca
        if ($LASTEXITCODE -ne 0) { throw 'Falló la aceptación HTTPS; revisar service.log y el certificado.' }
        # El HTTP podría pertenecer a otro proceso que ocupara el puerto.
        $taskProcess = Get-Content -LiteralPath (Join-Path $StateDirectory 'process.json') -Raw | ConvertFrom-Json
        $taskActual = Get-CimInstance Win32_Process -Filter "ProcessId = $($taskProcess.pid)"
        if (-not $taskActual -or $taskActual.CommandLine -notlike '*deploy.runtime*' -or (Get-OwnedTask).State -ne 'Running') { throw 'El proceso esperado no está ejecutándose.' }
    }
    catch { Stop-ServiceTask; throw }
    finally { Pop-Location }
}
try {
    switch ($Action) {
        'Install' {
            if (-not $ReleasePath -or -not $Profile -or -not $CAFile) { throw 'Install requiere ReleasePath, Profile y CAFile.' }
            if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) { throw 'El nombre de tarea ya existe.' }
            if (Test-Path -LiteralPath $taskDescriptor) { throw 'El directorio ya contiene un despliegue; use otro StateDirectory.' }
            $taskRelease = Assert-Release $ReleasePath
            $taskCA = (Resolve-Path -LiteralPath $CAFile).Path
            Copy-Item -LiteralPath $Profile -Destination $taskProfile
            Push-Location $taskRelease
            try {
                & (Join-Path $taskRelease '.venv/Scripts/python.exe') -c 'import sys; from pathlib import Path; from deploy.runtime import load_environment; from backend.serve import build_config; build_config(load_environment(Path(sys.argv[1])))' $taskProfile
                if ($LASTEXITCODE -ne 0) { throw 'Perfil no válido.' }
            }
            finally { Pop-Location }
            $taskUser = [Security.Principal.WindowsIdentity]::GetCurrent().Name
            $taskPrincipal = New-ScheduledTaskPrincipal -UserId $taskUser -LogonType Interactive -RunLevel Limited
            $taskSettings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
            $taskDefinitionArgs = @{ Action = (New-ServiceAction $taskRelease); Principal = $taskPrincipal; Settings = $taskSettings; Description = $taskTag }
            # El disparador periódico recupera cualquier salida, incluso una terminación
            # externa que RestartOnFailure no recuperó en el ensayo de este equipo.
            # IgnoreNew conserva la instancia sana. Stop deshabilita ambos disparadores.
            $taskTriggers = @(New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 1))
            if (-not $ManualOnly) { $taskTriggers += New-ScheduledTaskTrigger -AtLogOn -User $taskUser }
            $taskDefinitionArgs.Trigger = $taskTriggers
            $taskDefinition = New-ScheduledTask @taskDefinitionArgs
            Register-ScheduledTask -TaskName $TaskName -InputObject $taskDefinition | Out-Null
            Disable-ScheduledTask -TaskName $TaskName | Out-Null
            Write-Descriptor @{ current = $taskRelease; previous = $null; probe_host = $ProbeHost; ca = $taskCA }
            Write-Output 'Instalado y detenido. Use Start para ejecutar y validar HTTPS.'
        }
        'Start' { Start-ServiceTask }
        'Stop' { Stop-ServiceTask }
        'Restart' { Stop-ServiceTask; Start-ServiceTask }
        { $_ -in 'Switch', 'Rollback' } {
            $taskOld = Read-Descriptor
            $taskTarget = if ($Action -eq 'Rollback') { $taskOld.previous } else { $ReleasePath }
            if (-not $taskTarget) { throw 'Falta una entrega de destino o una versión anterior.' }
            $taskTarget = Assert-Release $taskTarget
            if ($taskTarget -eq $taskOld.current) { throw 'La entrega ya es la actual.' }
            Stop-ServiceTask
            try {
                Set-ScheduledTask -TaskName $TaskName -Action (New-ServiceAction $taskTarget) | Out-Null
                Write-Descriptor @{ current = $taskTarget; previous = $taskOld.current; probe_host = $taskOld.probe_host; ca = $taskOld.ca }
                Start-ServiceTask
            }
            catch {
                $taskFailure = $_
                Stop-ServiceTask
                Set-ScheduledTask -TaskName $TaskName -Action (New-ServiceAction $taskOld.current) | Out-Null
                Write-Descriptor $taskOld
                Start-ServiceTask
                throw "Cambio rechazado; entrega anterior restaurada. $taskFailure"
            }
        }
        'Status' {
            $taskItem = Get-OwnedTask
            $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
            @{ task = $TaskName; state = [string]$taskItem.State; last_result = $taskInfo.LastTaskResult; deployment = (Read-Descriptor) } | ConvertTo-Json -Depth 4
        }
        'Uninstall' {
            Stop-ServiceTask
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Output 'Tarea eliminada. Se conservan entregas, perfil y logs para auditoría.'
        }
    }
}
finally { $taskLock.Dispose() }
