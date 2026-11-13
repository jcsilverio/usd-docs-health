from pathlib import Path

import pytest

from usd_docs_health.cli import main

FIXTURES = Path(__file__).parent / "fixtures" / "pages"


def test_gate_accepts_a_py_fence(capsys):
    page = FIXTURES / "py_fence.md"
    assert main(["gate", "--page", str(page)]) == 0
    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    assert lines[0] == "accept"
    assert "passed 2, failed 0, skipped 0" in captured.out
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
    assert "referenced, not scanned 0" in captured.out
    assert "accept" not in captured.out


def test_gate_rejects_include_only_page(tmp_path, capsys):
    page = tmp_path / "exercise.md"
    page.write_text(
        "# Exercise\n"
        "\n"
        "```{literalinclude} scripts/example.py\n"
        ":caption: example.py\n"
        "```\n",
        encoding="utf-8",
    )
    assert main(["gate", "--page", str(page)]) == 1
    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    assert lines[0] == "reject"
    assert "passed 0, failed 0, skipped 0" in captured.out
    assert "referenced, not scanned" in lines
    assert "referenced, not scanned 1" in captured.out
    assert "no eligible checks" not in captured.out
    assert "Python" not in captured.out
    assert "accept" not in captured.out
    assert not (tmp_path / "scripts" / "example.py").exists()


def test_gate_accepts_passing_fence_with_an_include(tmp_path, capsys):
    page = tmp_path / "mixed.md"
    page.write_text(
        "# Mixed\n"
        "\n"
        "```py\n"
        "Usd.Stage.Open()\n"
        "```\n"
        "\n"
        "```{include} notes/venv-table.md\n"
        "```\n",
        encoding="utf-8",
    )
    assert main(["gate", "--page", str(page)]) == 0
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == "accept"
    assert "passed 2, failed 0, skipped 0" in captured.out
    assert "referenced, not scanned 1" in captured.out
    assert "no eligible checks" not in captured.out
    assert "reject" not in captured.out
    assert not (tmp_path / "notes" / "venv-table.md").exists()


def test_gate_accepts_an_assignment_only_fence(capsys):
    page = FIXTURES / "assignment_only.md"
    assert main(["gate", "--page", str(page)]) == 0
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == "accept"
    assert "passed 1, failed 0, skipped 0" in captured.out
    assert "reject" not in captured.out


def test_gate_rejects_a_parsed_fence_when_a_cell_fails(tmp_path, capsys):
    page = tmp_path / "mixed.md"
    page.write_text(
        "# Mixed\n"
        "\n"
        "```python\n"
        "x = 1\n"
        "```\n"
        "\n"
        "```{code-cell}\n"
        'raise RuntimeError("broken cell")\n'
        "```\n",
        encoding="utf-8",
    )
    assert main(["gate", "--page", str(page)]) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == "reject"
    assert "passed 1, failed 1, skipped 0" in captured.out
    assert "broken cell" in captured.out
    assert "accept" not in captured.out


def test_gate_keeps_the_parse_failure_when_an_include_is_present(tmp_path, capsys):
    page = tmp_path / "proposed.md"
    page.write_text(
        "# Proposed\n"
        "\n"
        "```py\n"
        "#usda 1.0\n"
        'def Xform "World"\n'
        "```\n"
        "\n"
        "```{include} notes/table.md\n"
        "```\n",
        encoding="utf-8",
    )
    assert main(["gate", "--page", str(page)]) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == "reject"
    assert "expected '('" in captured.out
    assert "referenced, not scanned 1" in captured.out
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


def test_gate_accepts_a_dict_fragment(capsys):
    page = FIXTURES / "dict_fragment.md"
    assert main(["gate", "--page", str(page)]) == 0
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == "accept"
    assert "passed 2, failed 0, skipped 0" in captured.out
    assert "fragments 1" in captured.out
    assert "reject" not in captured.out


def test_gate_rejects_a_fragment_with_a_missing_symbol(capsys):
    page = FIXTURES / "dict_fragment_missing.md"
    assert main(["gate", "--page", str(page)]) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == "reject"
    assert "passed 1, failed 1, skipped 0" in captured.out
    assert "fragments 1" in captured.out
    assert f"fail {page}:4 Usd.Foo.Bar" in captured.out
    assert "accept" not in captured.out


def test_gate_rejects_an_unclosed_call(capsys):
    page = FIXTURES / "unclosed_call.md"
    assert main(["gate", "--page", str(page)]) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == "reject"
    assert "passed 0, failed 1, skipped 0" in captured.out
    assert "fragments 0" in captured.out
    assert "'(' was never closed" in captured.out
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


