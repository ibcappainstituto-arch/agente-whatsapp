# Gateway Node local, conduzido pelo Claude Code — sem Docker obrigatório

No Windows usado na validação, Node 24.15.0 e npm 11.17.0 já existiam; requisito Node >=22 atendido. Cada aluno deve verificar suas próprias versões.
Comando técnico do gateway: `node server.mjs`, dentro de `gateway`.

Dependências diretas exatas: `baileys@7.0.0-rc14` e `qrcode@1.5.4`. Foram instaladas na cópia Windows de validação, com scripts desativados. O package-lock.json v3 acompanha o projeto; não há node_modules no repositório. Cada computador precisa de sua própria instalação autorizada. A instalação dessas dependências e revisão dos scripts/árvore exigem autorização antes de tentar o canal real.

O launcher separado `INICIAR_NODE.ps1` depende da correção `PYTHON_WINDOWS.ps1` já entregue. Não chama Docker nem npm e não instala nada. Verifica Node, versões das dependências locais, porta livre, fonte comercial e CLI autenticado. Não altera a política de execução. Se a política bloquear, parar; sem bypass.

Após configurações previamente autorizadas, mantém os consentimentos separados PAREAR e ENVIAR do launcher original. Não criar nova fonte: usar a pasta conhecimento_agente que o usuário já preparou. A importação e aprovação continuam etapas explícitas. Este launcher não cria segredo ou configuração por conta própria.

API local em http://127.0.0.1:3210; `/health` é diagnóstico, não há painel de gestão web. `/qr.svg` exige token e QR é privado, não deve aparecer na aula. Variáveis do processo Node recebem token/allowlist já autorizados; o ambiente do launcher é restaurado. Sessão e journal ficam em `dados/gateway-node`, separados do volume Docker e protegidos pelo .gitignore existente. DATA_DIR absoluto é obrigatório; não há fallback para pasta raiz do Windows.

O servidor usa loopback por padrão. Compose recebe somente uma variável de bind para preservar a conectividade dentro do container existente, sem mudar sua publicação 127.0.0.1. Isso é ajuste de fonte para compatibilidade, não alteração do Docker Desktop/WSL. Nenhum socket Docker foi acessado nesta alternativa.

Validação: 43 testes Python e 17 regras Node passaram; análise de sintaxe PowerShell e node --check passaram. Integração HTTP Windows com Baileys falso passou fora do sandbox restrito, incluindo idempotência, journal e reconexão515 limitada; não usa dependências reais ou conta WhatsApp. Na execução restrita inicial, o teste não observou eventos. Launcher real foi executado somente até recusar dependência baileys ausente, antes de qualquer configuração/pareamento.

Continua NÃO validado: Baileys conectado, pareamento e envio. Instalação/imports da árvore real e health desconectado passaram no Windows, conforme RODAR_NO_CLAUDE_CODE.md. Nenhum segredo operacional, QR ou mensagem real criado. A alternativa elimina a dependência de Docker, mas não elimina autorização de instalação, pareamento e teste supervisionado.

## Ordem de execução

1. Revise os seis Markdown já criados em `conhecimento_agente`.
2. Autorize explicitamente a preparação local antes de criar `.env`/chave do gateway e antes de qualquer instalação npm. O launcher não faz nenhuma dessas instalações.
3. Confira `gateway/package.json`: duas dependências diretas exatas. Após autorização separada, a instalação ocorre somente em `gateway`, nunca globalmente. A árvore transitiva e scripts precisam ser revistos; use o lockfile fornecido com npm ci --ignore-scripts, conforme COMECE_NO_CLAUDE_CODE.md. Não regenere nem execute scripts automaticamente. Nenhum comando npm deve ser executado silenciosamente pelo assistente.
4. Siga `INSTALAR_WINDOWS.md` para importar e revisar a fonte comercial; aprove o SHA somente depois da leitura.
5. O assistente conduz os processos pelo Claude Code. Como suporte opcional, se a política atual permitir, ele pode usar `.\INICIAR_NODE.ps1` na raiz. O programa recusa Node incompatível, pacotes ausentes/versões erradas, porta ocupada e fonte/login não verificados antes de pedir PAREAR e ENVIAR.
6. Não execute Node e Docker juntos. Ctrl+C encerra o agente; o launcher encerra somente o processo Node que ele criou e preserva sessão/journal privados.

Baileys é a biblioteca do gateway implementado neste kit. Referências ao OpenWA em materiais históricos não significam que o pacote OpenWA seja usado nesta versão.

## Bloqueio de prontidão após o piloto

Antes de qualquer novo pareamento, leia QR_DIAGNOSTICO_20261027.md. O gateway foi corrigido offline para não fornecer QR localmente após15s/invalidação; isso não corrige nem comprova a conexão real. Não entregue QR por chat. Visualizador privado LOCAL com atualização por eventos e remoção na expiração/desconexão ainda precisa ser implementado/validado; os SVG estáticos dos launchers não atendem ao requisito. Pare na preparação offline até cumprir esse critério e obter autorização para ensaio ponta a ponta. Não anunciar o agente pronto nem iniciar nova demonstração automática.
