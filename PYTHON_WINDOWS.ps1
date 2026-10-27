# Usa somente Python existente, sem instalar ou alterar PATH/politica.
$script:kitPythonExe = $null
$script:kitPythonPrefix = @()
foreach ($candidato in @('python','py')) {
  $comandos = @(Get-Command $candidato -CommandType Application -ErrorAction SilentlyContinue)
  foreach ($comando in $comandos) {
    if ($comando.Source -match '\\Microsoft\\WindowsApps\\') { continue }
    $prefixo = @()
    if ($candidato -eq 'py') { $prefixo = @('-3') }
    try {
      & $comando.Source @prefixo -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" 2>$null
      $executou = $?
      if ($executou -and $LASTEXITCODE -eq 0) {
        $script:kitPythonExe = $comando.Source
        $script:kitPythonPrefix = $prefixo
        break
      }
    } catch { continue }
  }
  if ($script:kitPythonExe) { break }
}
if (-not $script:kitPythonExe) { throw 'Nenhum Python 3.10+ funcional em python ou py -3. Nada instalado.' }
function Invoke-KitPython {
  & $script:kitPythonExe @kitPythonPrefix @args
}