def test_gate_pointer_scan_error_is_exit_3(tmp_path, monkeypatch, capsys):
    page = tmp_path / "page.md"
    page.write_text("# Hi\n\n```python\nUsd.Stage.Open()\n```\n", encoding="utf-8")

    def boom(path):
        raise RuntimeError("checker broke")

    monkeypatch.setattr("usd_docs_health.cli.pointer_files", boom)
    assert main(["gate", "--page", str(page)]) == 3
    captured = capsys.readouterr()
    assert "unexpected checker error" in captured.err
    assert "page.md" in captured.err
    assert "checker broke" in captured.err
    assert "accept" not in captured.out
    assert "reject" not in captured.out


@pytest.mark.parametrize(
    "fence",
    ["Usd.Stage.Open()\n", 'def Xform "World"\n'],
    ids=["healthy", "unhealthy"],
)
def test_gate_summary_crash_prints_no_decision(tmp_path, monkeypatch, capsys, fence):
    page = tmp_path / "page.md"
    page.write_text(f"# Hi\n\n```python\n{fence}```\n", encoding="utf-8")

    def boom(findings):
        raise RuntimeError("checker broke")

    monkeypatch.setattr("usd_docs_health.cli.count_fragments", boom)
    assert main(["gate", "--page", str(page)]) == 3
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "unexpected checker error" in captured.err
    assert "page.md" in captured.err
    assert "checker broke" in captured.err


def test_gate_usage_error_is_system_exit():
    with pytest.raises(SystemExit) as raised:
        main(["gate"])
    assert raised.value.code == 2


def test_gate_rejects_a_variant_sets_typo(capsys):
    page = FIXTURES / "usda_variant_sets.md"
    assert main(["gate", "--page", str(page)]) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == "reject"
    assert "passed 0, failed 1, skipped 0" in captured.out
    assert f"fail {page}:5 " in captured.out
    assert "Expected }" in captured.out
    assert "elided 0" in captured.out
    assert "accept" not in captured.out


def test_gate_fail_line_without_a_symbol_has_one_space(capsys):
    page = FIXTURES / "usda_variant_sets.md"
    assert main(["gate", "--page", str(page)]) == 1
    captured = capsys.readouterr()
    assert f"fail {page}:5 Expected }}" in captured.out, captured.out


def test_gate_rejects_a_non_breaking_space(tmp_path, capsys):
    page = tmp_path / "proposed.md"
    page.write_text(
        "# Proposed\n"
        "\n"
        "```usda\n"
        "#usda 1.0\n"
        "\n"
        'def Xform "World"\n'
        "{\n"
        "\u00a0\u00a0  custom int x = 1\n"
        "}\n"
        "```\n",
        encoding="utf-8",
    )
    assert main(["gate", "--page", str(page)]) == 1
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == "reject"
    assert "passed 0, failed 1, skipped 0" in captured.out
    assert "non-breaking space (U+00A0) at line 8" in captured.out
    assert "accept" not in captured.out


def test_gate_rejects_a_page_whose_only_usda_is_elided(capsys):
    page = FIXTURES / "usda_elided.md"
    assert main(["gate", "--page", str(page)]) == 1
    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    assert lines[0] == "reject"
    assert "passed 0, failed 0, skipped 0" in captured.out
    assert "elided, not parsed" in lines
    assert "elided 1" in captured.out
    assert "no eligible checks" not in captured.out
    assert "accept" not in captured.out


def test_gate_names_elided_over_an_include(tmp_path, capsys):
    page = tmp_path / "exercise.md"
    page.write_text(
        "# Exercise\n"
        "\n"
        "```usda\n"
        'def Xform "World"\n'
        "{\n"
        "    ...\n"
        "}\n"
        "```\n"
        "\n"
        "```{include} notes/table.md\n"
        "```\n",
        encoding="utf-8",
    )
    assert main(["gate", "--page", str(page)]) == 1
    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    assert lines[0] == "reject"
    assert "elided, not parsed" in lines
    assert "referenced, not scanned" not in lines
    assert "referenced, not scanned 1" in captured.out
    assert "elided 1" in captured.out
    assert "accept" not in captured.out


def test_gate_accepts_a_relocates_excerpt(capsys):
    page = FIXTURES / "usda_relocates.md"
    assert main(["gate", "--page", str(page)]) == 0
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == "accept"
    assert "passed 1, failed 0, skipped 0" in captured.out
    assert "fragments 1" in captured.out
    assert "elided 0" in captured.out
    assert "reject" not in captured.out
