# Kit Windows — WhatsApp + Claude Code ou Codex local

**Versão de laboratório, 26/10/2026. Código implementado e testes offline; canal real ainda não validado.**

O WhatsApp fica em um gateway Baileys/Docker. O agente comercial e o CLI autenticado ficam no Windows.
Não usa Zernio, API paga de IA, instalador antigo, Docker para a IA nem cópia de sessões `.codex`/`.claude`.
Assinatura e seus limites continuam necessários; o programa bloqueia API/provedor alternativo e não faz fallback pago.

**Repositório desta versão:** https://github.com/ibcappainstituto-arch/agente-whatsapp

1. [Comando 01 — salvar conhecimento](COMANDO_01_SALVAR_CONHECIMENTO.md).
2. [Comando 02 — preparar o kit Windows](COMANDO_02_INSTALAR_WINDOWS.md).
3. [Guia técnico Windows](INSTALAR_WINDOWS.md).

**Comece pelo [INSTALAR_WINDOWS.md](INSTALAR_WINDOWS.md).** A pasta `conhecimento_agente` já preparada,
com seus seis Markdown, é a fonte primária. Não é necessário redigitar tudo em CSV.

Baixe este repositório em pasta nova (Code > Download ZIP) ou clone com Git. Abra a pasta extraída no Claude Code/Codex e siga o comando 02. Não execute comandos do repositório antigo supondo que sejam esta versão. Todos os scripts estão na raiz; não há subpasta adicional obrigatória.

## Limites importantes

- Somente texto novo de contatos de teste explicitamente autorizados. Lista vazia não libera ninguém.
- Sem campanhas, disparos iniciais, grupos, anexos, áudio, Instagram ou follow-ups.
- Recusa, intervenção manual, pedido de humano ou falha ambígua pausam a conversa; não há retomada automática.
- Preços e contratação vêm do catálogo revisado, não da resposta livre do modelo.
- QR e sessões são privados. Nunca projetar o QR para a turma.
- Baileys não é a plataforma oficial da Meta; não se promete ausência de bloqueio.
- Chats fornecidos apenas como `@lid` são ignorados; não se adivinha número nem se abre a lista.
- Sem teste real no Windows, build Docker, pareamento, IA autenticada ou envio real nesta entrega.

A documentação distingue implementação, testes mockados e validação real pendente. Leia `VALIDACAO.md`.
