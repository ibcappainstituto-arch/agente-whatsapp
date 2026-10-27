# Validacao Windows e correcao de launchers — 27/10/2026
Base 8b6a36c39435b65b6443d240d7f42edd6885a27a, ibcappainstituto-arch/agente-whatsapp.
Copia isolada validacao-kit-windows-20261027. Sem alteracao dos repos antigos.
Windows 10.0.26200.0; Python 3.13.13. py -3 falha com No installed Python found!.
Corrigidos INSTALAR.ps1/INICIAR.ps1 para helper PYTHON_WINDOWS.ps1 selecionar executavel Python funcional. Sem instalacao, PATH persistente ou mudanca de politica. Helper testado com python real.
Corrigido cli_adapter.py para localizar Claude nativo npm existente a partir do wrapper; wrapper continua recusado sem executavel. Claude 2.1.311 e Codex autenticados por assinatura, sem copiar credenciais. Geração Claude nao testada.
43 testes offline passaram via helper; sintaxe dos tres PS1 passou; git diff --check passou.
Codex real no adaptador publicado retornou status ok_sintetico e exit 0 nesta sessao. Nao e prova de WhatsApp.
Docker Desktop instalado foi aberto com autorizacao; processos Desktop e backend confirmados. No ultimo probe daemon Linux ainda indisponivel (pipe dockerDesktopLinuxEngine nao encontrado). Nao houve build, download de dependencias, QR ou envio.
Windows PowerShell 5.1 bloqueou dot-source por politica (PSSecurityException/UnauthorizedAccess). Nao foi alterada nem contornada. PowerShell do executor executou helper normalmente. Esse bloqueio precisa de orientacao/autorizacao especifica antes de usar PS1 no shell bloqueado; comandos Python de checagem continuam disponiveis.
Nao executado agente.py preparar nem importador real: nao foram criados .env, config.local.json, segredo de gateway ou aprovacao de fonte. Conhecimento do usuario nao foi lido ou refeito.
Este relatorio registra o teste local anterior a publicacao do patch. A publicacao e conferida separadamente na branch main. Nenhum QR ou envio foi autorizado/executado neste teste.
