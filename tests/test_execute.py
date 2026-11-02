from pathlib import Path

from usd_docs_health.execute import execute_page

CORPUS_SRC = Path(__file__).parents[1] / "vendor" / "learnopenusd" / "src"

PAGES = Path(__file__).parent / "fixtures" / "pages"


def test_cell_passes():
    results = execute_page(PAGES / "cell_passes.md")
    assert len(results) == 1
    assert results[0].status == "pass"
    assert results[0].line == 4


def test_cell_fails():
    results = execute_page(PAGES / "cell_fails.md")
    assert len(results) == 1
    assert results[0].status == "fail"
    assert results[0].line == 4
    assert results[0].reason == "broken cell"


def test_cell_depends():
    results = execute_page(PAGES / "cell_depends.md")
    assert len(results) == 2
    assert [result.status for result in results] == ["pass", "pass"]
    assert [result.line for result in results] == [4, 8]


def test_cell_skipped():
    results = execute_page(PAGES / "cell_skipped.md")
    assert len(results) == 2
    assert results[0].status == "fail"
    assert results[0].line == 4
    assert results[0].reason == "broken cell"
    assert results[1].status == "skipped"
    assert results[1].line == 8
    assert results[1].reason == "earlier cell failed"


def test_cell_timeout():
    results = execute_page(PAGES / "cell_timeout.md", timeout_seconds=1)
    assert len(results) == 2
    assert results[0].status == "fail"
    assert results[0].line == 4
    assert results[0].reason == "cell timed out"
    assert results[1].status == "skipped"
    assert results[1].line == 9
    assert results[1].reason == "earlier cell failed"

def test_cell_prim_range():
    results = execute_page(PAGES / "cell_prim_range.md")
    assert len(results) == 1
    assert results[0].status == "fail"
    assert results[0].line == 4
    assert results[0].reason == "name 'prim_range' is not defined"

def test_cell_hidden():
    results = execute_page(PAGES / "cell_hidden.md")
    assert len(results) == 2
    assert [result.status for result in results] == ["pass", "pass"]
    assert [result.line for result in results] == [6, 10]

def test_cell_neighbor():
    results = execute_page(PAGES / "cell_neighbor.md")
    assert len(results) == 1
    assert results[0].status == "pass"
    assert results[0].line == 4

def test_cell_imports_lousd():
    results = execute_page(PAGES / "cell_lousd.md", python_path=CORPUS_SRC)
    assert len(results) == 1
    assert results[0].status == "pass"
    assert results[0].line == 4

def test_cell_writes_stage_outside_fixtures():
    written = PAGES / "made_in_temp.usda"
    results = execute_page(PAGES / "cell_write_stage.md", python_path=CORPUS_SRC)
    assert len(results) == 1
    assert results[0].status == "pass"
    assert results[0].line == 4
    assert not written.exists()


def test_cell_display_intercepts_usd2gltf():
    results = execute_page(PAGES / "cell_display.md", python_path=CORPUS_SRC)
    assert len(results) == 1
    assert results[0].status == "pass"
    assert results[0].line == 4
    assert results.usd2gltf_calls == 1


def test_cell_reads_file_outside_its_folder(tmp_path):
    docs = tmp_path / "docs"
    lesson = docs / "lesson"
    exercise = docs / "exercise_content"
    lesson.mkdir(parents=True)
    exercise.mkdir()
    (lesson / "cell_parent.md").write_text(
        (PAGES / "cell_parent.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (exercise / "cell_parent_asset.txt").write_text(
        (PAGES / "cell_parent_asset.txt").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    results = execute_page(lesson / "cell_parent.md")
    assert len(results) == 1
    assert results[0].status == "pass"
    assert results[0].line == 4
