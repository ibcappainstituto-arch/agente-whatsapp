# 02 — Usar o kit Windows implementado, depois de revisar o conhecimento

Repositório correto: https://github.com/ibcappainstituto-arch/agente-whatsapp

Baixe o código desse repositório em uma pasta nova ou clone com Git. Abra essa pasta no Claude Code ou Codex.
O kit já contém agente Python, adaptadores CLI e gateway Baileys; **não é pedido para implementar do zero**.
Não use o repositório antigo, o commit OpenWA antigo, Zernio ou instalador Linux.
Aplicativo aberto não prova que o CLI está instalado, autenticado por assinatura e com cota disponível.

Cole no assistente com a pasta do novo repositório aberta:

```text
Quero preparar o kit deste repositório no meu Windows: https://github.com/ibcappainstituto-arch/agente-whatsapp . Leia README.md e INSTALAR_WINDOWS.md da pasta que abri. Use o código implementado nesta pasta; não refaça o agente do zero nem use outro repositório. Preserve qualquer instalação anterior.

Primeiro localize comigo a pasta conhecimento_agente já criada pelo COMANDO_01_SALVAR_CONHECIMENTO.md e confira os seis Markdown. Se eu ainda não os revisei, aguarde minha revisão. Não peça para redigitar tudo em CSV: use importar_conhecimento.py para gerar a proposta rastreável, preservando os originais. Dados PENDENTES ou conflitantes não viram preço, prazo ou promessa. Mostre a proposta e peça aprovação comercial explícita antes de registrar o SHA.

Confira Python, Docker Desktop Linux containers, Compose e qual motor escolho: Claude Code nativo ou Codex. Verifique o CLI no PATH e a autenticação por assinatura, não apenas o aplicativo aberto. Execute os testes locais e siga o procedimento de preparação do INSTALAR_WINDOWS.md. Não instale programas, não altere a política PowerShell e não ative bypass sem autorização específica. Se scripts forem bloqueados, use a preparação Python documentada ou pare para orientação. Não copie .claude, .codex, tokens ou sessões para Docker. Não use API paga nem fallback para outro fornecedor.

O gateway deve ficar somente em 127.0.0.1:3210, com allowlist fechada de um contato de teste que consentiu. Explique riscos do WhatsApp não oficial. Pareamento exige minha confirmação e ação no celular; abra QR somente na minha tela privada, fora de gravação. Envios exigem minha segunda confirmação. Nunca abra atendimento a todos, nunca mande mensagem inicial, nunca faça campanha ou retomada automática.

Só depois dessas autorizações, siga INICIAR.ps1 e acompanhe um teste real: receba uma pergunta nova do outro telefone, gere a resposta com o CLI real e confira que ela apareceu no WhatsApp desse telefone. Faça uma segunda troca para verificar contexto. Teste recusa e pedido de humano. QR conectado, logs e mocks não bastam para validar canal real. Se faltar cota/login ou alguma etapa falhar, mostre o bloqueio verdadeiro e não diga que funcionou.

Ao terminar, informe o que foi de fato verificado, o que falta e como parar; encerre o piloto salvo minha autorização para mantê-lo ativo nos mesmos contatos. Preserve conhecimento, credenciais e dados localmente; não os publique no GitHub. Não prometa resultado judicial ou condição comercial fora da fonte aprovada.
```

Estado em 27/10/2026: 43 testes Python passaram no Windows, Codex por assinatura gerou resposta real e Claude teve autenticação confirmada (geração Claude não testada). Também passaram 43 testes Python, 17 Node e integração HTTP mockada no workspace Linux. PowerShell 5.1 bloqueou scripts por política, sem bypass; daemon Docker permaneceu indisponível. Preparação completa, build, QR e WhatsApp real ainda não validados. Cada aluno precisa verificar seu próprio ambiente.
