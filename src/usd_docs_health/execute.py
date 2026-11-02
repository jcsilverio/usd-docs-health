"""Execution check for MyST code cells."""

import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

import jupytext
import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError, CellTimeoutError

TIMEOUT_SECONDS = 30

_SETUP_CELL = """\
import subprocess
_usd2gltf_calls = 0
_real_subprocess_run = subprocess.run

def _intercepting_run(*args, **kwargs):
    global _usd2gltf_calls
    argv = kwargs.get("args")
    if argv is None and args:
        argv = args[0]
    command = argv[0] if isinstance(argv, (list, tuple)) and argv else argv
    if command == "usd2gltf":
        _usd2gltf_calls += 1
        return subprocess.CompletedProcess(argv, 0)
    return _real_subprocess_run(*args, **kwargs)

subprocess.run = _intercepting_run
"""

_PROBE_CELL = "print(_usd2gltf_calls)"


@dataclass(frozen=True)
class CellResult:
    status: str
    line: int
    reason: str


class PageResults(list):
    def __init__(self, cells: list[CellResult], usd2gltf_calls: int):
        super().__init__(cells)
        self.usd2gltf_calls = usd2gltf_calls


def execute_page(
    path: Path,
    timeout_seconds: int = TIMEOUT_SECONDS,
    python_path: Path | None = None,
) -> PageResults:
    page = Path(path)
    text = page.read_text(encoding="utf-8")
    code_lines = _first_code_lines(text)
    if not code_lines:
        return PageResults([], 0)
    notebook = jupytext.read(page, fmt="md:myst")
    notebook.metadata["kernelspec"] = {
        "name": "python3",
        "display_name": "Python 3",
        "language": "python",
    }
    code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
    if len(code_cells) != len(code_lines):
        raise RuntimeError(
            f"{page} has {len(code_lines)} code cells in the file "
            f"and {len(code_cells)} in the notebook"
        )

    notebook.cells.insert(0, nbformat.v4.new_code_cell(_SETUP_CELL))
    probe = nbformat.v4.new_code_cell(_PROBE_CELL)
    notebook.cells.append(probe)

    timed_out = False
    source = _copy_source(page)
    with tempfile.TemporaryDirectory() as workdir:
        copy_root = Path(workdir)
        shutil.copytree(source, copy_root, dirs_exist_ok=True)
        page_dir = copy_root / page.parent.relative_to(source)
        client = NotebookClient(
            notebook,
            timeout=timeout_seconds,
            kernel_name="python3",
            resources={"metadata": {"path": str(page_dir)}},
        )
        try:
            if python_path is None:
                client.execute()
            else:
                client.execute(env=_kernel_env(python_path))
        except CellTimeoutError:
            timed_out = True
        except CellExecutionError:
            timed_out = False

    timeout_index = None
    if timed_out:
        for index, cell in enumerate(code_cells):
            if cell.get("execution_count") is not None or _error_text(cell):
                timeout_index = index
        if timeout_index is None:
            timeout_index = 0

    results: list[CellResult] = []
    failed = False
    for index, (line, cell) in enumerate(zip(code_lines, code_cells)):
        if failed:
            results.append(
                CellResult(status="skipped", line=line, reason="earlier cell failed")
            )
            continue
        error = _error_text(cell)
        if error:
            failed = True
            results.append(CellResult(status="fail", line=line, reason=error))
        elif timeout_index == index:
            failed = True
            results.append(CellResult(status="fail", line=line, reason="cell timed out"))
        elif cell.get("execution_count") is None:
            failed = True
            results.append(CellResult(status="fail", line=line, reason="cell did not run"))
        else:
            results.append(CellResult(status="pass", line=line, reason=""))
    return PageResults(results, _usd2gltf_calls(probe))


def _usd2gltf_calls(probe) -> int:
    text = _printed_text(probe)
    if text.isdigit():
        return int(text)
    return 0


def _printed_text(cell) -> str:
    parts: list[str] = []
    for output in cell.get("outputs", []):
        if output.get("output_type") != "stream":
            continue
        text = output.get("text", "")
        if isinstance(text, list):
            parts.extend(text)
        else:
            parts.append(text)
    return "".join(parts).strip()


def _copy_source(page: Path) -> Path:
    for parent in page.parents:
        if parent.name == "docs":
            return parent
    return page.parent


def _kernel_env(python_path: Path | None) -> dict[str, str] | None:
    if python_path is None:
        return None
    env = os.environ.copy()
    previous = env.get("PYTHONPATH", "")
    src = str(python_path)
    env["PYTHONPATH"] = src if not previous else src + os.pathsep + previous
    return env


def _first_code_lines(text: str) -> list[int]:
    lines = text.splitlines()
    found: list[int] = []
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped == "```{code-cell}" or stripped.startswith("```{code-cell} "):
            index += 1
            if index < len(lines) and lines[index].startswith("---"):
                index += 1
                while index < len(lines) and not lines[index].startswith("---"):
                    index += 1
                index += 1
            elif index < len(lines) and lines[index].lstrip().startswith(":"):
                while index < len(lines) and lines[index].lstrip().startswith(":"):
                    index += 1
            if index < len(lines) and not lines[index].strip():
                index += 1
            found.append(index + 1)
            while index < len(lines) and lines[index].strip() != "```":
                index += 1
        index += 1
    return found


def _error_text(cell) -> str | None:
    for output in cell.get("outputs", []):
        if output.get("output_type") == "error":
            return output.get("evalue") or output.get("ename") or "cell failed"
    return None
