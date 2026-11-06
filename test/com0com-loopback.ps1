# Windows loopback for the hardware tests: a com0com virtual null-modem pair, with an echo on one
# end. Tests open $TestPort; everything written to it comes back, like a TX-RX jumper.
#
# Needs an elevated shell, and a machine that loads com0com's 2011 signed driver: test-signing on
# or Secure Boot off, as on GitHub's Windows runners. Most desktops with Secure Boot won't load it.
#
#   pwsh test/com0com-loopback.ps1            # installs COM10 <-> COM11 if needed, echoes on COM11
#   $env:TEST_PORT = 'COM10'; $env:TEST_PORT_TYPE = 'com0com'; npm test
param(
  [string]$TestPort = 'COM10',
  [string]$EchoPort = 'COM11',
  [string]$WorkDir = $(if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { [IO.Path]::GetTempPath() }),
  # Only install the pair; don't start the echo
  [switch]$NoEcho
)
$ErrorActionPreference = 'Stop'

if (-not ([System.IO.Ports.SerialPort]::GetPortNames() -contains $TestPort)) {
  # com0com 2.2.2.0, the signed x64 build from the project's own SourceForge page
  $zip = Join-Path $WorkDir 'com0com.zip'
  $dir = Join-Path $WorkDir 'com0com'
  Invoke-WebRequest 'https://downloads.sourceforge.net/project/com0com/com0com/2.2.2.0/com0com-2.2.2.0-x64-fre-signed.zip' -OutFile $zip -UserAgent 'curl/8'
  $hash = (Get-FileHash $zip -Algorithm SHA256).Hash
  if ($hash -ne '3BC7313E8577774CE78CFF4D1C816FAF96CFA48C485BBCC5527D4569F7D5E373') { throw "com0com.zip has an unexpected SHA-256: $hash" }
  Expand-Archive $zip -DestinationPath $WorkDir -Force
  # The installer is an NSIS archive; setupc.exe installs the driver without any UI
  7z x -y "-o$dir" (Join-Path $WorkDir 'com0com-2.2.2.0-x64-fre-signed\setup.exe') | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "7z failed ($LASTEXITCODE)" }

  # Trust the driver's signer up front, or Windows asks in a dialog
  $cert = (Get-AuthenticodeSignature (Join-Path $dir 'com0com.cat')).SignerCertificate
  foreach ($storeName in 'TrustedPublisher', 'Root') {
    $store = [System.Security.Cryptography.X509Certificates.X509Store]::new($storeName, 'LocalMachine')
    $store.Open('ReadWrite'); $store.Add($cert); $store.Close()
  }

  Push-Location $dir
  try {
    & .\setupc.exe --silent install "PortName=$TestPort" "PortName=$EchoPort"
    if ($LASTEXITCODE -ne 0) { throw "setupc failed ($LASTEXITCODE)" }
  } finally { Pop-Location }
  for ($i = 0; $i -lt 50 -and -not ([System.IO.Ports.SerialPort]::GetPortNames() -contains $TestPort); $i++) { Start-Sleep -Milliseconds 100 }
}

if ($NoEcho) { return }

# The echo runs in its own hidden process, until it's stopped or the machine goes away
$echo = Join-Path $PSScriptRoot 'serial-echo.ps1'
$log = Join-Path $WorkDir 'serial-echo.log'
Start-Process pwsh -ArgumentList '-NoProfile', '-File', $echo, $EchoPort -WindowStyle Hidden -RedirectStandardOutput $log -RedirectStandardError "$log.err"
for ($i = 0; $i -lt 50 -and -not (Select-String -Path $log -Pattern 'echoing' -Quiet -ErrorAction SilentlyContinue); $i++) { Start-Sleep -Milliseconds 100 }
Get-Content $log, "$log.err" -ErrorAction SilentlyContinue
