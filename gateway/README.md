# Gateway Baileys — componente de laboratório

O cérebro roda no Windows. O canal usa este gateway Baileys em Node local (recomendado no Windows) ou, opcionalmente, no container Docker. Não é WhatsApp Business Platform oficial. A biblioteca pode deixar de funcionar e a conta pode sofrer restrições. Use uma conta de laboratório e destinatários que consentiram. Não conecte o número principal em uma aula sem avaliar esse risco.

## Estado de validação

- Código de proteção testado com `node --test gateway/test*.mjs` sem dependências ou conta.
- Integração HTTP com Baileys substituído por mock local (`python gateway/test_http_mock.py`): handshake515 limitado, credenciais persistidas antes de reconectar, idempotência, bloqueio de resposta incerta e journal. Não valida a biblioteca real nem WhatsApp.
- Sintaxe de `server.mjs` conferida por `node --check`.
- Smoke HTTP local sem consentimento: saúde desconectada, API sem token recusada, buffer vazio, QR indisponível e envio recusado; nenhuma sessão criada nem dependência Baileys importada.
- Não instalamos dependências, não construímos a imagem, não executamos Docker, não pareamos uma conta nem enviamos WhatsApp real neste ambiente.
- Dependências e árvore fixadas em package-lock.json v3. Instalação/imports reais passaram no Windows com lifecycle scripts desativados; o build Docker opcional continua não testado. Não anunciar produção ou WhatsApp conectado validado.

## Configuração (arquivo `.env` da raiz)

- `GATEWAY_TOKEN`: segredo aleatório URL-safe de pelo menos 32 caracteres, igual no agente Windows; não é chave API paga.
- `ALLOWED_NUMBERS`: números E164 explícitos separados por vírgula. Exemplo estrutural: `+<país><DDD><número>` (não copie os colchetes). Vazio = ninguém. Nunca `*`.
- `WHATSAPP_PAIRING_CONSENT=SIM`: somente após consentimento do dono da conta. Padrão `NAO` não abre conexão WhatsApp nem gera QR.

Não há mapeamento de `.codex`, `.claude`, home do Windows ou tokens de IA. No Node local, sessão WhatsApp/journal ficam em `dados/gateway-node`; no Docker opcional, ficam no volume `whatsapp_private`. Nunca publicar essas pastas.

## API (127.0.0.1:3210)

Todos os endpoints exceto `/health` requerem `Authorization: Bearer <GATEWAY_TOKEN>`. Não passar segredo na URL. Sem CORS. Não mudar o bind do Compose para `0.0.0.0` no host.

- `GET /health`: `{status,connected}`. Estado do processo; não comprova entrega nem que a IA está autenticada.
- `GET /events?after=0`: `{events:[{id,chat_id,text,timestamp,kind,cursor}],cursor}`. Timestamp Unix em segundos; cursor numérico. `kind`: `incoming` ou `human_takeover`. Buffer em memória até 1000 eventos/10 minutos; não reprocessa histórico após reinício. Perda de eventos é preferível a disparos antigos.
- `GET /qr`: `{status,qr,expires_in_ms}`; payload sensível, só após consentimento. Sem QR disponível: string vazia e prazo zero. Prazo restante é apenas a janela local, não garantia do WhatsApp.
- `GET /qr.svg`: SVG para abrir privadamente. Não projetar, imprimir em logs nem compartilhar a tela. A API deixa de fornecer o QR após no máximo 15 segundos e invalida em renovação, início/fim de transporte e confirmação de novo login. Revalida após renderizar SVG. **Uma imagem já salva/aberta não se autoapaga nem se atualiza:** não a entregue por chat nem a use como visualizador de aula. UI privada local com renovação e remoção automática ainda pendente; veja QR_DIAGNOSTICO_20261027.md na raiz.
- `POST /send`: JSON `{event_id,chat_id,text,idempotency_key}`. Chave idempotente URL-safe 16–128 caracteres; texto até 4000 caracteres. Retorna `{message_id,state:"sent"}` quando a biblioteca entrega recibo local de envio — não comprova leitura ou entrega no celular.

