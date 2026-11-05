"""Static check for ordinary python and py fences."""

import ast
import importlib
from dataclasses import dataclass
from pathlib import Path

USD_MODULES = {"Usd", "Sdf", "UsdGeom", "UsdShade", "UsdLux"}


@dataclass(frozen=True)
class Finding:
    status: str
    symbol: str | None
    line: int
    reason: str
    page: str


def check_fences(path: Path) -> list[Finding]:
    page = str(path)
    text = Path(path).read_text(encoding="utf-8")
    findings: list[Finding] = []
    for start, source in _python_fences(text):
        findings.extend(_check_fence(page, start, source))
    return findings


def _python_fences(text: str) -> list[tuple[int, str]]:
    lines = text.splitlines()
    found: list[tuple[int, str]] = []
    index = 0
    while index < len(lines):
        if lines[index].strip() in {"```python", "```py"}:
            index += 1
            content_start = index + 1
            body: list[str] = []
            while index < len(lines) and lines[index].strip() != "```":
                body.append(lines[index])
                index += 1
            found.append((content_start, "\n".join(body)))
        index += 1
    return found


def _check_fence(page: str, content_start: int, source: str) -> list[Finding]:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        line = content_start + (exc.lineno or 1) - 1
        reason = exc.msg if exc.msg else "parse error"
        return [
            Finding(
                status="fail",
                symbol=None,
                line=line,
                reason=reason,
                page=page,
            )
        ]

    findings: list[Finding] = []
    for symbol, lineno in _usd_symbols(tree):
        file_line = content_start + lineno - 1
        if _symbol_exists(symbol):
            findings.append(
                Finding(
                    status="pass",
                    symbol=symbol,
                    line=file_line,
                    reason="",
                    page=page,
                )
            )
        else:
            findings.append(
                Finding(
                    status="fail",
                    symbol=symbol,
                    line=file_line,
                    reason=f"{symbol} was not found in the installed pxr modules",
                    page=page,
                )
            )
    return findings


def _usd_symbols(tree: ast.AST) -> list[tuple[str, int]]:
    parent: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parent[child] = node

    found: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        if isinstance(parent.get(node), ast.Attribute):
            continue
        parts = _chain(node)
        if parts is None:
            continue
        if parts[0] == "pxr":
            parts = parts[1:]
        if not parts or parts[0] not in USD_MODULES:
            continue
        found.append((".".join(parts), node.lineno))
    return found


def _chain(node: ast.AST) -> list[str] | None:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    parts.append(current.id)
    parts.reverse()
    return parts


def _symbol_exists(symbol: str) -> bool:
    module_name, _, rest = symbol.partition(".")
    try:
        obj = importlib.import_module(f"pxr.{module_name}")
    except ModuleNotFoundError:
        return False
    if rest == "":
        return True
    for name in rest.split("."):
        try:
            obj = getattr(obj, name)
        except AttributeError:
            return False
    return True
