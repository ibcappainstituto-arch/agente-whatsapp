# Evidências e limites — 27/10/2026

## Estado atual

**Implementado e testado offline; não homologado para operação/aula autônoma.** A causa das desconexões do piloto não foi identificada. Correções de QR/observabilidade e visualizador não provam pareamento nem entrega.

## Revisão atual no workspace Linux

- **79 testes Python:**44 da base/CLI,33 do visualizador/controlador/HTTP frame mock e2 contratos estáticos de launchers.
- **36 testes Node:**17 regras do gateway,3 diagnóstico,8 ciclo QR e8 quadro privado.
- Dois HTTP mocks independentes: idempotência/reinício515/resultado incerto; expiração/invalidação/corridas de renderização QR.
- Compilação Python e sintaxe Node verificadas. Saídas em `TESTES-EXECUTADOS.txt` e `gateway/TESTES-EXECUTADOS.txt`.
- Módulos Baileys/qrcode falsos escritos localmente, entradas sintéticas e PNG branco1×1, não QR de conta. Nenhuma instalação npm, modelo real, gateway WhatsApp real, login, pareamento ou envio nesta revisão.
- Tk9.0 importável, mas sem DISPLAY/Wayland. **Nenhuma janela real foi criada aqui.** Controlador com widgets falsos não valida desenho/decodificação no Tk Windows.
- PowerShell indisponível aqui: os launchers alterados receberam revisão textual e testes de contrato, **não parsing/runtime Windows**.

## Evidências reais anteriores no Windows

- Windows10.0.26200.0, Python3.13.13. `py -3` não encontrou instalação; `python` funcionou. Helper seleciona executável funcional sem instalar/alterar PATH.
- **44 testes Python de base/CLI passaram** após preservar `CLAUDECODE`/`CLAUDE_CODE_ENTRYPOINT`. Não remover marcadores para contornar proteção do fornecedor.
- Codex autenticado por assinatura gerou `ok_sintetico`, exit0.
- Claude nativo2.1.311 autenticado gerou `ok_sintetico`, exit0/success, em terminal externo. Outra geração externa, com marcadores de sessão simulados e preservados, retornou `ok_sintetico_aninhado`, exit0/success. **Terminal interno do aplicativo não testado.** Veja [VALIDACAO_CLAUDE_20261027.md](VALIDACAO_CLAUDE_20261027.md).
- Versões anteriores dos scripts tiveram sintaxe PowerShell conferida e helper executado. Windows PowerShell5.1 bloqueou dot-source por política; não foi alterada/contornada. Isso não valida os launchers modificados posteriormente para o visualizador.
- Node24.15.0/npm11.17.0 existentes. Baileys7.0.0-rc14/qrcode1.5.4 instalados somente no projeto por npm canônico com `--ignore-scripts`;124 entradas de dependências no lock mais raiz;98 pacotes aplicáveis ao Windows. Nenhum lifecycle executado.
- Lock SHA256 `9cc312f9812aae819ce9c61cd2265c2fd594e52defdd39e65163953f0bbf0fed`. Imports reais passaram sem conexão. Preparação: health `consent_required/connected:false`, QR409,send503,API sem token401,eventos vazios; token efêmero e processo encerrado.
- Patch de observabilidade anterior passou20Node eHTTPmock no Windows. Novos testes de ciclo QR, quadro e GUI ainda não repetidos ali.
- Docker CLI29.8/Compose5.5 existentes, desktop/backend abertos com autorização; daemon Linux indisponível no último probe, pipe ausente. **Imagem/build Docker não executados.** COPY atualizado por revisão para incluir módulos novos.

## Encerramento do piloto e correções

O executor relatou encerramento do processo piloto, sem listener3210, sessão preservada com `registered:false/connected:false`, envio desabilitado e nenhuma mensagem enviada. QR não foi entregue no chat nessa etapa. Trata-se de registro do encerramento, não monitoramento contínuo da máquina. Não apagar sessão/repetir pareamento para tentar contornar esse resultado.

A fonte primária Baileysrc14 confirma primeiroQR60s/subsequentes20s. O limite local antigo45s podia expor QR vencido. Agora: limite conservador15s, relógio monotônico, invalidação e latch pós-pareamento, revalidação após renderização. Diagnóstico sanitizado futuro não recupera a causa anterior. Detalhes: [QR_DIAGNOSTICO_20261027.md](QR_DIAGNOSTICO_20261027.md).

O [visualizador local](VISUALIZADOR_QR_PRIVADO.md) consulta somente a API autenticada em loopback, mantém PNG em memória, oculta antes de renovar e mostra prazo local conservador. Polling tem atraso de observação; sistema/janela travados podem reter pixels. Não é garantia de apagamento remoto ou validade no WhatsApp. Sem imagem em chat, browser, token em query ou porta externa.

## Critério de conclusão ainda não atingido

1. Validar GUI/Tk e permissões locais Windows com conteúdo sintético; validar launchers atuais.
2. Verificar condução dos processos no terminal interno efetivo do Claude Code, sem remover proteções.
3. Revisar/aprovar explicitamente os seis Markdown e proposta comercial; formulários/depoimentos não substituem validação técnica.
4. Em horário combinado, autorizar pareamento e envio a contato de teste consentido; confirmar duas trocas com resposta vista no segundo telefone.

Sem esses resultados, não chamar o agente de pronto para aula/operação. Nenhuma coleta de histórico foi ampliada para contornar instabilidade; ressalva LID permanece hipótese documentada. Anexos, áudio, LID exclusivo, campanhas e retomadas continuam fora do escopo.

## Fontes e publicação

- [Codex CLI oficial](https://developers.openai.com/codex/cli/) e help local0.163.0.
- [Claude CLI](https://code.claude.com/docs/en/cli-reference), [modo programático](https://code.claude.com/docs/en/headless) e ensaios Windows descritos acima.
- Baileys/qrcode versionados: fontes em `gateway/README.md`.
- Código publicado somente no repositório autorizado `ibcappainstituto-arch/agente-whatsapp`; licença preservada, nenhuma fonte real/configuração/sessão publicada. Publicação e hashes conferidos não substituem E2E.

Ausência de API paga no código não garante cota futura nem que cobrança extra da conta esteja desligada. O kit não lê nem altera configurações privadas de billing.