Somente um envio por entrada registrada, recente e autorizada. Journal é persistido **antes** do efeito externo. Falha ambígua retorna `uncertain_send_do_not_retry`; não reenviar automaticamente. Verifique manualmente o WhatsApp antes de qualquer ação. Não existe endpoint para campanhas, retomadas agendadas, leitura de contatos ou grupos. Media/anexos e identificadores `@lid` são ignorados por segurança; se a biblioteca fornecer apenas LID, a conversa não será atendida neste kit.

Mensagem manual de saída em chat autorizado gera `human_takeover`. O agente host deve pausar o chat até liberação explícita. IDs dos próprios envios são registrados antes de enviar para evitar esse falso positivo. A exceção de transporte é uma única reconexão `restartRequired` (515) após registro, usando credenciais persistidas, sem novo QR nem repetição de envio; isso completa o handshake de pareamento. Demais desconexões exigem inspeção e reinício manual — não há ciclo automático de novo pareamento.

## Fontes oficiais verificadas em 26/10/2026

- [Baileys, releases do projeto](https://github.com/WhiskeySockets/Baileys/releases): versão atual 7.0.0-rc14; release candidata, não chamada de estável.
- [Manifesto canônico da versão](https://raw.githubusercontent.com/WhiskeySockets/Baileys/v7.0.0-rc14/package.json): pacote `baileys`, ESM.
- [Exemplo oficial versionado](https://raw.githubusercontent.com/WhiskeySockets/Baileys/v7.0.0-rc14/Example/example.ts): `makeWASocket`, `useMultiFileAuthState`, `creds.update`, `messages.upsert`, `connection.update`, `generateMessageIDV2` e `sendMessage`.
- [QR Code, projeto oficial](https://github.com/soldair/node-qrcode): `qrcode` 1.5.4 e geração de SVG local.

`useMultiFileAuthState` é uma escolha didática de sessão local, não uma arquitetura de armazenamento de produção. As APIs acima foram conferidas na fonte; integração real continua pendente.

- [Enum oficial DisconnectReason](https://raw.githubusercontent.com/WhiskeySockets/Baileys/v7.0.0-rc14/src/Types/index.ts): `restartRequired = 515`; reconexão limitada testada como regra pura, handshake real não testado.

- [Release rc11, migração do libsignal para NPM](https://github.com/WhiskeySockets/Baileys/releases/tag/v7.0.0-rc11): manifesto rc14 não requer dependência Git para libsignal; não foi acrescentado instalador Git/apt sem necessidade.

## Preparação real posterior no Windows

Baileys7.0.0-rc14/qrcode1.5.4 instalados somente no projeto via npm canônico e --ignore-scripts;124 entradas de dependências no lock mais raiz,98 pacotes aplicáveis instalados. Imports reais passaram. Health consent_required/connected:false,QR409,send503,API não autenticada401,eventos vazios. Token apenas efêmero; processo encerrado; nenhuma sessão/configuração persistente. Isso não comprova conexão WhatsApp.

## Correção offline de QR e diagnóstico — 27/10/2026

A fonte [socket.ts da versão rc14](https://github.com/WhiskeySockets/Baileys/blob/v7.0.0-rc14/src/Socket/socket.ts) usa 60 s no primeiro QR e 20 s nos seguintes, salvo qrTimeout explícito (não configurado pelo kit). O limite anterior de 45 s podia expor QR subsequente expirado. O limite local conservador passou a 15 s, com relógio monotônico, sem renovação por evento duplicado. É uma correção de exposição local, não prova de validade no servidor nem explicação das desconexões anteriores.

Desconexões futuras registram somente horário, código numérico e classificações de lista fechada em DATA_DIR/last-disconnect.json. Erro bruto, stack, QR, sessão, número e mensagens não são registrados. Código408 isolado não distingue timeout de esgotamento de referências QR. Diagnóstico real anterior indisponível; causa não determinada. Não houve conexão real para validar esta instrumentação.

Testes adicionais: `node --test gateway/test*.mjs` e `python gateway/test_http_qr_mock.py` (módulos falsos locais). Execute os dois HTTP mocks separadamente: usam a mesma porta3210.
