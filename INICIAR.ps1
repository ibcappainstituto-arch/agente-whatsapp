# Operacao supervisionada. QR, allowlist e dados sao privados; nao projete este terminal.
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
. (Join-Path $PSScriptRoot 'PYTHON_WINDOWS.ps1')
Invoke-KitPython -c "import tkinter"
if ($LASTEXITCODE -ne 0) { throw 'Python existente sem Tk/Tcl. Visualizador privado indisponivel; nada sera instalado ou pareado.' }
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker Desktop oficial precisa estar instalado e aberto, em modo Linux containers.' }
& docker compose version
if ($LASTEXITCODE -ne 0) { throw 'Docker Compose indisponivel.' }
$osType = & docker info --format '{{.OSType}}'
if ($LASTEXITCODE -ne 0 -or $osType.Trim() -ne 'linux') { throw 'Docker Desktop nao esta pronto.' }
Invoke-KitPython .\agente.py verificar
if ($LASTEXITCODE -ne 0) { throw 'Fonte ou CLI nao verificados. Nao parear.' }
$configPath = Join-Path $PSScriptRoot 'config.local.json'
$config = Get-Content -Raw -Encoding UTF8 -LiteralPath $configPath | ConvertFrom-Json
Write-Host 'Allowlist fechada: ' ($config.allowlist -join ', ')
Write-Host 'Baileys e nao oficial: pode haver instabilidade ou bloqueio da conta. Use conta de teste consentida.'
Write-Host 'Docker baixara imagem Node e dependencias oficiais fixadas no projeto. Nenhuma credencial Claude/Codex sera copiada.'
$consent = Read-Host 'Para construir o gateway e parear sua conta de teste, digite PAREAR. Qualquer outra resposta cancela'
if ($consent -cne 'PAREAR') { throw 'Pareamento nao autorizado.' }
$envPath = Join-Path $PSScriptRoot '.env'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$envText = [IO.File]::ReadAllText($envPath)
$envText = $envText -replace '(?m)^WHATSAPP_PAIRING_CONSENT=.*$', 'WHATSAPP_PAIRING_CONSENT=SIM'
[IO.File]::WriteAllText($envPath,$envText,$utf8)
$tokenLine = @($envText -split "`n" | Where-Object { $_ -match '^GATEWAY_TOKEN=' })[0]
$token = $tokenLine.Substring('GATEWAY_TOKEN='.Length).Trim()
$viewerProcess = $null
try {
  & docker compose up --build -d
  if ($LASTEXITCODE -ne 0) { throw 'Build/inicio falhou. Nao houve confirmacao de pareamento ou envio.' }
  $connected = $false
  # Sem segredo em argumentos; o viewer so le GATEWAY_TOKEN do .env privado.
  $viewerArgs = @($script:kitPythonPrefix) + @('qr_viewer.py')
  $viewerProcess = Start-Process -FilePath $script:kitPythonExe -ArgumentList $viewerArgs -WorkingDirectory $PSScriptRoot -PassThru
  $deadline = (Get-Date).AddMinutes(5)
  Write-Host 'Na janela privada, clique Exibir. QR fica somente em memoria; nao compartilhe a tela nem envie imagem pelo chat.'
  while ((Get-Date) -lt $deadline) {
    if ($viewerProcess.HasExited) { throw 'Visualizador privado encerrou antes da confirmacao. Gateway sera parado; nao usar QR estatico.' }
    try {
      $health = Invoke-RestMethod -Uri 'http://127.0.0.1:3210/health' -TimeoutSec 5
      if ($health.connected -eq $true) { $connected = $true; break }
      if ($health.status -in @('startup_error','storage_error','disconnected')) { throw ('Gateway: '+$health.status+'. Veja guia; nao repetir envios.') }
    } catch { if ($_.Exception.Message -like 'Gateway:*') { throw } }
    Start-Sleep -Seconds 2
  }
  if (-not $connected) { throw 'Pareamento nao confirmado em cinco minutos; gateway sera parado. Inicie novamente apenas quando estiver pronto.' }
  if ($viewerProcess -and -not $viewerProcess.HasExited) { Stop-Process -InputObject $viewerProcess -ErrorAction Continue }
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
  if ($viewerProcess -and -not $viewerProcess.HasExited) { Stop-Process -InputObject $viewerProcess -ErrorAction Continue }
  & docker compose down
  Write-Host 'Agente e gateway parados. A sessao permanece no volume privado; desvincule no WhatsApp se nao for continuar.'
}
