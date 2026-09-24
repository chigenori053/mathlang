"""Interactive MathLang session (`mathlang repl`)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, TextIO

from core.errors import EvaluationError, MathLangError
from mathlang import __version__, api
from mathlang.cli import program_lines

HELP = """\
Enter an expression to evaluate it, or assign a variable with NAME = EXPR.
The previous result is available as `ans`.

  :simplify EXPR        simplify (uses current variables)
  :expand EXPR          expand products and powers
  :factor EXPR          factor a polynomial
  :equiv EXPR1 ; EXPR2  check equivalence
  :convert EXPR -> UNIT unit conversion, e.g. :convert 3*kilometer -> meter
  :run FILE             run a .mlang program
  :dsl                  enter a program inline; finish with an empty line
  :vars                 list variables        :clear   remove all variables
  :json on|off          toggle JSON output    :timeout SECONDS
  :help                 this message          :quit    leave (also Ctrl-D)"""

_ASSIGNMENT = re.compile(r"^([A-Za-z]\w*)\s*=(?!=)\s*(.+)$")
_QUIT = {":quit", ":q", ":exit", "quit", "exit"}


class Repl:
    def __init__(
        self,
        *,
        timeout: float | None = None,
        json_output: bool = False,
        out: TextIO,
    ) -> None:
        self.timeout = timeout
        self.json_output = json_output
        self.out = out
        self.variables: dict[str, str] = {}
        self._dsl_lines: list[str] | None = None
        self._commands: dict[str, Callable[[str], Any]] = {
            ":simplify": lambda arg: ("simplify", api.simplify(arg, self.variables)),
            ":expand": lambda arg: ("expand", api.expand(arg)),
            ":factor": lambda arg: ("factor", api.factor(arg)),
            ":equiv": self._equiv,
            ":convert": self._convert,
            ":run": self._run_file,
            ":vars": self._vars,
            ":clear": self._clear,
            ":json": self._toggle_json,
            ":timeout": self._set_timeout,
            ":help": lambda arg: ("help", HELP),
        }

    # -- driver -------------------------------------------------------------

    def loop(self, stdin: TextIO) -> int:
        interactive = stdin.isatty()
        if interactive:
            try:
                import readline  # noqa: F401 - enables line editing and history
            except ImportError:  # pragma: no cover - e.g. Windows
                pass
            self._print(f"MathLang {__version__} — type :help for commands, :quit to exit.")
        while True:
            prompt = "...... " if self._dsl_lines is not None else "mathlang> "
            try:
                line = input(prompt) if interactive else stdin.readline()
            except EOFError:
                line = ""
                eof = True
            except KeyboardInterrupt:
                self._dsl_lines = None
                self._print("")
                continue
            else:
                eof = not interactive and line == ""
            if eof:
                if self._dsl_lines:
                    self.handle("")
                if interactive:
                    self._print("")
                return 0
            if self.handle(line.rstrip("\n")) is False:
                return 0

    def handle(self, line: str) -> bool:
        """Process one input line. Returns False when the session should end."""

        if self._dsl_lines is not None:
            if line.strip():
                self._dsl_lines.append(line)
                return True
            source, self._dsl_lines = "\n".join(self._dsl_lines), None
            self._dispatch(lambda: self._run_source(source))
            return True

        text = line.strip()
        if not text or text.startswith("#"):
            return True
        if text in _QUIT:
            return False
        if text == ":dsl":
            self._dsl_lines = []
            return True
        if text.startswith(":"):
            name, _, arg = text.partition(" ")
            command = self._commands.get(name)
            if command is None:
                self._report_error("command", MathLangError(f"Unknown command '{name}'. Type :help."))
                return True
            self._dispatch(lambda: command(arg.strip()))
            return True

        match = _ASSIGNMENT.match(text)
        if match:
            name, expr = match.groups()
            self._dispatch(lambda: self._assign(name, expr))
        else:
            self._dispatch(lambda: self._evaluate(text))
        return True

    # -- commands -----------------------------------------------------------

    def _evaluate(self, expr: str) -> tuple[str, Any]:
        try:
            result = api.evaluate(expr, self.variables)
            self.variables["ans"] = result["exact"]
            return "eval", result
        except EvaluationError as exc:
            if not str(exc).startswith("Undefined symbols"):
                raise
        # Free symbols remain: show the simplified symbolic form instead.
        simplified = api.simplify(expr, self.variables)
        self.variables["ans"] = simplified
        return "simplify", simplified

    def _assign(self, name: str, expr: str) -> tuple[str, Any]:
        if name.startswith("_") or name == "ans":
            raise MathLangError(f"Cannot assign to '{name}'.")
        value = api.simplify(expr, self.variables)
        self.variables[name] = value
        return "assign", {"name": name, "value": value}

    def _equiv(self, arg: str) -> tuple[str, Any]:
        left, sep, right = arg.partition(";")
        if not sep or not left.strip() or not right.strip():
            raise MathLangError("Usage: :equiv EXPR1 ; EXPR2")
        return "equiv", api.check_equivalence(left.strip(), right.strip())

    def _convert(self, arg: str) -> tuple[str, Any]:
        expr, sep, unit = arg.partition("->")
        if not sep or not expr.strip() or not unit.strip():
            raise MathLangError("Usage: :convert EXPR -> UNIT")
        return "convert", api.convert_units(expr.strip(), unit.strip())

    def _run_file(self, arg: str) -> tuple[str, Any]:
        path = Path(arg)
        if not arg or not path.is_file():
            raise MathLangError(f"Script '{arg}' not found")
        return self._run_source(path.read_text(encoding="utf-8"))

    def _run_source(self, source: str) -> tuple[str, Any]:
        return "run", api.run_program(source)

    def _vars(self, arg: str) -> tuple[str, Any]:
        return "vars", dict(self.variables)

    def _clear(self, arg: str) -> tuple[str, Any]:
        self.variables.clear()
        return "clear", "variables cleared"

    def _toggle_json(self, arg: str) -> tuple[str, Any]:
        if arg not in ("on", "off"):
            raise MathLangError("Usage: :json on|off")
        self.json_output = arg == "on"
        return "json", f"JSON output {arg}"

    def _set_timeout(self, arg: str) -> tuple[str, Any]:
        try:
            self.timeout = float(arg)
        except ValueError:
            raise MathLangError("Usage: :timeout SECONDS (0 disables)") from None
        return "timeout", f"timeout {self.timeout:g}s"

    # -- output -------------------------------------------------------------

    def _dispatch(self, action: Callable[[], tuple[str, Any]]) -> None:
        try:
            with api.time_limit(self.timeout):
                command, result = action()
        except Exception as exc:  # report and keep the session alive
            self._report_error("error", exc)
            return
        if self.json_output:
            if isinstance(result, api.ProgramResult):
                payload = {"command": command, **result.to_dict()}
            else:
                payload = {"ok": True, "command": command, "result": result}
            self._print(json.dumps(payload, ensure_ascii=False, default=str))
            return
        for line in _render(command, result):
            self._print(line)

    def _report_error(self, command: str, exc: BaseException) -> None:
        if self.json_output:
            payload = {"ok": False, "command": command,
                       "error": {"type": type(exc).__name__, "message": str(exc)}}
            self._print(json.dumps(payload, ensure_ascii=False))
        else:
            self._print(f"Error: {exc}")

    def _print(self, text: str) -> None:
        print(text, file=self.out, flush=True)


def _render(command: str, result: Any) -> list[str]:
    if command == "eval":
        if result["exact"] == result["numeric"]:
            return [result["exact"]]
        return [f"{result['exact']}  ≈ {result['numeric']}"]
    if command == "assign":
        return [f"{result['name']} = {result['value']}"]
    if command == "equiv":
        return ["equivalent" if result else "not equivalent"]
    if command == "vars":
        return [f"{name} = {value}" for name, value in result.items()] or ["(no variables)"]
    if command == "run":
        lines = program_lines(result)
        if result.error:
            lines.append(f"Error: {result.error}")
        return lines
    return [str(result)]
