# 02 — Rodar o projeto pelo Claude Code

Repositório correto: https://github.com/ibcappainstituto-arch/agente-whatsapp

Abra a pasta deste repositório no **Claude Code autenticado**. Não há aplicativo Windows para instalar, wizard obrigatório ou Docker obrigatório. O Claude Code conduz os processos Node/Python deste projeto. O WhatsApp continua dependendo do gateway Baileys real; não é uma integração nativa do Claude.

Cole na conversa do Claude Code, com a pasta do projeto aberta:

```text
Quero rodar este projeto aqui, pelo Claude Code: https://github.com/ibcappainstituto-arch/agente-whatsapp . Leia README.md e COMECE_NO_CLAUDE_CODE.md da pasta aberta. Use o código já implementado; não crie instalador de Windows, wizard nem Docker obrigatório. Faça você a preparação técnica e conduza os processos Node e Python do próprio projeto. Scripts PowerShell são suporte opcional, não o passo que devo executar.

Aproveite a pasta conhecimento_agente que já preparei com os seis Markdown. Localize-a comigo se o caminho não estiver claro. Preserve originais e decisões confirmadas; não peça para redigitar tudo em CSV. Use o importador do projeto para propor o catálogo rastreável, indique somente lacunas e peça minha revisão comercial antes de registrar aprovação. Nada PENDENTE vira preço, prazo, condição ou promessa.

Confira os executáveis Python, Node e Claude CLI já disponíveis. Ter o aplicativo aberto não prova login/cota do CLI. Teste o código local e confira autenticação por assinatura. Não use API paga nem fallback. Não instale programas no sistema nem altere PATH/política de execução. Se faltar uma dependência npm do projeto, explique quais pacotes e peça autorização específica antes de instalar somente em gateway. Não presuma autorização para criar ou gravar chave persistente/configuração: explique e peça essa autorização separadamente.

Leia também QR_DIAGNOSTICO_20261027.md: o visualizador privado local autoatualizado ainda é critério pendente. Não use imagem estática nem QR por chat para contornar esse limite. Pare na preparação offline enquanto esse critério não estiver implementado e validado. Nunca interprete testes mock como ensaio real concluído.

Somente após resolver esse critério e obter preparação e revisão autorizadas, conduza os processos do projeto: gateway Node e agente Python, usando apenas HTTP local 127.0.0.1:3210 e uma allowlist fechada de contato de teste consentido. Não exponha painel, token ou credenciais. Explique que Baileys é não oficial e que o código não é uma integração WhatsApp nativa do Claude Code.

Pareamento e envio têm autorizações próprias. Peça minha confirmação antes de abrir QR; mostre-o apenas na tela privada e eu faço a ação no celular. Antes de qualquer resposta real, confirme comigo o contato de teste e a autorização de envio. Sem mensagens iniciais, grupos, campanha, atendimento a todos ou retomadas automáticas.

Quando eu autorizar, acompanhe uma pergunta nova enviada pelo outro telefone: entrada no gateway, geração real pelo Claude e resposta aparecendo naquele telefone. Faça segunda troca para verificar contexto. Mock, QR conectado e log não comprovam entrega. Se faltar cota, dependência, login ou surgir erro, informe o bloqueio real; não diga que validou WhatsApp.

Ao terminar, informe resultados e pendências e pare os processos que você iniciou, salvo minha autorização para mantê-los nos mesmos contatos. Não publique conhecimento, configuração, chave, sessão, mensagens ou dados pessoais no GitHub. Não copie credenciais .claude/.codex para o projeto ou para containers.
```

Estado verificado: 43 testes Python passaram em Windows e em Linux; 28 testes Node e dois HTTP mocks passaram na revisão Linux atual; os novos testes de QR ainda não foram repetidos no Windows. Codex gerou resposta real por assinatura; Claude teve autenticação confirmada, mas geração Claude ainda não foi testada. Dependências reais Baileys/qrcode foram instaladas no projeto de validação com scripts desativados; imports passaram e health real permaneceu desconectado, sem QR/envio. Lockfile incluído para reprodução autorizada em outros computadores. Baileys conectado, QR e WhatsApp real continuam pendentes. Não confundir esses resultados com um piloto de WhatsApp concluído.

## Bloqueio de prontidão após o piloto

Antes de qualquer novo pareamento, leia QR_DIAGNOSTICO_20261027.md. O gateway foi corrigido offline para não fornecer QR localmente após15s/invalidação; isso não corrige nem comprova a conexão real. Não entregue QR por chat. Visualizador privado LOCAL com atualização por eventos e remoção na expiração/desconexão ainda precisa ser implementado/validado; os SVG estáticos dos launchers não atendem ao requisito. Pare na preparação offline até cumprir esse critério e obter autorização para ensaio ponta a ponta. Não anunciar o agente pronto nem iniciar nova demonstração automática.
