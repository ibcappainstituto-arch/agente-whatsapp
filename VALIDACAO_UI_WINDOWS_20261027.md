# Validação Windows isolada da UI — 27/10/2026

Código testado: commit QA `bdd4d1a7b997b480cb038c23a107c9287c1a3c74`, 58 arquivos (57 hashes mais manifesto).

- Windows10.0.26200.0; Python3.13.13; Tcl/Tk8.6.15.
- Parsing **4/4 scripts** aprovado tanto em PowerShell7.6.5 quanto em Windows PowerShell5.1.26100.9711. Apenas parser: os launchers não foram executados em operação.
- `python tests/smoke_viewer_tk.py`: **PASS, exit0, 1378ms**. Tk real com janela **withdrawn/oculta**, PNG branco1×1 sintético; PhotoImage/decodificação real, clear, expiração, pause/resume, estado desconectado, worker tardio e close aprovados.
- Suíte Python:78 testes incluídos,77 passaram e1 skip POSIX. O teste HTTP que inicia Node foi excluído desta etapa para respeitar a restrição de não iniciar gateway/rede; não houve falha ocultada como passe.
- Nenhuma configuração privada, QR real, conexão WhatsApp, autenticação ou envio. Porta3210 permaneceu fechada.

**Não valida:** layout visível, leitura pelo celular, ACL Windows, execução operacional dos launchers, terminal interno do Claude Code ou atendimento ponta a ponta. Gerações Claude externas e contexto simulado são evidências separadas em VALIDACAO_CLAUDE_20261027.md.

## Bytes e Git no Windows

O checkout inicial com autocrlf divergiu do manifesto por finais de linha. Na validação QA, conteúdo foi conferido em LF contra Git, sem mudança semântica. A entrega posterior inclui `.gitattributes` com `* -text`: preserva os bytes registrados no repositório (inclusive arquivos que já eram CRLF) e não modifica a configuração global do Git.

Regra conferida em repositório temporário com `core.autocrlf=true`, comparando bytes LF e CRLF depois do checkout. O manifesto continua comparando **bytes exatos**, não escondendo divergências por normalização. Em clone antigo já convertido, preserve alterações próprias e prefira nova pasta/ZIP da mesma revisão; não use reset/descarte para “corrigir” hashes automaticamente.
