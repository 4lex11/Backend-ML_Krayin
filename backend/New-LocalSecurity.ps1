#requires -Version 7.4
param([string]$Directory = '.local/security')
$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$taskDirectory = [IO.Path]::GetFullPath((Join-Path $taskRoot $Directory))
if (-not $taskDirectory.StartsWith($taskRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'El directorio de secretos debe estar dentro del proyecto.'
}
if (Test-Path -LiteralPath $taskDirectory) {
    throw 'El directorio ya existe. No se sobrescriben certificados ni claves.'
}
New-Item -ItemType Directory -Path $taskDirectory | Out-Null
# Quitar herencia antes de escribir cualquier secreto, sin modificar el almacén de Windows.
$taskAcl = Get-Acl -LiteralPath $taskDirectory
$taskAcl.SetAccessRuleProtection($true, $false)
$taskSid = [Security.Principal.WindowsIdentity]::GetCurrent().User
$taskSystem = [Security.Principal.SecurityIdentifier]::new('S-1-5-18')
foreach ($taskPrincipal in @($taskSid, $taskSystem)) {
    $taskRule = [Security.AccessControl.FileSystemAccessRule]::new(
        $taskPrincipal, 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow'
    )
    $taskAcl.AddAccessRule($taskRule)
}
Set-Acl -LiteralPath $taskDirectory -AclObject $taskAcl
$taskRsa = [Security.Cryptography.RSA]::Create(3072)
try {
    $taskRequest = [Security.Cryptography.X509Certificates.CertificateRequest]::new(
        'CN=localhost', $taskRsa, [Security.Cryptography.HashAlgorithmName]::SHA256,
        [Security.Cryptography.RSASignaturePadding]::Pkcs1
    )
    $taskSan = [Security.Cryptography.X509Certificates.SubjectAlternativeNameBuilder]::new()
    $taskSan.AddDnsName('localhost')
    $taskSan.AddIpAddress([Net.IPAddress]::Parse('127.0.0.1'))
    $taskSan.AddIpAddress([Net.IPAddress]::Parse('::1'))
    $taskRequest.CertificateExtensions.Add($taskSan.Build())
    $taskRequest.CertificateExtensions.Add([Security.Cryptography.X509Certificates.X509BasicConstraintsExtension]::new($false, $false, 0, $true))
    $taskUsages = [Security.Cryptography.OidCollection]::new()
    $taskUsages.Add([Security.Cryptography.Oid]::new('1.3.6.1.5.5.7.3.1')) | Out-Null
    $taskRequest.CertificateExtensions.Add([Security.Cryptography.X509Certificates.X509EnhancedKeyUsageExtension]::new($taskUsages, $true))
    $taskCert = $taskRequest.CreateSelfSigned([DateTimeOffset]::UtcNow.AddMinutes(-5), [DateTimeOffset]::UtcNow.AddDays(30))
    try {
        [IO.File]::WriteAllText((Join-Path $taskDirectory 'cert.pem'), $taskCert.ExportCertificatePem())
        [IO.File]::WriteAllText((Join-Path $taskDirectory 'key.pem'), $taskRsa.ExportPkcs8PrivateKeyPem())
        $taskToken = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(48))
        [IO.File]::WriteAllText((Join-Path $taskDirectory 'api-key.txt'), $taskToken)
    }
    finally { $taskCert.Dispose() }
}
finally { $taskRsa.Dispose() }
Write-Output "Certificado de localhost (30 días) y secretos creados en $taskDirectory"
Write-Output 'No se instaló confianza en Windows. Configure el cliente con cert.pem; no omita la verificación TLS.'
