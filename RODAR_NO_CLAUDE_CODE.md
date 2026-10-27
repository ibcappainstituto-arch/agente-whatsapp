# Abrir o projeto no Claude Code e conduzir os processos locais

Não há instalação de aplicação Windows, serviço, wizard ou atalhos. Docker não é necessário nesta rota. Claude Code conduz o projeto e seus processos Node/Python; não tem WhatsApp nativo. O motor escolhido continua dependendo do CLI autenticado e limite disponível.

Percurso principal e pedido completo: [COMANDO_02_CLAUDE_CODE.md](COMANDO_02_CLAUDE_CODE.md). Resumo para colar depois de abrir esta pasta no Claude Code:

> Leia RODAR_NO_CLAUDE_CODE.md e as instruções do projeto. Use o Node/Python já existentes e minha pasta conhecimento_agente já pronta, sem refazê-la. Confira dependências e fonte comercial. Não instale aplicação Windows nem use Docker. Antes de criar configuração/segredo persistente, pareamento ou envio, pare e obtenha minha autorização específica. Depois de autorizado, conduza os processos locais no terminal e mantenha o gateway ativo, mostrando somente status sem expor segredo ou QR na tela da aula. Não envie mensagens fora dos contatos de teste consentidos.

## Preparação confirmada no computador Windows de validação

Node 24.15.0, npm 11.17.0, Python 3.13.13. Instaladas somente dependências do gateway local: baileys 7.0.0-rc14 e qrcode 1.5.4. A árvore tem lockfile v3; todas as 124 entradas resolvidas apontam ao npm canônico. Instalação trouxe 98 pacotes aplicáveis à plataforma, com --ignore-scripts; nenhum lifecycle foi executado. Encontrados preinstall/prepare do Baileys e postinstall de protobufjs, deixados desativados. Não há fallback para origem Git/servidor externo.

Importação real dos dois módulos passou, sem chamar função de conexão. Health real Node respondeu consent_required/connected:false. QR=409, send=503, API não autenticada=401, eventos vazios; nenhuma sessão ou journal. Foi usado token efêmero apenas do teste, não persistido. O processo de teste foi encerrado. Isso NÃO prova Baileys conectado, pareamento ou entrega WhatsApp.

## Conferir e manter processos

Checagens sem criar configuração:

```powershell
node --version
npm --prefix gateway ls --depth=0
python -m unittest discover -s tests -q
node --test gateway/test*.mjs
```

Depois de configuração, fonte e consentimentos explicitamente autorizados, o comando técnico do gateway é `node server.mjs` dentro de gateway. O assistente precisa fornecer ao processo as variáveis autorizadas GATEWAY_TOKEN, ALLOWED_NUMBERS, WHATSAPP_PAIRING_CONSENT, DATA_DIR absoluto e GATEWAY_BIND_HOST=127.0.0.1. Não imprimir valores. O projeto não recebe permissão para gerar esses valores nesta preparação.

O gateway pode ficar num terminal ativo do Claude Code ou numa tarefa de background controlada por ele, sem instalar serviço. O processo Python de atendimento é separado e só inicia após autorização de envio e fonte aprovada. Fechar terminal/tarefa ou suspender computador pode interromper o atendimento; não prometer disponibilidade contínua.

Conferir apenas saúde, sem segredo:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:3210/health
```

Parar: Ctrl+C no terminal do gateway e no terminal do agente. Se o assistente iniciou em background, encerrar somente os PIDs que ele próprio iniciou, sem matar outros processos Node ou aplicativos. O auxiliar INICIAR_NODE.ps1 já preparado pode ser inspecionado como referência de orquestração; não é uma atividade extra exigida do aluno nem autorização para executar scripts bloqueados por política.

API em 127.0.0.1:3210, sem painel de gestão. Dados de sessão/journal em dados/gateway-node; nada do Docker ou instalações antigas é copiado. QR é privado e só pode ser obtido depois de consentimento; não abrir/projetar durante compartilhamento da aula. Configuração persistente, importação real da fonte, pareamento e envio continuam pendentes de autorização.

## Bloqueio de prontidão após o piloto

Antes de qualquer novo pareamento, leia QR_DIAGNOSTICO_20261027.md. O gateway foi corrigido offline para não fornecer QR localmente após15s/invalidação; isso não corrige nem comprova a conexão real. Não entregue QR por chat. Visualizador privado LOCAL com atualização por eventos e remoção na expiração/desconexão ainda precisa ser implementado/validado; os SVG estáticos dos launchers não atendem ao requisito. Pare na preparação offline até cumprir esse critério e obter autorização para ensaio ponta a ponta. Não anunciar o agente pronto nem iniciar nova demonstração automática.
