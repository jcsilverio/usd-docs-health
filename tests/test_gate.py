from pathlib import Path

from usd_docs_health.cli import main

FIXTURES = Path(__file__).parent / "fixtures" / "pages"


def test_gate_accepts_a_py_fence(capsys):
    page = FIXTURES / "py_fence.md"
    assert main(["gate", "--page", str(page)]) == 0
    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    assert lines[0] == "accept"
    assert "passed 1, failed 0, skipped 0" in captured.out
    assert "usd2gltf calls 0" in captured.out
    assert "reject" not in captured.out


def test_gate_rejects_py_fence_that_does_not_parse(tmp_path, capsys):
    page = tmp_path / "proposed.md"
    page.write_text(
        "# Proposed\n"
        "\n"
        "```py\n"
        "#usda 1.0\n"
        "\n"
        'def Xform "World"\n'
        "{\n"
        "}\n"
        "```\n",
        encoding="utf-8",
    )
    assert main(["gate", "--page", str(page)]) == 1
    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    assert lines[0] == "reject"
    assert "expected '('" in captured.out
    assert "```py" not in captured.out
    assert "accept" not in captured.out


def test_gate_rejects_missing_symbol(capsys):
    page = FIXTURES / "missing_symbol.md"
    assert main(["gate", "--page", str(page)]) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == "reject"
    assert "Usd.Foo.Bar" in captured.out
    assert "was not found" in captured.out


def test_gate_rejects_page_with_no_eligible_checks(tmp_path, capsys):
    page = tmp_path / "prose.md"
    page.write_text("# Only prose\n\nNothing to run.\n", encoding="utf-8")
    assert main(["gate", "--page", str(page)]) == 1
    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    assert lines[0] == "reject"
    assert "passed 0, failed 0, skipped 0" in captured.out
    assert "no eligible checks" in captured.out
    assert "accept" not in captured.out


def test_gate_rejects_failed_cell_and_names_the_skip(capsys):
    page = FIXTURES / "cell_skipped.md"
    assert main(["gate", "--page", str(page)]) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == "reject"
    assert "passed 0, failed 1, skipped 1" in captured.out
    assert "broken cell" in captured.out
    assert "earlier cell failed" in captured.out


def test_gate_accepts_cell_that_imports_corpus_src(tmp_path, monkeypatch, capsys):
    corpus = tmp_path / "vendor" / "learnopenusd"
    docs = corpus / "docs"
    src = corpus / "src"
    docs.mkdir(parents=True)
    src.mkdir()
    (src / "tinybox.py").write_text("LABEL = 'World'\n", encoding="utf-8")
    page = docs / "cell_tinybox.md"
    page.write_text(
        "# Cell imports a corpus module\n"
        "\n"
        "```{code-cell}\n"
        "import tinybox\n"
        "print(tinybox.LABEL)\n"
        "```\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    assert main(
        [
            "gate",
            "--page",
            "vendor/learnopenusd/docs/cell_tinybox.md",
            "--corpus",
            "vendor/learnopenusd",
        ]
    ) == 0
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == "accept"
    assert "passed 1, failed 0, skipped 0" in captured.out


def test_gate_missing_page_is_exit_2(tmp_path, capsys):
    missing = tmp_path / "missing.md"
    assert main(["gate", "--page", str(missing)]) == 2
    captured = capsys.readouterr()
    assert "page not found" in captured.err
    assert captured.out == ""


def test_gate_missing_corpus_is_exit_2(tmp_path, capsys):
    page = tmp_path / "page.md"
    page.write_text("# Hi\n", encoding="utf-8")
    missing = tmp_path / "missing-corpus"
    assert main(["gate", "--page", str(page), "--corpus", str(missing)]) == 2
    captured = capsys.readouterr()
    assert "corpus not found" in captured.err
    assert "reject" not in captured.out
    assert "accept" not in captured.out


def test_gate_lfs_pointer_is_exit_2(capsys):
    page = FIXTURES / "cell_pointer.md"
    assert main(["gate", "--page", str(page)]) == 2
    captured = capsys.readouterr()
    assert "LFS pointer file:" in captured.err
    assert "cell_pointer_asset.usda" in captured.err
    assert captured.out == ""


def test_gate_unexpected_error_is_exit_3(tmp_path, monkeypatch, capsys):
    page = tmp_path / "page.md"
    page.write_text("# Hi\n\n```python\nUsd.Stage.Open()\n```\n", encoding="utf-8")

    def boom(path):
        raise RuntimeError("checker broke")

    monkeypatch.setattr("usd_docs_health.cli.check_fences", boom)
    assert main(["gate", "--page", str(page)]) == 3
    captured = capsys.readouterr()
    assert "unexpected checker error" in captured.err
    assert "page.md" in captured.err
    assert "checker broke" in captured.err
    assert "accept" not in captured.out
    assert "reject" not in captured.out
