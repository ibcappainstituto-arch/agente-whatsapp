"""CLI local por assinatura; não lê/copía credenciais nem chama API diretamente.

Fontes: Codex CLI 0.163.0 (`exec --help`, `features list`, 2026-10-26);
https://code.claude.com/docs/en/cli-reference
https://code.claude.com/docs/en/headless
Não existe fallback para API paga. Limite, login ou saída inválida = falha fechada.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


class ErroCLI(RuntimeError):
    """Falha sanitizada: nunca inclui prompt, credenciais ou stdout do CLI."""


# Estes modos podem selecionar cobrança API ou outro backend. Não alterar o
# ambiente global: a pessoa deve resolver a ambiguidade antes de continuar.
ENV_PROIBIDO = {
    "OPENAI_API_KEY", "CODEX_API_KEY", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
    "OPENAI_BASE_URL", "ANTHROPIC_BASE_URL", "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY", "CLAUDE_CODE_OAUTH_TOKEN",
}
MAX_OUTPUT = 128 * 1024
TIMEOUT = 180


def executavel(nome: str) -> str:
    """Resolve binário nativo; não passa .cmd/.bat/.ps1 ao shell Windows."""
    if nome not in {"codex", "claude"}:
        raise ErroCLI("Motor deve ser codex ou claude.")
    caminho = shutil.which(nome)
    if not caminho:
        raise ErroCLI(f"{nome} não encontrado no PATH. Instale o CLI oficial e faça login por assinatura.")
    arquivo = Path(caminho)
    if arquivo.suffix.lower() in {".cmd", ".bat", ".ps1"}:
        if nome == "claude":
            candidato = arquivo.parent / "node_modules" / "@anthropic-ai" / "claude-code" / "bin" / "claude.exe"
            if candidato.is_file():
                return str(candidato)
        if nome == "codex":
            base = arquivo.parent / "node_modules" / "@openai" / "codex"
            for arch, triple in (("x64", "x86_64-pc-windows-msvc"), ("arm64", "aarch64-pc-windows-msvc")):
                caminhos = (
                    base / "node_modules" / "@openai" / f"codex-win32-{arch}" / "vendor" / triple / "bin" / "codex.exe",
                    base / "vendor" / triple / "bin" / "codex.exe",
                    base.parent / f"codex-win32-{arch}" / "vendor" / triple / "bin" / "codex.exe",
                )
                for candidato in caminhos:
                    if candidato.is_file():
                        return str(candidato)
        raise ErroCLI(f"{nome}: só foi encontrado um wrapper de shell. Use a instalação nativa oficial, sem executar .cmd pelo agente.")
    return str(arquivo)


def _ambiente() -> dict[str, str]:
    if any(os.environ.get(k) for k in ENV_PROIBIDO):
        raise ErroCLI("Há configuração de API/provedor no ambiente. Remova-a deste terminal e use login por assinatura; nada foi executado.")
    # Evita que o contexto de outro processo CLI desvie a chamada.
    ambiente = dict(os.environ)
    for k in ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT"):
        ambiente.pop(k, None)
    return ambiente


def _rodar(args: list[str], *, ambiente: dict[str, str], pasta: str, entrada: str | None = None,
           timeout: int = TIMEOUT) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(args, input=entrada, cwd=pasta, env=ambiente,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="strict", timeout=timeout, shell=False)
    except (OSError, subprocess.TimeoutExpired, UnicodeError):
        raise ErroCLI("CLI indisponível ou tempo esgotado. Nenhuma resposta liberada para envio.") from None


def _json(texto: str) -> dict:
    def objeto(pares):
        resultado = {}
        for chave, valor in pares:
            if chave in resultado:
                raise ValueError("chave duplicada")
            resultado[chave] = valor
        return resultado
    try:
        if len(texto.encode("utf-8")) > MAX_OUTPUT:
            raise ValueError("tamanho")
        valor = json.loads(texto, object_pairs_hook=objeto,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError("número")))
        if not isinstance(valor, dict):
            raise ValueError("objeto")
        return valor
    except (ValueError, UnicodeError):
        raise ErroCLI("CLI devolveu JSON inválido, incompleto ou fora do limite. Nada será enviado.") from None


def _validar(valor, esquema: dict, caminho: str = "resposta") -> None:
    """Subconjunto fechado de JSON Schema usado por este kit, não validador geral."""
    aceitos = {"type", "properties", "required", "additionalProperties", "enum", "items",
               "minLength", "maxLength", "minItems", "maxItems", "minimum", "maximum",
               "description", "title", "$schema"}
    if not isinstance(esquema, dict) or set(esquema) - aceitos:
        raise ErroCLI("Schema contém regra não suportada pelo validador local.")
    tipo = esquema.get("type")
    tipos = {"object": lambda v: isinstance(v, dict), "array": lambda v: isinstance(v, list),
             "string": lambda v: isinstance(v, str), "boolean": lambda v: type(v) is bool,
             "integer": lambda v: type(v) is int, "number": lambda v: type(v) in (int, float),
             "null": lambda v: v is None}
    if tipo not in tipos or not tipos[tipo](valor):
        raise ErroCLI(f"Saída incompatível com o schema ({caminho}).")
    if "enum" in esquema and valor not in esquema["enum"]:
        raise ErroCLI(f"Valor fora do schema ({caminho}).")
    if tipo == "object":
        props = esquema.get("properties", {})
        if set(esquema.get("required", [])) - set(valor):
            raise ErroCLI(f"Campos obrigatórios ausentes ({caminho}).")
        if esquema.get("additionalProperties") is False and set(valor) - set(props):
            raise ErroCLI(f"Campos inesperados ({caminho}).")
        for k, v in valor.items():
            if k in props:
                _validar(v, props[k], f"{caminho}.{k}")
    elif tipo == "array":
        if "items" not in esquema:
            raise ErroCLI("Array sem schema de itens não é aceito.")
        for item in valor:
            _validar(item, esquema["items"], caminho + "[]")
    if tipo in {"string", "array"}:
        minimo, maximo = ("minLength", "maxLength") if tipo == "string" else ("minItems", "maxItems")
        if len(valor) < esquema.get(minimo, 0) or len(valor) > esquema.get(maximo, MAX_OUTPUT):
            raise ErroCLI(f"Tamanho fora do schema ({caminho}).")
    elif tipo in {"integer", "number"}:
        if valor < esquema.get("minimum", float("-inf")) or valor > esquema.get("maximum", float("inf")):
            raise ErroCLI(f"Número fora do schema ({caminho}).")


def _assinatura(exe: str, motor: str, ambiente: dict, pasta: str) -> None:
    args = [exe, "login", "status"] if motor == "codex" else [exe, "auth", "status"]
    resultado = _rodar(args, ambiente=ambiente, pasta=pasta, timeout=20)
    if resultado.returncode:
        raise ErroCLI(f"{motor}: login por assinatura não confirmado. Faça login no CLI oficial primeiro.")
    if motor == "codex":
        # Status do Codex é texto, normalmente em stderr. Não o registrar.
        status = resultado.stdout + "\n" + resultado.stderr
        ok = bool(re.search(r"logged\s+in\s+using\s+chatgpt", status, re.I))
    else:
        status = _json(resultado.stdout)
        ok = status.get("loggedIn") is True and status.get("authMethod") == "claude.ai"
    if not ok:
        raise ErroCLI(f"{motor}: autenticação não identificada como assinatura. API e modos ambíguos bloqueados.")


def verificar_autenticacao(motor: str) -> None:
    ambiente = _ambiente()
    exe = executavel(motor)
    with tempfile.TemporaryDirectory(prefix="whatsapp-cli-check-") as pasta:
        _assinatura(exe, motor, ambiente, pasta)


# Alias para verificações manuais/compatibilidade do instalador.
verificar_motor = verificar_autenticacao


def obter_decisao(prompt: str, schema: dict, motor: str) -> dict:
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 100_000:
        raise ErroCLI("Prompt vazio ou grande demais.")
    if not isinstance(schema, dict) or schema.get("type") != "object":
        raise ErroCLI("A resposta deve usar schema de objeto.")
    ambiente = _ambiente()
    exe = executavel(motor)
    with tempfile.TemporaryDirectory(prefix="whatsapp-cli-") as pasta:
        _assinatura(exe, motor, ambiente, pasta)
        p = Path(pasta)
        if motor == "codex":
            esquema_path = p / "schema.json"
            saida_path = p / "resposta.json"
            esquema_path.write_text(json.dumps(schema, ensure_ascii=False), encoding="utf-8")
            args = [exe, "exec", "--ignore-user-config", "--skip-git-repo-check", "--ephemeral",
                    "-s", "read-only", "-c", 'model_provider="openai"',
                    "-c", 'web_search="disabled"', "-c", "mcp_servers={}",
                    "--disable", "shell_tool", "--disable", "unified_exec", "--disable", "apps",
                    "--disable", "plugins", "--disable", "hooks", "--disable", "multi_agent",
                    "--disable", "computer_use", "--disable", "browser_use",
                    "--disable", "image_generation", "--disable", "code_mode_host",
                    "--output-schema", str(esquema_path), "-o", str(saida_path), "-"]
            resultado = _rodar(args, ambiente=ambiente, pasta=pasta, entrada=prompt)
            if resultado.returncode or not saida_path.is_file():
                raise ErroCLI("Codex falhou (login, limite ou CLI incompatível). Nada será enviado; não há fallback pago.")
            if saida_path.stat().st_size > MAX_OUTPUT:
                raise ErroCLI("Resposta Codex excede o limite.")
            try:
                decisao = _json(saida_path.read_text(encoding="utf-8"))
            except OSError:
                raise ErroCLI("Não foi possível ler a resposta Codex.") from None
        else:
            # --safe-mode preserva login; --bare NÃO é usado, pois ignora OAuth.
            args = [exe, "-p", "--safe-mode", "--output-format", "json", "--json-schema", json.dumps(schema),
                    "--tools", "", "--disallowedTools", "mcp__*", "--strict-mcp-config",
                    "--mcp-config", '{"mcpServers":{}}', "--setting-sources", "",
                    "--no-session-persistence", "--disable-slash-commands"]
            resultado = _rodar(args, ambiente=ambiente, pasta=pasta, entrada=prompt)
            if resultado.returncode:
                raise ErroCLI("Claude falhou (login, limite ou CLI incompatível). Nada será enviado; não há fallback pago.")
            envelope = _json(resultado.stdout)
            if envelope.get("is_error") is not False or envelope.get("subtype") != "success":
                raise ErroCLI("Claude não concluiu a geração estruturada.")
            decisao = envelope.get("structured_output")
            if not isinstance(decisao, dict):
                raise ErroCLI("Claude não devolveu structured_output válido.")
        _validar(decisao, schema)
        return decisao
