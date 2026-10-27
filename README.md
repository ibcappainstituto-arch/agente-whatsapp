# Agente de WhatsApp conduzido pelo Claude Code

**Abra esta pasta no Claude Code autenticado e use [o comando 02](COMANDO_02_CLAUDE_CODE.md).** Não há aplicativo Windows para instalar, wizard obrigatório ou Docker obrigatório.

Repositório correto: https://github.com/ibcappainstituto-arch/agente-whatsapp

1. Se ainda não salvou seu conhecimento, use [comando01](COMANDO_01_SALVAR_CONHECIMENTO.md).
2. Abra a pasta do repositório no Claude Code e siga [COMECE_NO_CLAUDE_CODE.md](COMECE_NO_CLAUDE_CODE.md).
3. Aproveite os seis Markdown já preparados em `conhecimento_agente`; o importador preserva os originais e propõe catálogo rastreável, sem pedir redigitação.

O Claude Code conduz os processos **Node + Python deste projeto**, usando o CLI autenticado por assinatura. O canal WhatsApp é um **gateway Baileys próprio**, não uma integração nativa do Claude. Codex é um motor alternativo suportado. Referências a OpenWA pertencem a materiais históricos, não ao pacote usado aqui.

## Limites e autorizações

- Sem API paga nem fallback automático. Assinatura/cota continuam necessárias; app aberto não comprova login do CLI.
- Dependências npm do projeto, gravação de chave/configuração, pareamento e envio exigem suas autorizações específicas. Nenhum launcher instala npm ou muda a política do sistema silenciosamente.
- Gateway somente em127.0.0.1:3210 e allowlist fechada. Somente novas mensagens de contatos de teste consentidos; sem campanhas, grupos, anexos ou retomadas.
- Recusa, intervenção humana e envio incerto pausam o chat. Nenhum reenvio automático após timeout.
- Preços/contratação vêm da fonte revisada, não da resposta livre do modelo. Sem promessas de resultado judicial.
- QR, `.env`, configuração, sessões e dados são privados. Nunca projetar QR ou publicar esses itens.
- Scripts PowerShell e Docker são **suporte opcional**, não o percurso obrigatório do aluno. Não contornar bloqueio de política.

## O que já foi verificado

43 testes Python passaram no Windows e no Linux;17 regras Node e integração HTTP mockada passaram. Codex autenticado gerou resposta real. Claude teve autenticação confirmada, sem geração real testada ainda. O launcher Node recusou dependências ausentes antes de configurar/parear.

**Ainda não validados: árvore npm/Baileys real, geração Claude real, QR e mensagem WhatsApp real.** Baileys é não oficial e pode sofrer instabilidade/restrições. Consulte [VALIDACAO.md](VALIDACAO.md).
