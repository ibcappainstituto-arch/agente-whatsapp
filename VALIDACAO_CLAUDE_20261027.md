# Claude CLI: geração real e preservação de contexto — 27/10/2026

## Comprovado no executor Windows

Uma geração sintética real pelo adaptador `cli_adapter.obter_decisao`, motor Claude e executável nativo, retornou `{"status":"ok_sintetico"}`; exit0, envelope `success`, `is_error:false`.

O ensaio usou pasta temporária isolada, prompt/schema sintéticos, ferramentas e MCP desabilitados e nenhuma persistência de sessão. Sem fonte comercial privada, nova autenticação ou fallback de API. Os44 testes Python do projeto passaram no Windows; a mesma suíte passou no workspace Linux após incorporar o patch incremental.

## Defeito corrigido

O adaptador removia `CLAUDECODE` e `CLAUDE_CODE_ENTRYPOINT` do ambiente filho. Agora os preserva, mantendo as proteções de contexto/sessão aninhada do fornecedor. Um teste unitário cobre essa preservação. A recusa de variáveis de API/provedor e a verificação de autenticação por assinatura continuam intactas.

**Não remover esses marcadores para forçar outra instância.** Se o fornecedor bloquear uma chamada, parar e reportar o limite real; não trocar credencial, limpar marcadores ou usar API como contorno.

## Não comprovado

O processo pai do ensaio **não tinha `CLAUDECODE`**: a geração foi chamada a partir de um terminal externo, não do terminal interno de uma sessão Claude Code. Portanto:

- Geração real por Claude CLI externo: **passou**.
- Execução aninhada a partir do terminal interno do Claude Code: **não testada**; não presumir que a versão instalada aceita ou rejeita sem evidência.
- Importação de fonte comercial real, respostas comerciais, pareamento e duas trocas WhatsApp com entrega no segundo aparelho: **não validados**.
- Sucesso neste ensaio não garante cota futura nem configurações de cobrança da conta.

Claude Code continua sendo o ponto de entrada para conduzir o trabalho no projeto, não uma alegação de integração nativa ou de fluxo ponta a ponta já aprovado dentro dele. O ensaio ocorreu com gateway parado e porta3210 fechada, sem QR ou mensagem WhatsApp.

## Ensaio adicional: marcadores simulados preservados

Uma segunda geração sintética real, executada separadamente no Windows com Claude nativo2.1.311, preservou `CLAUDECODE=1` e `CLAUDE_CODE_ENTRYPOINT=cli`. Pelo adaptador em modo `--print`, retornou `{"status":"ok_sintetico_aninhado"}`, exit0 e envelope `success`. Nenhuma proteção foi removida; nenhuma ferramenta/MCP, fonte privada, nova autenticação ou conexão WhatsApp foi usada.

**É simulação do ambiente de uma sessão Claude Code a partir de processo externo, não execução no terminal interno do aplicativo.** Não se deve afirmar bloqueio inevitável de `--print` nesta versão, nem afirmar que o fluxo completo dentro do app passou. A gestão de processos no app e a conversa WhatsApp ponta a ponta continuam pendentes de ensaio autorizado. O gateway permaneceu parado, porta3210 fechada.
