# Comece no Claude Code — sem instalador Windows

Abra esta pasta no Claude Code e use [COMANDO_02_CLAUDE_CODE.md](COMANDO_02_CLAUDE_CODE.md). O assistente conduz o trabalho nos arquivos e terminais do projeto. Não há wizard obrigatório, instalação de aplicativo Windows nem necessidade de Docker.

## O que realmente roda

**WhatsApp ⇄ gateway Baileys/Node local ⇄ HTTP 127.0.0.1:3210 ⇄ agente Python ⇄ CLI Claude autenticado por assinatura.**

Claude Code ajuda a preparar e conduzir esses processos; isso **não** transforma WhatsApp em integração nativa do produto. Como alternativa de motor, o código também suporta Codex por assinatura. Para este percurso principal, use Claude.

## Preparação conduzida pelo assistente

1. Inspecione esta pasta, `gateway/package.json`, `agente.py` e `cli_adapter.py`. Preserve instalações/conhecimento existentes.
2. Confira Python >=3.10, Node >=22 e Claude CLI nativo existentes. Não instale software de sistema, altere política ou PATH silenciosamente.
3. Rode testes offline (`python -m unittest discover -s tests -v`; `node --test gateway/test*.mjs`). Use o executável Python funcional; não pressuponha que `py -3` funciona.
4. Confira autenticação por assinatura pelo adaptador. Não leia/copíe arquivos de credenciais. A presença do app aberto não basta. Uma geração real Claude foi aprovada somente em terminal externo; a execução aninhada pelo terminal interno do Claude Code ainda precisa ser verificada. Preserve CLAUDECODE/CLAUDE_CODE_ENTRYPOINT e não contorne bloqueio do fornecedor.
5. Pacotes diretos do gateway: `baileys@7.0.0-rc14` e `qrcode@1.5.4`. Se ausentes, peça autorização específica para instalar dependências **somente no projeto**, usando o `gateway/package-lock.json` já fornecido e scripts de instalação desativados. Revise a árvore/scripts; não regenere o lock por conta própria. Nenhum script deste kit executa npm silenciosamente. A árvore foi instalada e os módulos importados no Windows de validação; isso não valida Baileys conectado.
6. Use os seis Markdown de `conhecimento_agente`, já produzidos no comando01. A conversão pelo CLI gera proposta com citações; não aprova automaticamente. Leia somente a pasta autorizada. Peça revisão de lacunas/associação de preço e serviço.
7. Antes de `agente.py preparar`, peça autorização específica para gravar configuração e chave local persistente. A autorização de usar Claude Code ou instalar dependências não implica esse consentimento. Não imprima a chave. Só depois, prepare configuração, importe/revise a fonte e registre aprovação comercial explícita conforme comandos do projeto.

## Condução dos processos — só depois dos consentimentos

- O gateway inicia com `node server.mjs` na pasta `gateway`, com `DATA_DIR` absoluto privado, `GATEWAY_BIND_HOST=127.0.0.1`, token local e allowlist explícita configurados no ambiente do processo. Não passe segredo na linha de comando nem o exponha em logs.
- Sem `WHATSAPP_PAIRING_CONSENT=SIM`, não conectar WhatsApp. Só preencher após autorização de pareamento, mantendo o QR privado.
- O agente inicia com `python agente.py iniciar` na raiz, somente com fonte aprovada, login validado e autorização explícita de envio na configuração. Não habilitar envio antes de o usuário confirmar o destinatário de teste.
- O fluxo de supervisão em `INICIAR_NODE.ps1` foi atualizado para abrir `qr_viewer.py`, sem SVG em disco. O próprio assistente pode conduzir os processos; não é tarefa manual obrigatória do aluno. A revisão atual desse launcher ainda requer parsing/runtime Windows e GUI local antes de novo piloto. Ele é **suporte opcional**, não tarefa obrigatória do aluno. Não fazer bypass de política para usá-lo. Se conduzir os processos diretamente, preserve todas as mesmas confirmações e o encerramento seguro.
- Depois do teste, desligue os processos iniciados, volte consentimentos para desligado e remova o arquivo QR; preserve journal/sessão para não repetir envios incertos. Não mate processos alheios nem reutilize porta ocupada.

Validação real exige verificar a resposta no segundo telefone após geração real pelo Claude. Até lá, afirmar somente as etapas comprovadas.

## Documentação de suporte

- [Fonte comercial e requisitos do ambiente](INSTALAR_WINDOWS.md): referência técnica, não exigência de instalar aplicativo Windows.
- [Gateway Node e verificações](NODE_NATIVO_WINDOWS.md).
- [Evidências/limites](VALIDACAO.md).
- `INICIAR.ps1`/`compose.yaml`: opção Docker, fora do caminho principal. Não usar sem escolha explícita.

## Reproduzir as dependências — somente após autorização

O assistente pode executar, dentro de `gateway`, após autorização específica:

```text
npm ci --ignore-scripts --registry=https://registry.npmjs.org --fetch-retries=0 --fetch-timeout=20000 --no-audit --no-fund
```

Não adicionar `--global`, não habilitar scripts de lifecycle nem trocar de registry se falhar. O lockfile v3 contém124 entradas de dependências mais a raiz; no Windows de validação foram instalados98 pacotes aplicáveis à plataforma. Nenhum lifecycle foi executado. Essa autorização não cria chave persistente, configuração, QR ou envio.

## Prontidão após a correção offline

O visualizador privado local foi implementado em `qr_viewer.py`, com PNG somente em memória, prazo local visível e retirada ao expirar, perder foco ou observar desconexão. Leia [VISUALIZADOR_QR_PRIVADO.md](VISUALIZADOR_QR_PRIVADO.md). Não transportar QR por chat nem usar SVG estático. Os launchers opcionais agora usam esse visualizador, sem salvar imagem.

Os testes de lógica/controlador/HTTP são offline; **GUI/Tk/ACL no Windows e os launchers alterados ainda precisam de validação local**. Claude gerou respostas reais externas, inclusive com marcadores de contexto simulados preservados; terminal interno do app continua não testado. Antes de novo piloto, validar a interface com conteúdo sintético e combinar ensaio real autorizado. Só considerar pronto depois de fonte aprovada, pareamento e duas trocas com resposta vista no segundo telefone. Não anunciar aula autônoma/E2E concluído.
