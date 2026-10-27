# Evidências e limites — atualizado em 27/10/2026

## Executado neste workspace Linux

- Testes unitários Python com entradas sintéticas e CLIs/canal mockados.
- Compilação Python.
- Testes Node puros das regras de gateway e sintaxe JavaScript.
- Smoke HTTP do servidor sem consentimento: estado desconectado; endpoints privados exigem token;
  nenhuma sessão, QR ou envio permitido. Baileys não foi importado nesse smoke.
- Métodos Codex conferidos no `--help` do CLI 0.163.0 local sem executar o modelo.
- Métodos Claude e Baileys conferidos em documentação/código oficial.

Contagens finais e saída dos comandos estão em `TESTES-EXECUTADOS.txt` e `gateway/TESTES-EXECUTADOS.txt`.

## Verificação real no Windows — 27/10/2026

Relatório completo: [VALIDACAO_WINDOWS_20261027.md](VALIDACAO_WINDOWS_20261027.md).

- Windows 10.0.26200.0; Python 3.13.13. **43 testes Python passaram no Windows**.
- `py -3` não encontrou Python, mas `python` funcionou. Novo `PYTHON_WINDOWS.ps1` detecta uma opção funcional sem instalar programas nem alterar PATH/política.
- Sintaxe dos três PS1 passou; helper executado no PowerShell do executor com Python real.
- Codex autenticado por assinatura fez geração real pelo adaptador: `ok_sintetico`, exit 0.
- Claude nativo 2.1.311 localizado e autenticação por assinatura confirmada; geração Claude **não testada**.
- Docker Desktop/Compose instalados; processos abertos com autorização. Último probe: daemon Linux indisponível, pipe `dockerDesktopLinuxEngine` ausente.
- Windows PowerShell 5.1 bloqueou dot-source por política. **Não alterada nem contornada**. Isso não autoriza bypass.
- Nenhum `.env`, configuração, segredo de gateway, importação real, aprovação comercial, QR ou envio criado/executado.
- Após incorporar o patch, no workspace Linux: 43 testes Python, 17 Node, compilação/sintaxe e integração HTTP mockada passaram novamente.

## Não executado / não alegado

- Instalação/preparação completa pelos scripts no Windows; PowerShell 5.1 bloqueou execução por política. Build e execução do gateway Docker não ocorreram.
- Conexão real do Baileys; a instalação/importação da árvore npm foi verificada posteriormente, conforme seção final.
- Geração Claude real e avaliação de billing. Autenticação dos dois CLIs e geração Codex real foram verificadas conforme seção acima.
- Escaneamento de QR, pareamento, mensagem WhatsApp real ou entrega no celular.
- Canal com JIDs exclusivamente LID, anexos, áudio, documentos, Google Drive, Instagram ou follow-up.

Não é produção homologada. O título correto é **kit de laboratório implementado com validação offline**.

## Fontes

- Adaptador comercial baseado na V2 local fornecida para esta tarefa, com revisão de catálogo determinística.
- [Codex CLI oficial](https://developers.openai.com/codex/cli/) e help local 0.163.0.
- [Claude CLI oficial](https://code.claude.com/docs/en/cli-reference) e [execução programática](https://code.claude.com/docs/en/headless).
- Baileys, pacote e exemplo versionados: fontes completas em `gateway/README.md`.

A ausência de API paga no código não garante que recursos de cobrança extra pré-ativados na conta estejam desligados.
O titular deve verificar isso no fornecedor. O kit não lê nem altera configurações privadas de billing.

## Publicação do código

Publicado em 26/10/2026 no repositório público `ibcappainstituto-arch/agente-whatsapp`.
Primeiro commit do kit: `f4f000435a395518ea77f3f8035c2c62e9feb1ec`.
A branch remota e os hashes Git dos 31 arquivos foram conferidos. Publicação não substitui os testes reais pendentes acima.

## Node direto no Windows — 27/10/2026

- Node 24.15.0/npm 11.17.0 já instalados; nenhuma instalação foi realizada para esse teste.
- `INICIAR_NODE.ps1` adicionado: sem Docker, npm automático, mudanças de política ou criação automática de segredo. Recusa pacotes ausentes/versões divergentes antes de configuração/pareamento.
- Servidor com bind padrão127.0.0.1 e DATA_DIR absoluto explícito; Compose mantém bind interno0.0.0.0 apenas para publicação externa127.0.0.1.
- Windows: 43 testes Python,17 regras Node,sintaxe e integração HTTP mockada passaram. Launcher real parou ao encontrar baileys ausente.
- Pacotes reais baileys7.0.0-rc14/qrcode1.5.4 e árvore npm não instalados/validados; nenhum QR, sessão WhatsApp ou mensagem real.
- Caminho Node recomendado reduz pré-requisitos; não transforma mock em canal real validado.

## Dependências reais e health Node no Windows — atualização27/10/2026

- npm canônico, dependências diretas baileys7.0.0-rc14 e qrcode1.5.4; npm ci --ignore-scripts, nenhum lifecycle executado.
- Lockfile v3 SHA2569cc312f9812aae819ce9c61cd2265c2fd594e52defdd39e65163953f0bbf0fed;124 entradas de dependências mais a raiz (125 objetos packages);98 pacotes instalados aplicáveis ao Windows.
- Imports reais dos dois módulos passaram sem conexão. Health real consent_required/connected:false;QR409,send503,API sem token401,eventos vazios.
- Token só efêmero; processo encerrado; nenhuma sessão/journal, .env ou configuração persistente.43Python/17Node passaram.
- Isto supera apenas a pendência anterior de instalar/importar pacotes. Geração Claude real, Baileys conectado,pareamento e mensagem WhatsApp continuam pendentes.
- Artefatos de evidência: PREPARACAO-NODE-CLAUDE-CODE-20261027.json e RODAR_NO_CLAUDE_CODE.md.
