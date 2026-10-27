# Referência técnica do ambiente Windows — suporte opcional

**Percurso principal: abrir a pasta no Claude Code e seguir COMECE_NO_CLAUDE_CODE.md.** Este arquivo não exige instalar um aplicativo Windows ou executar wizard. Scripts PowerShell são suporte opcional para o assistente, se a política existente permitir.

## Antes de começar

Este é um **kit novo, separado**. Não execute novamente `instalar.sh`, instalador do antigo OpenWA,
Docker Linux para o cérebro nem o `main` Zernio supondo que sejam esta versão. Preserve a instalação anterior.
Extraia o ZIP em uma pasta local, fora de OneDrive/Dropbox, por exemplo uma pasta privada de laboratório.
Não copie `.env`, números, sessões ou tokens da instalação antiga.

Arquitetura recomendada: **WhatsApp ⇄ Baileys/Node no Windows ⇄ HTTP 127.0.0.1:3210 ⇄ Python Windows ⇄ Claude Code/Codex Windows**. Docker é opcional, somente para quem escolher executar o gateway em container.
O token do gateway é um segredo local criado pelo kit, não uma chave de API comercial.
Os logins de IA ficam onde os CLIs oficiais os guardam. Nada monta essas credenciais no container.

Requisitos que o kit **não instala silenciosamente**:

- Windows com Python 3.10+ oficial funcional por `python` ou `py -3`. Os scripts detectam a opcao funcional, sem instalar nada.
- Recomendado: Node >=22 já instalado; dependências locais exatas `baileys@7.0.0-rc14` e `qrcode@1.5.4` após autorização específica. Consulte [NODE_NATIVO_WINDOWS.md](NODE_NATIVO_WINDOWS.md).
- Opcional: Docker Desktop oficial aberto em modo **Linux containers**, com Compose, se escolher esse caminho em vez de Node direto.
- **Um** CLI oficial atual: Codex autenticado com ChatGPT ou Claude Code nativo autenticado com Claude.ai.
- Conta de teste WhatsApp e um segundo número que consentiu em participar do teste.
- Assinatura compatível disponível e sem limite esgotado. Assinatura não equivale a uso ilimitado;
  configurações pré-existentes de uso extra/billing do fornecedor precisam ser conferidas pelo titular.

