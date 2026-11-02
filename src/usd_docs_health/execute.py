"""Execution check for MyST code cells."""

import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

import jupytext
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError, CellTimeoutError

TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class CellResult:
    status: str
    line: int
    reason: str


def execute_page(
    path: Path,
    timeout_seconds: int = TIMEOUT_SECONDS,
    python_path: Path | None = None,
) -> list[CellResult]:
    page = Path(path)
    text = page.read_text(encoding="utf-8")
    code_lines = _first_code_lines(text)
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

    timed_out = False
    with tempfile.TemporaryDirectory() as workdir:
        copy_root = Path(workdir)
        shutil.copytree(page.parent, copy_root, dirs_exist_ok=True)
        client = NotebookClient(
            notebook,
            timeout=timeout_seconds,
            kernel_name="python3",
            resources={"metadata": {"path": str(copy_root)}},
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
    return results


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
