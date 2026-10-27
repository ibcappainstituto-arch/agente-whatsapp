# Correção offline de QR e observabilidade — 27/10/2026

## Resultado e limite

Corrigido um defeito concreto de exposição local de QR. **Não foi determinada a causa das desconexões anteriores e não foi validado pareamento nem conversa WhatsApp ponta a ponta.** Nenhuma conexão/login/QR/envio real foi iniciado para desenvolver ou testar esta correção.

O piloto anterior foi encerrado pelo executor Windows, sem listener na porta3210, registro/conexão confirmados ou envio habilitado. A sessão foi preservada com `registered:false`; não se deve apagar/recriar sessão para tentar contornar esse estado. Nenhuma mensagem foi enviada; QR não foi entregue pelo chat nessa etapa. Esses são registros do encerramento, não uma verificação contínua da máquina.

## Fonte primária e defeito

Na [fonte Baileys v7.0.0-rc14, socket.ts](https://github.com/WhiskeySockets/Baileys/blob/v7.0.0-rc14/src/Socket/socket.ts), `genPairQR` usa por padrão60 segundos no primeiro QR e20 segundos nos seguintes. A opção `qrTimeout` altera esses períodos; o kit não a configura. O evento de pareamento emite `isNewLogin:true` com `qr:undefined`.

A API do kit aceitava cada QR por45 segundos e ignorava a limpeza explícita `qr:undefined`. Assim podia expor QR subsequente expirado. Essa constatação não explica uma desconexão ocorrida antes de obter QR nem prova a validade do QR no servidor.

## Alterações

- Janela local máxima de **15 segundos**, conservadora para todos os QR, medida com relógio monotônico. Pode haver intervalo sem QR até o próximo evento; não é erro a corrigir prolongando um QR antigo.
- Renovação substitui o snapshot anterior. Evento duplicado não estende prazo nem ressuscita QR expirado/inválido.
- Limpeza em `qr:undefined`, vazio/nulo, `isNewLogin`, conexão iniciando/aberta/fechada, encerramento e falha de armazenamento. Após novo login, abertura ou fechamento, um bloqueio persistente por transporte rejeita também os próximos QR do timer antigo; só um novo transporte reinicia esse estado. Eventos tardios do transporte já fechado são ignorados.
- `/qr` informa `expires_in_ms` (zero sem QR). O prazo é local, não garantia de aceitação pelo WhatsApp. `/qr.svg` retorna409 quando indisponível e revalida após a geração assíncrona; não devolve SVG que ficou obsoleto durante a renderização.
- Auth Bearer, proibição de origem de navegador e `Cache-Control:no-store` preservados. Nenhum token em URL, porta externa ou endpoint de QR público foi acrescentado.
- Desconexões futuras produzem metadados sanitizados: horário, código numérico, classe conhecida de erro/mensagem e indicadores booleanos. Sem erro bruto, stack, sessão, número, QR ou mensagens. Arquivo privado `DATA_DIR/last-disconnect.json`; não publicar.
- Código408 isolado é ambíguo. Somente a classe explícita sanitizada pode distinguir referências QR esgotadas de outros erros; os logs antigos não permitem recuperar essa causa.

## Testes executados nesta revisão

- Linux:43 testes Python;28 testes Node (17 regras existentes, 3 diagnóstico e 8 ciclo QR); compilação Python/sintaxe Node.
- HTTP mock existente: reinício515 limitado, idempotência e envio incerto sem repetição.
- Novo HTTP mock: autenticação, no-store, renovação/limpeza/novo login, invalidação no meio da renderização por rotação/abertura/fechamento, evento tardio ignorado e diagnóstico sem conteúdo privado.
- O patch de observabilidade de origem passou20 testes Node e HTTP mock no Windows. **Os testes novos do ciclo QR e o build Docker não foram executados no Windows/Docker.**

Mocks usam módulos falsos escritos localmente e textos sintéticos, não geram QR de pareamento real, não instalam npm e não acessam WhatsApp. As duas integrações HTTP devem rodar sequencialmente, pois usam a mesma porta3210.

## Interface posterior e regra de prontidão

**Uma imagem estática já salva/aberta não pode ser invalidada pela API.** Pode vencer antes de chegar pelo chat, e o navegador pode continuar mostrando o arquivo antigo. Os launchers anteriores reabriam SVG a cada35 segundos e não constituíam um visualizador confiável para aula. A revisão posterior removeu esse percurso estático.

O visualizador **privado no próprio computador** foi implementado posteriormente em qr_viewer.py, com versão/polling, prazo local e retirada do quadro ao expirar ou observar desconexão/falha. Tk real oculto passou posteriormente no Windows; layout visível ainda precisa de validação antes de ensaio real. Sem token em query/log, compartilhamento de tela, transporte do QR por chat ou bind externo. Veja VISUALIZADOR_QR_PRIVADO.md: a integração foi testada offline, não comprova a GUI real nem pareamento.

Prontidão operacional exige ainda fonte comercial explicitamente aprovada, geração pelo fluxo efetivo no app, pareamento e duas trocas com contato de teste consentido, com resposta vista no segundo telefone. Cada etapa real requer autorização e horário combinado. Importação npm, health local, QR disponível, autenticação e mocks não substituem esse teste. Até lá: preparação offline e diagnóstico, não operação/aula autônoma.

## Ressalva LID — hipótese, sem mudança de privacidade

A mesma fonte primária rc14 alerta que bloquear todas as sincronizações por `shouldSyncHistoryMessage` impede mapas LID iniciais e pode causar instabilidade de sessão. O kit mantém esse bloqueio e ignora contatos exclusivamente LID para não coletar histórico privado. **O aviso não prova a causa do piloto.** Nenhuma coleta de conversas foi ampliada. Uma eventual investigação de mapeamento mínimo, sem sincronizar conteúdos privados, deve ser revisada separadamente; não ativar histórico para tentar corrigir conexão silenciosamente.
