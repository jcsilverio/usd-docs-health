"""Static check for ordinary python and py fences."""

import ast
import importlib
import textwrap
from dataclasses import dataclass
from pathlib import Path

USD_MODULES = {"Usd", "Sdf", "UsdGeom", "UsdShade", "UsdLux"}

# Reasons on a parse finding when the fence parsed only after a fragment retry.
FRAGMENT_REASONS = frozenset(
    {
        "fragment, parsed as dedented",
        "fragment, parsed as list item",
        "fragment, parsed as dict entry",
    }
)


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
        tree, reason, shift = _parse_fence(source)
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

    findings: list[Finding] = [
        Finding(
            status="pass",
            symbol=None,
            line=content_start,
            reason=reason,
            page=page,
        )
    ]
    for symbol, lineno in _usd_symbols(tree):
        # shift is the wrapper line added so a fragment can be parsed.
        # That line is not part of the lesson, so it is not reported.
        file_line = content_start + lineno - 1 - shift
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


def _parse_fence(source: str) -> tuple[ast.AST, str, int]:
    """Parse a fence. On failure, retry it as a fragment.

    Returns the tree, the parse reason, and how many lines were added
    before the lesson text. A fence that parses as written has an empty
    reason and a shift of 0. The original SyntaxError is raised when the
    fence and all three fragment tries fail.
    """
    try:
        return ast.parse(source), "", 0
    except SyntaxError as original:
        saved = original

    dedented = textwrap.dedent(source)
    # The bracket or brace is on its own line, so the lesson text starts
    # one line later in the tree than it does in the file.
    attempts = (
        (dedented, "fragment, parsed as dedented", 0),
        ("[\n" + dedented + "\n]", "fragment, parsed as list item", 1),
        ("{\n" + dedented + "\n}", "fragment, parsed as dict entry", 1),
    )
    for text, reason, shift in attempts:
        try:
            return ast.parse(text), reason, shift
        except SyntaxError:
            continue
    raise saved


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