Fontes oficiais para requisitos: [Python Windows](https://www.python.org/downloads/windows/),
[Docker Desktop Windows](https://docs.docker.com/desktop/setup/install/windows-install/),
[Codex](https://developers.openai.com/codex/cli/), [Claude Code](https://code.claude.com/docs/en/setup).
Não há comando remoto `curl | shell`, `irm | iex` ou download de instalador legado neste kit.

## 1. Preparar sem conectar WhatsApp

Abra a pasta extraída no Claude Code ou Codex e peça para seguir este arquivo, inspecionar os scripts locais e conferir o CLI autenticado. Ter apenas o aplicativo aberto não prova que o CLI está no PATH nem que há login por assinatura.

Se a política atual do seu Windows permitir scripts locais, abra PowerShell **na pasta extraída** e execute:

```powershell
.\INSTALAR.ps1
```

Nenhum script deste kit altera a política de execução. Se o Windows bloquear scripts, **não altere nem contorne a política automaticamente**. Use os comandos Python de preparação abaixo ou peça orientação ao administrador. Qualquer mudança de política precisa de autorização específica do titular/administrador; ela não faz parte desta instalação.
Esse script é local e inspecionável. Antes de executá-lo, autorize a preparação local: ele roda testes offline e cria configuração/chave privada do gateway, pedindo o motor e somente números de teste consentidos.
**Não instala Docker, não inicia o gateway, não mostra QR e não envia WhatsApp.**

Ao pedir a pasta, informe o caminho da **`conhecimento_agente` que você já criou** com:

```
servicos.md
precos_e_condicoes.md
tom_de_voz.md
perguntas_frequentes.md
memorias_e_decisoes.md
LEIA_PRIMEIRO.md
```

O importador chama o CLI escolhido por assinatura, preserva a origem e copia os seis arquivos para
`fonte_comercial/originais`. Propõe um catálogo interno e mostra de onde retirou cada campo.
Não transforma estimativa em preço, não inventa contratação e não aprova a própria proposta.
Campos ausentes/inconsistentes geram `PENDENCIAS.md`; corrija só as lacunas na fonte, mantendo os demais arquivos.
Se houver tentativa anterior, preserve-a e use uma pasta de kit nova para reimportar: o importador recusa sobrescrita.

Alternativa explícita, sem script PowerShell (substitua os textos entre colchetes):

```powershell
python agente.py preparar --motor codex --nome "[SEU NOME]" --numeros "[DDI_DDD_NUMERO_DE_TESTE]"
python importar_conhecimento.py --pasta "C:\[CAMINHO]\conhecimento_agente" --motor codex --destino fonte_comercial
```

Os exemplos manuais usam `python`. Se somente `py -3` funcionar no seu Windows, use essa opção após conferir a versão; não instale nem altere PATH automaticamente.

Troque `codex` por `claude` se esse foi o motor escolhido. Não coloque chaves API nos arquivos.
O adaptador bloqueia variáveis `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` e configurações de provedores alternativos.
O Claude precisa ser o binário nativo; wrappers shell inseguros/CLIs antigos são recusados.

## 2. Revisar a proposta comercial

Leia `fonte_comercial/REVISAO.md` e `servicos.csv` comparando com os trechos dos seus Markdown.
O CSV é **representação interna gerada**, não uma tarefa de redigitar seu conhecimento.
Confira sobretudo serviço, entrega, prazo, preço total e contratação, inclusive o vínculo entre cada preço e serviço.
Valores parcelados só podem constar como condição literal aprovada; nenhum cálculo livre de desconto é feito.
Quando as pendências estiverem resolvidas, calcule o hash:

```powershell
python agente.py hash-fonte
```

Depois de revisar, use o hash exibido — **não aprove automaticamente sem ler**:

```powershell
python agente.py aprovar-fonte --sha256 [HASH_REVISADO]
python agente.py verificar
```

Essa aprovação não autoriza pareamento nem envio. Qualquer mudança posterior no catálogo ou nos Markdown copiados
bloqueia o agente até nova revisão. O original `conhecimento_agente` não é alterado pelo kit.

## 3. Parear privadamente e liberar um teste supervisionado — Node recomendado

Execute o script abaixo somente se a política atual do Windows permitir. Se bloqueado, pare e obtenha orientação/autorização específica; o assistente não deve ativar bypass por conta própria.

```powershell
.\INICIAR_NODE.ps1
```

1. O script verifica Node, dependências locais exatas, porta livre, fonte e login por assinatura; exibe a lista fechada de números. Não roda npm nem instala nada.
2. Só a palavra **PAREAR** autoriza iniciar o gateway e conectar a conta de teste. Se as dependências estiverem ausentes, pare e obtenha autorização específica para instalá-las; não use instalação silenciosa.
3. O QR é aberto em arquivo SVG privado. **Pare o compartilhamento de tela antes.** No WhatsApp,
   use Aparelhos conectados e escaneie no seu próprio computador. Não envie QR por chat, slide ou grupo.
4. Após a conexão, só a palavra **ENVIAR** libera respostas a novas entradas dessa allowlist durante a sessão.
5. Envie do segundo número uma mensagem de teste **depois** de aparecer “Agente ligado”. Histórico anterior é descartado.
6. Confira manualmente os dois celulares. Recibo do gateway não é prova de entrega ou leitura.
7. Ctrl+C encerra o agente; o script retira autorização de envio, para o gateway e remove o arquivo QR.

O pareamento e o uso extra do plano pertencem ao titular da conta. Não conecte número principal de trabalho sem avaliar risco.
No caminho Node, a sessão e o journal permanecem em `dados/gateway-node`; para revogar, desconecte o dispositivo no próprio WhatsApp. Não apague essa pasta sem decidir conscientemente perder sessão e journal.

### Docker opcional

Se você escolher Docker e ele já estiver pronto, use `.\INICIAR.ps1` em vez do launcher Node. Ele verifica Docker/Compose e a confirmação PAREAR autoriza build do gateway, que baixa imagem e dependências. Não use os dois launchers juntos. `docker compose down` preserva a sessão no volume privado; não use `down -v` sem decidir apagar sessão/journal. O caminho Docker continua não validado neste ambiente.

## 4. Roteiro mínimo do primeiro teste real — ainda pendente

- Um contato da allowlist envia uma mensagem nova; deve receber uma resposta identificada como assistente virtual.
- Um número fora da lista não recebe resposta; grupos também não.
- “Não quero mais mensagens” pausa o chat sem nova tentativa.
- Pedido de humano e resposta manual do titular pausam o agente naquele chat.
- Leia o preço retornado e compare com a fonte comercial aprovada.
- Interrompa uma operação somente em ambiente de teste. Envio de resultado incerto nunca é repetido automaticamente.

Anote versão Windows/Python/Docker/CLI, motor, momento, cenário e resultado — sem número completo, QR ou conteúdo de cliente.
Até esse teste terminar, diga **“implementado e testado offline”**, nunca “WhatsApp validado”.

## Diagnóstico sem exposição de dados

- Limite Codex/Claude: pare, aguarde a liberação ou escolha outro CLI já autorizado e autenticado; não há fallback para API.
- `startup_error`: dependências/build/conexão precisam de revisão. Não trate como conexão bem-sucedida.
- `disconnected`: uma reconexão de transporte após registro pode ocorrer para completar o pareamento;
  demais quedas exigem inspeção e reinício manual. Não repetir mensagens de resultado incerto.
- `@lid`: este kit conservador ignora identificadores sem número verificável; não amplie a allowlist para “todos”.
- Conversa pausada: consulte `dados/agente.sqlite3` localmente; não existe comando de retomada automática neste escopo.
- Sintaxe dos três scripts e detector Python foram verificados em Windows real. PowerShell 5.1 bloqueou os scripts por política; ela não foi alterada. A execução completa de preparação/pareamento não foi feita. Não execute como administrador nem ative bypass para “resolver” falha desconhecida.

Dados privados: `.env`, `config.local.json`, `dados/`, `fonte_comercial/` preenchida e volume Docker, se utilizado.
Não publique esses itens em GitHub, ZIP compartilhado ou tela de aula.


O detector Claude aceita o executavel nativo existente na instalacao npm oficial quando o PATH retorna apenas wrapper. Nao executa o wrapper e nao altera PATH persistentemente.
