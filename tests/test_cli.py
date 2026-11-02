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
