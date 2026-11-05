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


def test_unreferenced_lfs_pointer_is_exit_0(tmp_path):
    corpus = _corpus_with(tmp_path, "valid_dotted_name.md")
    pointer = corpus / "docs" / "cell_pointer_asset.usda"
    pointer.write_text(
        (FIXTURES / "cell_pointer_asset.usda").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    assert main(["check", "--corpus", str(corpus)]) == 0
