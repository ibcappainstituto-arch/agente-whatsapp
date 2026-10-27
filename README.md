# Agente de WhatsApp conduzido pelo Claude Code

> **Candidato de QA:** esta revisão do visualizador está em validação offline; aguarda testes Windows. Não comprova GUI visível, pareamento ou WhatsApp ponta a ponta. Não usar para demonstração autônoma.

**Abra a pasta no Claude Code autenticado e use [o comando02](COMANDO_02_CLAUDE_CODE.md).** Não há aplicativo Windows para instalar, wizard obrigatório ou Docker obrigatório. O projeto ainda não está homologado para aula/operação autônoma.

Repositório: https://github.com/ibcappainstituto-arch/agente-whatsapp

1. Para preparar conhecimento, use [comando01](COMANDO_01_SALVAR_CONHECIMENTO.md).
2. Siga [COMECE_NO_CLAUDE_CODE.md](COMECE_NO_CLAUDE_CODE.md), aproveitando os seis Markdown de `conhecimento_agente`. Originais são preservados; nenhuma redigitação manual em CSV é exigida.
3. Claude Code conduz os processos **Node + Python deste projeto**. O WhatsApp depende de um **gateway Baileys próprio**, não integração nativa do Claude. Codex é motor alternativo. OpenWA é referência histórica, não o canal usado aqui.

## Limites e autorizações

- CLI por assinatura, sem API paga/fallback automático. Aplicativo aberto não prova login/cota.
- Dependências npm, chave/configuração persistente, pareamento e envio têm autorizações específicas. Não instalar software de sistema nem alterar política silenciosamente.
- Gateway somente em127.0.0.1:3210, allowlist fechada, novas entradas de contatos de teste consentidos; sem campanhas, grupos, anexos ou retomadas.
- Preços/contratação dependem da fonte revisada. Recusa, intervenção humana e envio incerto pausam o chat; não reenviar após timeout.
- QR, `.env`, configuração, sessão e dados ficam privados. Nunca publicar/projetar/transportar QR por chat.
- Scripts PowerShell e Docker são suporte **opcional**. Não contornar bloqueio de política.

## Correções e evidências

- QR: limite local15s, invalidação por eventos e bloqueio de timer tardio após pareamento. Diagnóstico sanitizado, sem erro bruto/segredos. **Causa das desconexões anteriores não determinada.**
- [Visualizador privado](VISUALIZADOR_QR_PRIVADO.md): janela Tkinter, PNG só em memória, leitura autenticada local, prazo/estado e retirada conservadora do quadro. Launchers não salvam SVG. GUI Windows ainda precisa de validação.
- Revisão Linux: **79 testes Python e36 Node**, incluindo HTTP de quadro mockado; mais dois HTTP mocks independentes. Não são testes WhatsApp.
- Windows:44 testes Python da base/CLI passaram. Codex e Claude geraram respostas sintéticas reais. Claude também passou com marcadores de sessão **simulados e preservados**; isso não foi execução no terminal interno do app. [Limite exato](VALIDACAO_CLAUDE_20261027.md).
- Dependências reais instaladas/importadas no projeto Windows com scripts desativados; lockfile incluído. Preparação real do gateway respondeu desconectado. O piloto posterior encerrou sem registro/conexão confirmados e sem envio.

**Ainda pendentes:** GUI/ACL e launchers atuais no Windows, condução real no terminal interno do Claude Code, fonte comercial aprovada e conversa WhatsApp ponta a ponta. Nenhum novo piloto deve ser iniciado sem combinar e autorizar o ensaio. Prontidão exige duas trocas, com resposta vista no segundo telefone; QR, health e logs não comprovam entrega. Consulte [VALIDACAO.md](VALIDACAO.md).
