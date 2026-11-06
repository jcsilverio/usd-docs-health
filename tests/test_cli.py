import json
from pathlib import Path

from usd_docs_health.cli import main

FIXTURES = Path(__file__).parent / "fixtures" / "pages"


def test_missing_corpus_is_exit_2(tmp_path):
    missing = tmp_path / "missing"
    assert main(["check", "--corpus", str(missing)]) == 2


def test_folder_without_docs_is_exit_2(tmp_path):
    assert main(["check", "--corpus", str(tmp_path)]) == 2


def _corpus_with(tmp_path, page_name):
    docs = tmp_path / "docs"
    docs.mkdir()
    target = docs / page_name
    target.write_text((FIXTURES / page_name).read_text(encoding="utf-8"), encoding="utf-8")
    return tmp_path


def test_valid_page_is_exit_0(tmp_path):
    corpus = _corpus_with(tmp_path, "valid_dotted_name.md")
    assert main(["check", "--corpus", str(corpus)]) == 0


def test_missing_symbol_page_is_exit_1(tmp_path):
    corpus = _corpus_with(tmp_path, "missing_symbol.md")
    assert main(["check", "--corpus", str(corpus)]) == 1


def test_not_python_page_is_exit_1(tmp_path):
    corpus = _corpus_with(tmp_path, "not_python.md")
    assert main(["check", "--corpus", str(corpus)]) == 1


def test_unexpected_page_error_is_exit_3(tmp_path, monkeypatch, capsys):
    corpus = _corpus_with(tmp_path, "valid_dotted_name.md")

    def boom(page):
        raise RuntimeError("checker broke")

    monkeypatch.setattr("usd_docs_health.cli.check_fences", boom)
    assert main(["check", "--corpus", str(corpus)]) == 3
    captured = capsys.readouterr()
    assert "unexpected checker error" in captured.err
    assert "valid_dotted_name.md" in captured.err
    assert "checker broke" in captured.err
    assert "passed " not in captured.out
    assert "fail " not in captured.out


def test_passing_cell_is_exit_0(tmp_path, capsys):
    corpus = _corpus_with(tmp_path, "cell_passes.md")
    assert main(["check", "--corpus", str(corpus)]) == 0
    captured = capsys.readouterr()
    assert "passed 1, failed 0, skipped 0" in captured.out
    assert "usd2gltf calls 0" in captured.out


def test_failing_cell_is_exit_1(tmp_path, capsys):
    corpus = _corpus_with(tmp_path, "cell_fails.md")
    assert main(["check", "--corpus", str(corpus)]) == 1
    captured = capsys.readouterr()
    assert "passed 0, failed 1, skipped 0" in captured.out
    assert "broken cell" in captured.out


def test_lfs_pointer_needed_by_a_cell_is_exit_2(tmp_path, capsys):
    docs = tmp_path / "docs"
    docs.mkdir()
    for name in ("cell_pointer.md", "cell_pointer_asset.usda"):
        (docs / name).write_text(
            (FIXTURES / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    assert main(["check", "--corpus", str(tmp_path)]) == 2
    captured = capsys.readouterr()
    assert "LFS pointer file:" in captured.err
    assert "cell_pointer_asset.usda" in captured.err
    assert "fail " not in captured.out


def test_relative_corpus_path_can_import_src(tmp_path, monkeypatch, capsys):
    corpus = tmp_path / "vendor" / "learnopenusd"
    docs = corpus / "docs"
    src = corpus / "src"
    docs.mkdir(parents=True)
    src.mkdir()
    (src / "tinybox.py").write_text("LABEL = 'World'\n", encoding="utf-8")
    (docs / "cell_tinybox.md").write_text(
        "# Cell imports a corpus module\n"
        "\n"
        "```{code-cell}\n"
        "import tinybox\n"
        "print(tinybox.LABEL)\n"
        "```\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    corpus_arg = "vendor/learnopenusd"
    assert not Path(corpus_arg).is_absolute()
    assert main(["check", "--corpus", corpus_arg]) == 0
    captured = capsys.readouterr()
    assert "passed 1, failed 0, skipped 0" in captured.out


def test_check_counts_includes_without_scanning_them(tmp_path, capsys):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "valid_dotted_name.md").write_text(
        "# Valid\n"
        "\n"
        "```python\n"
        "Usd.Stage.Open()\n"
        "```\n"
        "\n"
        "```{include} ./_includes/note.md\n"
        "```\n",
        encoding="utf-8",
    )
    (docs / "included_only.md").write_text(
        "# Exercise\n"
        "\n"
        "```{literalinclude} ../exercise_content/example.py\n"
        ":caption: example.py\n"
        ":linenos:\n"
        "```\n",
        encoding="utf-8",
    )
    (docs / "prose.md").write_text(
        "# Title\n\nThis lesson includes practical examples.\n",
        encoding="utf-8",
    )
    html_path = tmp_path / "page-table.html"
    llms_path = tmp_path / "llms.txt"
    assert (
        main(
            [
                "check",
                "--corpus",
                str(tmp_path),
                "--format",
                "json",
                "--html",
                str(html_path),
                "--llms",
                str(llms_path),
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["passed"] == 1
    assert report["failed"] == 0
    assert report["skipped"] == 0
    assert report["referenced_not_scanned"] == 2
    assert report["pages_no_eligible_checks"] == 1
    rows = {Path(row["page"]).name: row for row in report["pages"]}
    assert rows["valid_dotted_name.md"]["health"] == "healthy"
    assert rows["valid_dotted_name.md"]["referenced_not_scanned"] == 1
    assert rows["included_only.md"]["health"] == "incomplete"
    assert rows["included_only.md"]["first_reason"] == "referenced, not scanned"
    assert "Python" not in rows["included_only.md"]["first_reason"]
    assert rows["prose.md"]["first_reason"] == "no eligible checks"
    html = html_path.read_text(encoding="utf-8")
    assert "Referenced, not scanned: 2" in html
    assert "referenced, not scanned" in html
    llms = llms_path.read_text(encoding="utf-8")
    assert "included_only.md referenced, not scanned" in llms
    assert "prose.md no eligible checks" in llms
    assert "valid_dotted_name.md" not in llms
    assert not (docs / "_includes" / "note.md").exists()
    assert not (tmp_path / "exercise_content" / "example.py").exists()

    assert main(["check", "--corpus", str(tmp_path)]) == 0
    text = capsys.readouterr()
    assert "passed 1, failed 0, skipped 0" in text.out
    assert "referenced, not scanned 2" in text.out


def test_unreferenced_lfs_pointer_is_exit_0(tmp_path):
    corpus = _corpus_with(tmp_path, "valid_dotted_name.md")
    pointer = corpus / "docs" / "cell_pointer_asset.usda"
    pointer.write_text(
        (FIXTURES / "cell_pointer_asset.usda").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    assert main(["check", "--corpus", str(corpus)]) == 0
