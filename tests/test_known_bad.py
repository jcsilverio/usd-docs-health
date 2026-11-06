from pathlib import Path

from usd_docs_health.cli import main

CASES = Path(__file__).parent / "fixtures" / "known_bad"


def _fence_body(path: Path, opener: str) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    start = lines.index(opener)
    end = lines.index("```", start + 1)
    return "\n".join(lines[start + 1 : end])


def test_gate_rejects_usda_in_python_fence(capsys):
    page = CASES / "usda_python.md"
    assert main(["gate", "--page", str(page)]) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == "reject"
    assert "passed 0, failed 1, skipped 0" in captured.out
    assert "expected '('" in captured.out
    assert "accept" not in captured.out


def test_gate_rejects_py_fragment(capsys):
    page = CASES / "fragment_py.md"
    assert main(["gate", "--page", str(page)]) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == "reject"
    assert "passed 0, failed 1, skipped 0" in captured.out
    assert "unexpected indent" in captured.out
    assert "accept" not in captured.out


def test_gate_rejects_prim_range_cell(capsys):
    page = CASES / "prim_range_cell.md"
    assert main(["gate", "--page", str(page)]) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == "reject"
    assert "passed 0, failed 1, skipped 0" in captured.out
    assert "name 'prim_range' is not defined" in captured.out
    assert "accept" not in captured.out


def test_gate_rejects_wording_only_edit(capsys):
    original = CASES / "usda_python.md"
    edited = CASES / "usda_python_wording.md"
    assert original.read_text(encoding="utf-8") != edited.read_text(encoding="utf-8")
    assert _fence_body(original, "```python") == _fence_body(edited, "```python")
    assert main(["gate", "--page", str(edited)]) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == "reject"
    assert "passed 0, failed 1, skipped 0" in captured.out
    assert "expected '('" in captured.out
    assert "accept" not in captured.out


def test_gate_rejects_visible_create_new_stage(capsys):
    page = CASES / "create_new_stage_visible.md"
    assert main(["gate", "--page", str(page)]) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == "reject"
    assert "passed 0, failed 1, skipped 0" in captured.out
    assert "name 'create_new_stage' is not defined" in captured.out
    assert "accept" not in captured.out
