# Visualizador QR privado — implementado, Tk oculto validado; layout visível pendente

Integrado ao kit após a correção QR do commit `30b99a53dfed4f39607fff0316d08853c065d011`. Não é instalador, plugin, serviço público ou integração nativa do Claude. Testes offline passaram; Tk real oculto passou no Windows; layout visível e fluxo WhatsApp continuam pendentes.

## O que está implementado

Janela Tkinter local com imagem PNG apenas em memória. Lê exclusivamente `GATEWAY_TOKEN` do `.env` privado existente na mesma pasta, exige uma única ocorrência válida de 64 caracteres hexadecimais minúsculos e não escreve configuração. Não lê tokens Claude/Codex; não usa segredo em URL, argumento de linha de comando, variável de ambiente do visualizador ou log.

Faz **somente GET** em `http://127.0.0.1:3210/qr/frame`, com Bearer no cabeçalho. Usa conexão HTTP direta: sem proxy do ambiente, redirecionamento, cookie, navegador, CORS ou nova porta de escuta. Não inicia gateway, não pede pareamento, não concede consentimento, não faz login de IA e não envia mensagens. O gateway precisa já estar iniciado pelo fluxo local expressamente autorizado.

O endpoint novo reutiliza a sessão, autenticação e biblioteca `qrcode` **já existentes**. Não muda `package.json` nem lockfile. Renderiza somente quando a sessão permite QR e revalida `snapshot/isCurrent` após o trabalho assíncrono. Pareamento, conexão, fechamento, rotação e expiração invalidam quadros; o latch da correção1 continua bloqueando QR tardio do transporte antigo. A geração numérica cresce inclusive após novo transporte.

## Validade conservadora e limites honestos

- O gateway mantém janela local máxima de 15 segundos; **não é confirmação da validade no WhatsApp**.
- O visualizador oculta a imagem **antes** de cada consulta. Solicita nova verificação a cada 0,50 s; mantém no máximo uma requisição em andamento.
- O prazo é calculado com relógio monotônico **desde o início da requisição**, não desde a chegada. Desconta 0,20 s de margem e usa lease de exibição de no máximo 0,75 s.
- Resposta que leva mais de 0,75 s é descartada. Imagem expirada, falha, desconexão observada ou mudança de estado remove o quadro. A UI mostra a contagem da **verificação local curta**, nunca “WhatsApp válido”.
- Uma checagem de relógio ocorre a cada 25 ms enquanto o event loop está responsivo. Polling não conhece uma desconexão instantaneamente; há atraso de observação. Um travamento do sistema/janela pode reter pixels na tela. Não se promete apagamento remoto nem proteção contra captura de tela.
- Ocultar, perder o foco, minimizar ou fechar remove a imagem e invalida resposta de worker pendente. Retomar exige clique em **Exibir nesta tela privada**.
- Gerações antigas não voltam a ser exibidas. Se o processo gateway for reiniciado e sua contagem voltar a zero, feche e reabra o visualizador após revisar a sessão; não existe recuperação automática que abra pareamento.
- PNG tem limite de bytes e dimensões antes de decodificar. Nada é salvo como `.png`/`.svg`; não há fallback para arquivo ou navegador.

## Uso conduzido pelo Claude Code local

Use o Python existente do projeto, em sessão gráfica **privada**. O comando técnico é `python qr_viewer.py` na raiz, sem token, URL ou caminho como argumento. O assistente pode iniciá-lo no terminal, mantendo a janela fora de projeção/compartilhamento. A janela começa oculta; **Exibir nesta tela privada** inicia somente consultas de leitura ao gateway já autorizado. O visualizador não inicia gateway ou WhatsApp, não cria `.env` e não concede consentimentos.

Os launchers opcionais `INICIAR_NODE.ps1` e `INICIAR.ps1` foram atualizados para abrir esse processo e encerrá-lo no cleanup. Não salvam QR em disco nem reabrem SVG a cada35s. Fazem preflight de importação Tk, sem instalação ou bypass. A leitura de configuração usa UTF8 explícito para não corromper nomes no Windows PowerShell5.1. Os quatro scripts passaram no parser Windows PowerShell5.1/PowerShell7; execução operacional dos launchers permanece pendente.

Se iniciado separadamente, fechar a janela **não para o gateway** nem autoriza envio: o assistente precisa encerrar os processos que iniciou ao terminar. Se o launcher iniciar a janela e ela fechar antes da confirmação de conexão, o launcher cancela e encerra seu próprio gateway. `/qr.svg` é compatibilidade técnica, não fallback de interface nem caminho de aula.

## Arquivo privado e dependências locais

- `.env` deve existir previamente; ausência, duplicidade ou token inválido bloqueiam a janela. O leitor não executa conteúdo `.env`, shell ou dotenv.
- Em POSIX, exige modo **600** (sem acesso de grupo/outros). O gerador atual do kit pode criar 644 por causa do umask; isso causará bloqueio deliberado. O visualizador **não muda permissões automaticamente**. Revisar e corrigir o arquivo local somente no contexto autorizado.
- No Windows, bits POSIX não comprovam ACL. A permissão NTFS precisa ser inspecionada localmente; não foi validada neste ambiente.
- Python com Tk/Tcl e sessão gráfica local são necessários. Se indisponíveis, a execução falha sem baixar nada e sem alternativa de navegador. Não se instalou Python/Tk nem dependência NPM neste trabalho.

## Testes executáveis sem conta e sem display

Na raiz do kit, sem conta ou display:

```text
python -m unittest discover -s tests -p "test_viewer*.py" -v
python -m unittest discover -s tests -p "test_http_frame_mock.py" -v
node --test gateway/test_qr.mjs gateway/test_frame.mjs
python gateway/test_http_mock.py
python gateway/test_http_qr_mock.py
```

Os testes usam apenas texto sintético e um PNG branco de 1×1 pixel — **não é um QR**. Nestes testes do visualizador não houve autenticação real, conexão WhatsApp, pareamento, envio ou screenshot. As gerações Claude externas documentadas separadamente não foram usadas pela UI.

**Atualização Windows:** Tk8.6.15 real em janela withdrawn decodificou pixel branco1×1 e passou os controles/expiração, exit0. **Pendente:** layout visível, ACL local, operação dos launchers, QR real/leitura pelo telefone e integração completa com o fluxo Claude Code. Testes de controlador com widgets falsos não validam esses itens. Neste executor, o módulo Tk 9.0 é importável, mas não há DISPLAY/Wayland; nenhuma janela Tk foi criada.

Evidência detalhada e limites: [VALIDACAO_UI_WINDOWS_20261027.md](VALIDACAO_UI_WINDOWS_20261027.md). Nenhuma nova conexão ou pareamento foi realizado.
