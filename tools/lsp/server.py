"""MathLang Language Server.

Provides real-time diagnostics (syntax errors) and hover documentation for
`.mlang` DSL keywords over the Language Server Protocol. Completion is
intentionally out of scope. Runs over WebSocket so browser-based editors
(the Streamlit web UI) can connect directly; the same server can later back
a VSCode extension since it speaks the standard protocol.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lsprotocol import types
from pygls.lsp.server import LanguageServer

from core.errors import MathLangError
from core.parser import Parser
from tools.lsp.dsl_lsp_stub import PREDEFINED_KEYWORDS

KEYWORD_DOCS: dict[str, str] = {
    "meta": "プログラムのメタ情報 (id, topic など) を宣言するセクションです。",
    "config": "causal / fuzzy-threshold などの実行時オプションを設定するセクションです。",
    "mode": "評価モード (symbolic / polynomial / causal) を指定します。",
    "problem": "解くべき問題の初期式を宣言します。プログラムの起点です。",
    "prepare": "問題を解く前に定義する変数・前提式です。",
    "step": "式の変形の1ステップです。before/after または単一式で記述します。",
    "end": "最終的な答え(終了式)を宣言します。",
    "counterfactual": "「もしこうだったら」を試すための仮定と期待値を宣言します。",
}
assert set(KEYWORD_DOCS) == set(PREDEFINED_KEYWORDS)

_LINE_PATTERN = re.compile(r"line (\d+)")
_WORD_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def build_diagnostics(source: str) -> list[types.Diagnostic]:
    """Parse `source` and return LSP diagnostics for any syntax error."""

    try:
        Parser(source).parse()
    except MathLangError as exc:
        message = str(exc)
        match = _LINE_PATTERN.search(message)
        line = max(int(match.group(1)) - 1, 0) if match else 0
        return [
            types.Diagnostic(
                range=types.Range(
                    start=types.Position(line=line, character=0),
                    end=types.Position(line=line, character=1000),
                ),
                message=message,
                severity=types.DiagnosticSeverity.Error,
                source="mathlang-lsp",
            )
        ]
    return []


def hover_text_for(source: str, line: int, character: int) -> str | None:
    """Return a short doc string for the DSL keyword at the given position, if any."""

    lines = source.splitlines()
    if not (0 <= line < len(lines)):
        return None
    text_line = lines[line]
    for match in _WORD_PATTERN.finditer(text_line):
        if match.start() <= character <= match.end():
            return KEYWORD_DOCS.get(match.group(0).lower())
    return None


server = LanguageServer("mathlang-lsp", "v0.1")


def _publish(ls: LanguageServer, uri: str, text: str) -> None:
    ls.text_document_publish_diagnostics(
        types.PublishDiagnosticsParams(uri=uri, diagnostics=build_diagnostics(text))
    )


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: LanguageServer, params: types.DidOpenTextDocumentParams) -> None:
    _publish(ls, params.text_document.uri, params.text_document.text)


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: LanguageServer, params: types.DidChangeTextDocumentParams) -> None:
    doc = ls.workspace.get_text_document(params.text_document.uri)
    _publish(ls, params.text_document.uri, doc.source)


@server.feature(types.TEXT_DOCUMENT_HOVER)
def hover(ls: LanguageServer, params: types.HoverParams) -> types.Hover | None:
    doc = ls.workspace.get_text_document(params.text_document.uri)
    text = hover_text_for(doc.source, params.position.line, params.position.character)
    if text is None:
        return None
    return types.Hover(contents=types.MarkupContent(kind=types.MarkupKind.Markdown, value=text))


def main(host: str = "127.0.0.1", port: int = 2087) -> None:
    server.start_ws(host, port)


if __name__ == "__main__":
    main()
