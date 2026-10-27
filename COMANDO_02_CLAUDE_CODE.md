# 02 — Rodar o projeto pelo Claude Code

Repositório correto: https://github.com/ibcappainstituto-arch/agente-whatsapp

Abra a pasta deste repositório no **Claude Code autenticado**. Não há aplicativo Windows para instalar, wizard obrigatório ou Docker obrigatório. O Claude Code conduz os processos Node/Python deste projeto. O WhatsApp continua dependendo do gateway Baileys real; não é uma integração nativa do Claude.

Cole na conversa do Claude Code, com a pasta do projeto aberta:

```text
Quero rodar este projeto aqui, pelo Claude Code: https://github.com/ibcappainstituto-arch/agente-whatsapp . Leia README.md e COMECE_NO_CLAUDE_CODE.md da pasta aberta. Use o código já implementado; não crie instalador de Windows, wizard nem Docker obrigatório. Faça você a preparação técnica e conduza os processos Node e Python do próprio projeto. Scripts PowerShell são suporte opcional, não o passo que devo executar.

Aproveite a pasta conhecimento_agente que já preparei com os seis Markdown. Localize-a comigo se o caminho não estiver claro. Preserve originais e decisões confirmadas; não peça para redigitar tudo em CSV. Use o importador do projeto para propor o catálogo rastreável, indique somente lacunas e peça minha revisão comercial antes de registrar aprovação. Nada PENDENTE vira preço, prazo, condição ou promessa.

Confira os executáveis Python, Node e Claude CLI já disponíveis. Ter o aplicativo aberto não prova login/cota do CLI. Teste o código local e confira autenticação por assinatura. Não use API paga nem fallback. Preserve CLAUDECODE e CLAUDE_CODE_ENTRYPOINT; nunca remova marcadores para contornar proteção de sessão aninhada. A geração Claude real já aprovada ocorreu fora do terminal interno do Claude Code; não a apresente como prova desse fluxo aninhado. Não instale programas no sistema nem altere PATH/política de execução. Se faltar uma dependência npm do projeto, explique quais pacotes e peça autorização específica antes de instalar somente em gateway. Não presuma autorização para criar ou gravar chave persistente/configuração: explique e peça essa autorização separadamente.

Leia QR_DIAGNOSTICO_20261027.md e VISUALIZADOR_QR_PRIVADO.md. Use o visualizador já implementado, não imagem estática nem QR por chat. Antes de qualquer gateway real, valide a janela local com conteúdo sintético; GUI Windows e terminal interno do app ainda não foram comprovados. Nunca interprete testes mock ou simulação de marcadores como ensaio real no app concluído.

Somente após validar a interface local e combinar ensaio real, com preparação e revisão autorizadas, conduza os processos do projeto: gateway Node e agente Python, usando apenas HTTP local 127.0.0.1:3210 e uma allowlist fechada de contato de teste consentido. Não exponha painel, token ou credenciais. Explique que Baileys é não oficial e que o código não é uma integração WhatsApp nativa do Claude Code.

Pareamento e envio têm autorizações próprias. Peça minha confirmação antes de abrir QR; mostre-o apenas na tela privada e eu faço a ação no celular. Antes de qualquer resposta real, confirme comigo o contato de teste e a autorização de envio. Sem mensagens iniciais, grupos, campanha, atendimento a todos ou retomadas automáticas.

Quando eu autorizar, acompanhe uma pergunta nova enviada pelo outro telefone: entrada no gateway, geração real pelo Claude e resposta aparecendo naquele telefone. Faça segunda troca para verificar contexto. Mock, QR conectado e log não comprovam entrega. Se faltar cota, dependência, login ou surgir erro, informe o bloqueio real; não diga que validou WhatsApp.

Ao terminar, informe resultados e pendências e pare os processos que você iniciou, salvo minha autorização para mantê-los nos mesmos contatos. Não publique conhecimento, configuração, chave, sessão, mensagens ou dados pessoais no GitHub. Não copie credenciais .claude/.codex para o projeto ou para containers.
```

Estado verificado: 44 testes Python de base/CLI passaram no Windows. Na revisão Linux atual, 79 testes Python e 36 Node passaram; incluem HTTP frame mock, e dois HTTP mocks independentes também passaram. Os testes novos de UI/QR e os launchers alterados ainda não foram repetidos no Windows. Codex gerou resposta real por assinatura; Claude também gerou resposta sintética real no Windows a partir de terminal externo; chamada aninhada pelo terminal interno do Claude Code continua não testada. Dependências reais Baileys/qrcode foram instaladas no projeto de validação com scripts desativados; imports passaram e health real permaneceu desconectado, sem QR/envio. Lockfile incluído para reprodução autorizada em outros computadores. Baileys conectado, QR e WhatsApp real continuam pendentes. Não confundir esses resultados com um piloto de WhatsApp concluído.

## Prontidão após a correção offline

O visualizador privado local foi implementado em `qr_viewer.py`, com PNG somente em memória, prazo local visível e retirada ao expirar, perder foco ou observar desconexão. Leia [VISUALIZADOR_QR_PRIVADO.md](VISUALIZADOR_QR_PRIVADO.md). Não transportar QR por chat nem usar SVG estático. Os launchers opcionais agora usam esse visualizador, sem salvar imagem.

Os testes de lógica/controlador/HTTP são offline; **GUI/Tk/ACL no Windows e os launchers alterados ainda precisam de validação local**. Claude gerou respostas reais externas, inclusive com marcadores de contexto simulados preservados; terminal interno do app continua não testado. Antes de novo piloto, validar a interface com conteúdo sintético e combinar ensaio real autorizado. Só considerar pronto depois de fonte aprovada, pareamento e duas trocas com resposta vista no segundo telefone. Não anunciar aula autônoma/E2E concluído.
