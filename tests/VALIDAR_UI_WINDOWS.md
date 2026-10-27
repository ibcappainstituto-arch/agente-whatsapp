# Validação Windows isolada — sem gateway, conta ou QR

Este procedimento testa apenas a interface com um pixel branco sintético e a sintaxe PowerShell. Não inicia Node, WhatsApp, modelo, instalação ou conexão externa. Não lê `.env`, configuração, sessão ou conversas. Não usar número/conta de ninguém.

1. Materializar o ZIP pelo fluxo Library suportado no próprio executor Windows e extrair em **pasta nova isolada**. Não sobrepor o clone operacional nem copiar credenciais/configurações para a pasta de teste. Conferir `MANIFESTO-SHA256.json` contra os arquivos extraídos.
2. Usar Python já instalado/funcional. Não instalar Tk/Python e não alterar PATH/política. Se faltar Tk ou sessão gráfica, registrar bloqueio sem fallback.
3. Analisar os quatro scripts com o parser, **sem executar o conteúdo**:

```powershell
$falhou = $false
foreach ($nome in @('PYTHON_WINDOWS.ps1','INSTALAR.ps1','INICIAR.ps1','INICIAR_NODE.ps1')) {
  $tokens = $null; $erros = $null
  [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PWD $nome), [ref]$tokens, [ref]$erros) | Out-Null
  if ($erros.Count -gt 0) { $falhou = $true; Write-Output ($nome + ': PARSE_FAIL') }
  else { Write-Output ($nome + ': PARSE_PASS') }
}
if ($falhou) { throw 'Sintaxe PowerShell precisa de correção; nenhum script foi executado.' }
```

4. Na raiz extraída, executar somente:

```text
python tests/smoke_viewer_tk.py
```

O teste injeta leitor falso e PNG branco1×1 em memória; não é QR. O objeto de janela Tk permanece withdrawn (oculto) e fecha sozinho em até4,5s; valida PhotoImage/estado real, não layout visível. Não alterar foco de outros aplicativos, compartilhar tela, capturar screenshot ou salvar imagem. Se o teste não conseguir criar/desenhar a janela, reportar a falha; não afirmar GUI validada por testes falsos.

5. Devolver resultado seguro/exit code, versões Windows/Python/Tk e confirmação de que nenhum gateway/configuração/sessão foi usado. Não anexar tela, segredos, caminhos de usuário ou dados reais. Não tentar pareamento para completar este teste.

Um passe aqui não valida o launcher em operação, o terminal interno do Claude Code, pareamento ou entrega no telefone. Esses resultados são etapas separadas e exigem autorização própria.
