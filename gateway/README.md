# Gateway Baileys — componente de laboratório

O cérebro roda no Windows. O canal usa este gateway Baileys em Node local (recomendado no Windows) ou, opcionalmente, no container Docker. Não é WhatsApp Business Platform oficial. A biblioteca pode deixar de funcionar e a conta pode sofrer restrições. Use uma conta de laboratório e destinatários que consentiram. Não conecte o número principal em uma aula sem avaliar esse risco.

## Estado de validação

- Código de proteção testado com `node --test gateway/test_guard.mjs` sem dependências ou conta.
- Integração HTTP com Baileys substituído por mock local (`python gateway/test_http_mock.py`): handshake515 limitado, credenciais persistidas antes de reconectar, idempotência, bloqueio de resposta incerta e journal. Não valida a biblioteca real nem WhatsApp.
- Sintaxe de `server.mjs` conferida por `node --check`.
- Smoke HTTP local sem consentimento: saúde desconectada, API sem token recusada, buffer vazio, QR indisponível e envio recusado; nenhuma sessão criada nem dependência Baileys importada.
- Não instalamos dependências, não construímos a imagem, não executamos Docker, não pareamos uma conta nem enviamos WhatsApp real neste ambiente.
- Dependências diretas fixadas; árvore transitiva ainda não congelada em lockfile. O primeiro build autorizado precisa resolver dependências, ser revisado e validado localmente. Não anunciar esse kit como produção validada.

## Configuração (arquivo `.env` da raiz)

- `GATEWAY_TOKEN`: segredo aleatório URL-safe de pelo menos 32 caracteres, igual no agente Windows; não é chave API paga.
- `ALLOWED_NUMBERS`: números E164 explícitos separados por vírgula. Exemplo estrutural: `+<país><DDD><número>` (não copie os colchetes). Vazio = ninguém. Nunca `*`.
- `WHATSAPP_PAIRING_CONSENT=SIM`: somente após consentimento do dono da conta. Padrão `NAO` não abre conexão WhatsApp nem gera QR.

Não há mapeamento de `.codex`, `.claude`, home do Windows ou tokens de IA. No Node local, sessão WhatsApp/journal ficam em `dados/gateway-node`; no Docker opcional, ficam no volume `whatsapp_private`. Nunca publicar essas pastas.

## API (127.0.0.1:3210)

Todos os endpoints exceto `/health` requerem `Authorization: Bearer <GATEWAY_TOKEN>`. Não passar segredo na URL. Sem CORS. Não mudar o bind do Compose para `0.0.0.0` no host.

- `GET /health`: `{status,connected}`. Estado do processo; não comprova entrega nem que a IA está autenticada.
- `GET /events?after=0`: `{events:[{id,chat_id,text,timestamp,kind,cursor}],cursor}`. Timestamp Unix em segundos; cursor numérico. `kind`: `incoming` ou `human_takeover`. Buffer em memória até 1000 eventos/10 minutos; não reprocessa histórico após reinício. Perda de eventos é preferível a disparos antigos.
- `GET /qr`: `{status,qr}`; payload de pareamento sensível, só após consentimento.
- `GET /qr.svg`: SVG para abrir privadamente. Não projetar, imprimir em logs nem compartilhar a tela. Expira em até 45 segundos; gerar novo arquivo quando necessário. Apague arquivos locais após parear.
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
