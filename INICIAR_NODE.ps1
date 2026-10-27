# Alternativa Node nativo, separada do Docker. Nao instala dependencias.
# Operacao supervisionada. QR, allowlist e dados sao privados; nao projete este terminal.
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
. (Join-Path $PSScriptRoot 'PYTHON_WINDOWS.ps1')
# Node existente, sem instalar pacote ou alterar sistema.
$node = Get-Command node -CommandType Application -ErrorAction Stop | Select-Object -First 1
& $node.Source -e "if (Number(process.versions.node.split('.')[0]) < 22) process.exit(1)"
if ($LASTEXITCODE -ne 0) { throw 'Node 22+ necessario; nada foi instalado.' }
foreach ($dependencia in @('baileys','qrcode')) {
  $manifesto = Join-Path $PSScriptRoot ('gateway\node_modules\'+$dependencia+'\package.json')
  if (-not (Test-Path -LiteralPath $manifesto)) { throw ('Dependencia '+$dependencia+' ausente. Instalar npm requer autorizacao separada; este launcher nao instala.') }
  $instalada = (Get-Content -Raw -LiteralPath $manifesto | ConvertFrom-Json).version
  $esperada = if ($dependencia -eq 'baileys') { '7.0.0-rc14' } else { '1.5.4' }
  if ($instalada -ne $esperada) { throw ('Versao inesperada de '+$dependencia+'. Revise antes de parear.') }
}
if (Get-NetTCPConnection -LocalPort 3210 -State Listen -ErrorAction SilentlyContinue) { throw 'Porta 3210 ocupada. Nao paro nem reutilizo outro processo.' }
Invoke-KitPython .\agente.py verificar
if ($LASTEXITCODE -ne 0) { throw 'Fonte ou CLI nao verificados. Nao parear.' }
$configPath = Join-Path $PSScriptRoot 'config.local.json'
$config = Get-Content -Raw -LiteralPath $configPath | ConvertFrom-Json
Write-Host 'Allowlist fechada: ' ($config.allowlist -join ', ')
Write-Host 'Baileys e nao oficial: pode haver instabilidade ou bloqueio da conta. Use conta de teste consentida.'
Write-Host 'Gateway Node local usa dependencias previamente autorizadas. Nenhuma credencial Claude/Codex sera copiada.'
$consent = Read-Host 'Para iniciar o gateway Node e parear sua conta de teste, digite PAREAR. Qualquer outra resposta cancela'
if ($consent -cne 'PAREAR') { throw 'Pareamento nao autorizado.' }
$envPath = Join-Path $PSScriptRoot '.env'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$envText = [IO.File]::ReadAllText($envPath)
$envText = $envText -replace '(?m)^WHATSAPP_PAIRING_CONSENT=.*$', 'WHATSAPP_PAIRING_CONSENT=SIM'
[IO.File]::WriteAllText($envPath,$envText,$utf8)
$tokenLine = @($envText -split "`n" | Where-Object { $_ -match '^GATEWAY_TOKEN=' })[0]
$token = $tokenLine.Substring('GATEWAY_TOKEN='.Length).Trim()
$headers = @{ Authorization = ('Bearer ' + $token) }
$gatewayProcess = $null
$nomesEnv = @('GATEWAY_TOKEN','ALLOWED_NUMBERS','WHATSAPP_PAIRING_CONSENT','DATA_DIR','GATEWAY_BIND_HOST')
$envAnterior = @{}
foreach ($chaveEnv in $nomesEnv) { $envAnterior[$chaveEnv] = [Environment]::GetEnvironmentVariable($chaveEnv,'Process') }
$qrPath = Join-Path $PSScriptRoot 'dados\qr-privado.svg'
New-Item -ItemType Directory -Force -Path (Split-Path $qrPath) | Out-Null
try {
  $env:GATEWAY_TOKEN = $token
  $env:ALLOWED_NUMBERS = ($config.allowlist -join ',')
  $env:WHATSAPP_PAIRING_CONSENT = 'SIM'
  $env:DATA_DIR = Join-Path $PSScriptRoot 'dados\gateway-node'
  $env:GATEWAY_BIND_HOST = '127.0.0.1'
  $gatewayProcess = Start-Process -FilePath $node.Source -ArgumentList 'server.mjs' -WorkingDirectory (Join-Path $PSScriptRoot 'gateway') -WindowStyle Hidden -PassThru
  foreach ($chaveEnv in $nomesEnv) { [Environment]::SetEnvironmentVariable($chaveEnv,$envAnterior[$chaveEnv],'Process') }
  $connected = $false
  $openedAt = [DateTime]::MinValue
  $deadline = (Get-Date).AddMinutes(5)
  Write-Host 'Escaneie o QR somente no seu computador: WhatsApp > Aparelhos conectados. Nao compartilhe a tela.'
  while ((Get-Date) -lt $deadline) {
    if ($gatewayProcess.HasExited) { throw 'Gateway Node encerrou; conexao nao confirmada.' }
    try {
      $health = Invoke-RestMethod -Uri 'http://127.0.0.1:3210/health' -TimeoutSec 5
      if ($health.connected -eq $true) { $connected = $true; break }
      if ($health.status -in @('startup_error','storage_error','disconnected')) { throw ('Gateway: '+$health.status+'. Veja guia; nao repetir envios.') }
      if (((Get-Date) - $openedAt).TotalSeconds -ge 35) {
        try {
          Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:3210/qr.svg' -Headers $headers -OutFile $qrPath -TimeoutSec 5 | Out-Null
          Invoke-Item -LiteralPath $qrPath
          $openedAt = Get-Date
        } catch { } # QR ainda nao chegou/expirou; nenhuma resposta comercial enviada.
      }
    } catch { if ($_.Exception.Message -like 'Gateway:*') { throw } }
    Start-Sleep -Seconds 2
  }
  if (-not $connected) { throw 'Pareamento nao confirmado em cinco minutos; gateway sera parado. Inicie novamente apenas quando estiver pronto.' }
  Remove-Item -LiteralPath $qrPath -Force -ErrorAction SilentlyContinue
  Write-Host 'Conexao do gateway confirmada; isso NAO prova que uma mensagem real foi entregue.'
  $sendConsent = Read-Host 'Para responder automaticamente APENAS novas entradas da allowlist durante esta sessao, digite ENVIAR'
  if ($sendConsent -cne 'ENVIAR') { throw 'Envio nao autorizado.' }
  $config.envio_autorizado = $true
  [IO.File]::WriteAllText($configPath,($config | ConvertTo-Json -Depth 8),$utf8)
  Invoke-KitPython .\agente.py iniciar
  if ($LASTEXITCODE -notin @(0,130)) { throw 'Agente parou com falha. Nao repita mensagem incerta; revise dados locais.' }
} finally {
  $config.envio_autorizado = $false
  [IO.File]::WriteAllText($configPath,($config | ConvertTo-Json -Depth 8),$utf8)
  $envText = $envText -replace '(?m)^WHATSAPP_PAIRING_CONSENT=.*$', 'WHATSAPP_PAIRING_CONSENT=NAO'
  [IO.File]::WriteAllText($envPath,$envText,$utf8)
  Remove-Item -LiteralPath $qrPath -Force -ErrorAction SilentlyContinue
  foreach ($chaveEnv in $nomesEnv) { [Environment]::SetEnvironmentVariable($chaveEnv,$envAnterior[$chaveEnv],'Process') }
  if ($gatewayProcess -and -not $gatewayProcess.HasExited) { Stop-Process -InputObject $gatewayProcess -ErrorAction Continue }
  Write-Host 'Agente e gateway Node parados. A sessao permanece em dados/gateway-node; desvincule no WhatsApp se nao for continuar.'
}
