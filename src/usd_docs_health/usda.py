"""USDA check: parse each usda example with USD's own text parser."""

import re
from pathlib import Path

from pxr import Sdf, Tf

from usd_docs_health.static import Finding

NBSP = "\u00a0"
HEADER = "#usda 1.0"
METADATA_REASON = "fragment, parsed as layer metadata"

_FENCE = re.compile(r"^\s*```\s*usda\s*$")
_CODE_BLOCK = re.compile(r"^\s*```\{code-block\}\s+usda\s*$")
# USD writes the position as path:line:column: before the message.
# An anonymous layer has no path, so the message starts at the colon.
_POSITION = re.compile(r":(\d+):(\d+):\s*")
# A string on one line, or a triple-quoted string over several lines.
_QUOTED = re.compile(r'"""[\s\S]*?"""|"[^"\n]*"|\'[^\'\n]*\'')


class UsdaResults(list):
    def __init__(self, findings: list[Finding], elided: int):
        super().__init__(findings)
        self.elided = elided


def check_usda(path: Path) -> UsdaResults:
    page = str(path)
    text = Path(path).read_text(encoding="utf-8")
    findings: list[Finding] = []
    elided = 0
    for first_line, body in _usda_examples(text):
        finding, was_elided = _check_example(page, first_line, body)
        if finding is not None:
            findings.append(finding)
        if was_elided:
            elided += 1
    return UsdaResults(findings, elided)


def _usda_examples(text: str) -> list[tuple[int, list[str]]]:
    """Return each example's first lesson line with text, and its lines from there."""
    lines = text.splitlines()
    found: list[tuple[int, list[str]]] = []
    index = 0
    while index < len(lines):
        code_block = _CODE_BLOCK.match(lines[index])
        if not (code_block or _FENCE.match(lines[index])):
            index += 1
            continue
        index += 1
        if code_block:
            while index < len(lines) and lines[index].lstrip().startswith(":"):
                index += 1
        # Python's strip() removes U+00A0, and a line of them is not blank to USD.
        while index < len(lines) and lines[index].strip(" \t") == "":
            index += 1
        start = index
        body: list[str] = []
        while index < len(lines) and lines[index].strip() != "```":
            body.append(lines[index])
            index += 1
        found.append((start + 1, body))
        index += 1
    return found


def _check_example(
    page: str, first_line: int, body: list[str]
) -> tuple[Finding | None, bool]:
    """Return the example's finding, or None when elided, and whether it is elided."""
    nbsp_line = next(
        (first_line + offset for offset, line in enumerate(body) if NBSP in line),
        None,
    )
    nbsp = None
    if nbsp_line is not None:
        nbsp = f"non-breaking space (U+00A0) at line {nbsp_line}"

    body = [line.replace(NBSP, " ") for line in body]
    if body and body[0].startswith("#usda"):
        header, rest, added = body[0], body[1:], 0
    else:
        header, rest, added = HEADER, body, 1

    messages = _parse([header, *rest])
    if messages and _is_elided(rest):
        if nbsp is None:
            return None, True
        return _fail(page, nbsp_line, nbsp), True

    reason = ""
    if messages and not _parse([header, "(", *rest, ")"]):
        messages, reason = [], METADATA_REASON

    if nbsp is not None:
        if messages:
            line = _error_line(messages, first_line, added)
            nbsp += f"; line {line}: {_join(messages)}"
        return _fail(page, nbsp_line, nbsp), False
    if messages:
        line = _error_line(messages, first_line, added)
        return _fail(page, line, _join(messages)), False
    return (
        Finding(status="pass", symbol=None, line=first_line, reason=reason, page=page),
        False,
    )


def _parse(lines: list[str]) -> list[str]:
    """Return USD's error messages in order. An empty list means the text parsed."""
    layer = Sdf.Layer.CreateAnonymous(".usda")
    try:
        if layer.ImportFromString("\n".join(lines) + "\n"):
            return []
    except Tf.ErrorException as exc:
        return [error.commentary for error in exc.args]
    return ["USD could not read the text"]


def _is_elided(lines: list[str]) -> bool:
    return "..." in _QUOTED.sub("", "\n".join(lines))


def _error_line(messages: list[str], first_line: int, added: int) -> int:
    for message in reversed(messages):
        match = _POSITION.search(message)
        if match:
            return first_line + int(match.group(1)) - 1 - added
    return first_line


def _join(messages: list[str]) -> str:
    texts = []
    for message in messages:
        match = _POSITION.search(message)
        text = (message[match.end():] if match else message).strip()
        # USD often raises the same error twice, without and then with its position.
        if text not in texts:
            texts.append(text)
    return "; ".join(texts)


def _fail(page: str, line: int, reason: str) -> Finding:
    return Finding(status="fail", symbol=None, line=line, reason=reason, page=page)
