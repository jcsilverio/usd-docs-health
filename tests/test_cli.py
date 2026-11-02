from usd_docs_health.cli import main


def test_missing_corpus_is_exit_2(tmp_path):
    missing = tmp_path / "missing"
    assert main(["check", "--corpus", str(missing)]) == 2


def test_real_folder_is_exit_2_until_checks_exist(tmp_path):
    assert main(["check", "--corpus", str(tmp_path)]) == 2
