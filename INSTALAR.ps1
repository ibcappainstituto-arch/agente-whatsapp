# Preparacao local. NAO instala programas, NAO pareia WhatsApp, NAO envia mensagens.
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
. (Join-Path $PSScriptRoot 'PYTHON_WINDOWS.ps1')
Invoke-KitPython -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Testes locais falharam. Nao prossiga.' }
if (-not (Test-Path -LiteralPath '.\config.local.json')) {
  $motor = Read-Host 'Motor ja instalado e autenticado por assinatura (codex ou claude)'
  if ($motor -notin @('codex','claude')) { throw 'Escolha codex ou claude.' }
  $nome = Read-Host 'Seu nome profissional'
  $numeros = Read-Host 'Numero(s) de TESTE consentido(s), DDI+DDD+numero; separe por virgula. Nao use lista de clientes'
  Invoke-KitPython .\agente.py preparar --motor $motor --nome $nome --numeros $numeros
  if ($LASTEXITCODE -ne 0) { throw 'Configuracao nao concluida.' }
}
$config = Get-Content -Raw -LiteralPath '.\config.local.json' | ConvertFrom-Json
if (-not (Test-Path -LiteralPath '.\fonte_comercial\servicos.csv')) {
  $pasta = Read-Host 'Caminho completo da pasta conhecimento_agente ja criada (seis Markdown)'
  Invoke-KitPython .\importar_conhecimento.py --pasta $pasta --motor $config.motor --destino '.\fonte_comercial'
  if ($LASTEXITCODE -ne 0) { throw 'Importacao nao concluida. Leia PENDENCIAS.md se criado; os originais foram preservados.' }
  if (-not (Test-Path -LiteralPath '.\fonte_comercial\servicos.csv') -or -not (Test-Path -LiteralPath '.\fonte_comercial\REVISAO.md')) { throw 'Proposta incompleta: nao aprovar nem parear.' }
}
Write-Host ''
Write-Host 'Preparacao concluida SEM pareamento e SEM envio.'
Write-Host '1. Revise fonte_comercial\REVISAO.md e servicos.csv contra seus Markdown.'
Write-Host '2. Resolva somente lacunas indicadas; nada foi inventado ou aprovado automaticamente.'
Write-Host '3. Para aprovar conscientemente: python agente.py hash-fonte'
Write-Host '   Depois: python agente.py aprovar-fonte --sha256 HASH_QUE_VOCE_REVISOU'
Write-Host '4. Leia INSTALAR_WINDOWS.md antes de executar .\INICIAR.ps1.'
