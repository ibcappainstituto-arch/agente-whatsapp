# Evidências e limites — 26/10/2026

## Executado neste workspace Linux

- Testes unitários Python com entradas sintéticas e CLIs/canal mockados.
- Compilação Python.
- Testes Node puros das regras de gateway e sintaxe JavaScript.
- Smoke HTTP do servidor sem consentimento: estado desconectado; endpoints privados exigem token;
  nenhuma sessão, QR ou envio permitido. Baileys não foi importado nesse smoke.
- Métodos Codex conferidos no `--help` do CLI 0.163.0 local sem executar o modelo.
- Métodos Claude e Baileys conferidos em documentação/código oficial.

Contagens finais e saída dos comandos estão em `TESTES-EXECUTADOS.txt` e `gateway/TESTES-EXECUTADOS.txt`.

## Não executado / não alegado

- PowerShell no Windows, instalador no computador do aluno, build e execução Docker.
- Instalação npm ou validação da árvore transitiva (sem lockfile nesta versão).
- Login por assinatura real, modelo real, limites/cobrança da conta.
- Escaneamento de QR, pareamento, mensagem WhatsApp real ou entrega no celular.
- Canal com JIDs exclusivamente LID, anexos, áudio, documentos, Google Drive, Instagram ou follow-up.
- Publicação deste kit em repositório remoto.

Não é produção homologada. O título correto é **kit de laboratório implementado com validação offline**.

## Fontes

- Adaptador comercial baseado na V2 local fornecida para esta tarefa, com revisão de catálogo determinística.
- [Codex CLI oficial](https://developers.openai.com/codex/cli/) e help local 0.163.0.
- [Claude CLI oficial](https://code.claude.com/docs/en/cli-reference) e [execução programática](https://code.claude.com/docs/en/headless).
- Baileys, pacote e exemplo versionados: fontes completas em `gateway/README.md`.

A ausência de API paga no código não garante que recursos de cobrança extra pré-ativados na conta estejam desligados.
O titular deve verificar isso no fornecedor. O kit não lê nem altera configurações privadas de billing.
