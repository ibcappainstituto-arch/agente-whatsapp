import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cli_adapter as cli

SCHEMA = {"type": "object", "properties": {"mensagem": {"type": "string", "maxLength": 200},
           "avisar": {"type": "boolean"}}, "required": ["mensagem", "avisar"], "additionalProperties": False}
VALIDO = {"mensagem": "Qual é a fase?", "avisar": False}


class CLITests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.path = patch.object(cli.shutil, "which", side_effect=lambda nome: "/trusted/" + nome + ".exe")
        self.path.start()
        self.addCleanup(self.path.stop)

    def transporte(self, motor, resposta=None, codigo=0):
        def run(args, **kw):
            self.assertIs(kw["shell"], False)
            self.assertTrue(Path(kw["cwd"]).is_dir())
            if args[1:3] == ["login", "status"]:
                return subprocess.CompletedProcess(args, 0, "", "Logged in using ChatGPT")
            if args[1:3] == ["auth", "status"]:
                return subprocess.CompletedProcess(args, 0, json.dumps({"loggedIn": True, "authMethod": "claude.ai"}), "")
            self.assertEqual(kw["input"], "Dado não confiável: & echo INJECAO")
            self.assertNotIn("INJECAO", str(args))
            if motor == "codex":
                self.assertIn("--ignore-user-config", args)
                self.assertIn("read-only", args)
                self.assertIn("--ephemeral", args)
                Path(args[args.index("-o") + 1]).write_text(resposta or json.dumps(VALIDO), encoding="utf-8")
                return subprocess.CompletedProcess(args, codigo, "progresso não usado", "")
            self.assertNotIn("--bare", args)
            self.assertEqual(args[args.index("--tools") + 1], "")
            envelope = resposta or json.dumps({"subtype": "success", "is_error": False, "structured_output": VALIDO})
            return subprocess.CompletedProcess(args, codigo, envelope, "")
        return run

    def obter(self, motor="codex"):
        return cli.obter_decisao("Dado não confiável: & echo INJECAO", SCHEMA, motor)

    def test_codex_stdin_arquivo_schema_sem_shell(self):
        with patch.object(cli.subprocess, "run", side_effect=self.transporte("codex")) as run:
            self.assertEqual(self.obter(), VALIDO)
            pasta = run.call_args.kwargs["cwd"]
        self.assertFalse(Path(pasta).exists())

    def test_claude_structured_output_sem_ferramentas(self):
        with patch.object(cli.subprocess, "run", side_effect=self.transporte("claude")):
            self.assertEqual(self.obter("claude"), VALIDO)

    def test_api_env_bloqueia_antes_de_qualquer_processo(self):
        for chave in cli.ENV_PROIBIDO:
            with self.subTest(chave=chave), patch.dict(os.environ, {chave: "NUNCA_EXIBIR"}), patch.object(cli.subprocess, "run") as run:
                with self.assertRaises(cli.ErroCLI) as erro:
                    self.obter()
                self.assertNotIn("NUNCA_EXIBIR", str(erro.exception))
                run.assert_not_called()

    def test_login_api_codex_e_claude_bloqueado(self):
        for motor, stdout in (("codex", "Logged in using an API key"),
                              ("claude", '{"loggedIn":true,"authMethod":"api_key"}')):
            with patch.object(cli.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, stdout, "")) as run:
                with self.assertRaises(cli.ErroCLI):
                    self.obter(motor)
                self.assertEqual(run.call_count, 1)

    def test_claude_recusa_envelope_sem_output_erro_ou_truncado(self):
        for saida in ('{"result":"texto"}', '{"is_error":true,"structured_output":{}}', '{"structured_output":',
                      '{"subtype":"error_max_turns","structured_output":{}}',
                      '{"subtype":"success","is_error":"false","structured_output":{}}',
                      '{"structured_output":{"mensagem":"oi","avisar":false}}'):
            with patch.object(cli.subprocess, "run", side_effect=self.transporte("claude", saida)):
                with self.assertRaises(cli.ErroCLI):
                    self.obter("claude")

    def test_codex_recusa_json_truncado_campos_extras_tipo_errado(self):
        for saida in ('{"mensagem":', '{"mensagem":"oi"}', '{"mensagem":"oi","avisar":"false"}',
                      '{"mensagem":"oi","avisar":false,"ferramenta":"shell"}'):
            with patch.object(cli.subprocess, "run", side_effect=self.transporte("codex", saida)):
                with self.assertRaises(cli.ErroCLI):
                    self.obter()

    def test_exit_nao_zero_nao_libera_mesmo_com_saida(self):
        for motor in ("codex", "claude"):
            with patch.object(cli.subprocess, "run", side_effect=self.transporte(motor, codigo=1)):
                with self.assertRaises(cli.ErroCLI):
                    self.obter(motor)

    def test_timeout_erro_sanitizado(self):
        with patch.object(cli.subprocess, "run", side_effect=subprocess.TimeoutExpired("SEGREDO", 10)):
            with self.assertRaises(cli.ErroCLI) as erro:
                self.obter()
            self.assertNotIn("SEGREDO", str(erro.exception))

    def test_claude_wrapper_cmd_recusado(self):
        with patch.object(cli.shutil, "which", return_value="C:/npm/claude.cmd"):
            with self.assertRaises(cli.ErroCLI):
                cli.executavel("claude")

    def test_claude_wrapper_resolve_nativo_existente_sem_shell(self):
        with tempfile.TemporaryDirectory() as pasta:
            base = Path(pasta)
            exe = base / "node_modules/@anthropic-ai/claude-code/bin/claude.exe"
            exe.parent.mkdir(parents=True)
            exe.write_bytes(b"fixture-nao-executado")
            with patch.object(cli.shutil, "which", return_value=str(base / "claude.cmd")):
                self.assertEqual(cli.executavel("claude"), str(exe))

    def test_codex_wrapper_resolve_binario_npm_sem_shell(self):
        with tempfile.TemporaryDirectory() as pasta:
            base = Path(pasta)
            exe = base / "node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe"
            exe.parent.mkdir(parents=True)
            exe.write_bytes(b"fixture-nao-executado")
            with patch.object(cli.shutil, "which", return_value=str(base / "codex.cmd")):
                self.assertEqual(cli.executavel("codex"), str(exe))

    def test_json_duplicado_nan_e_raiz_lista_bloqueados(self):
        for texto in ('{"a":1,"a":2}', '{"a":NaN}', '[]'):
            with self.assertRaises(cli.ErroCLI):
                cli._json(texto)

    def test_sem_fallback_motor_desconhecido(self):
        with self.assertRaises(cli.ErroCLI):
            self.obter("api")


if __name__ == "__main__":
    unittest.main()
