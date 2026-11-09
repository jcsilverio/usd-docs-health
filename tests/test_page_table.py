from usd_docs_health.page_table import render_page_table
from usd_docs_health.report import (
    build_report,
    count_referenced_not_scanned,
    sort_pages_for_table,
    usd_version_string,
)
from usd_docs_health.static import Finding


def test_page_table_lists_unhealthy_pages_first():
    report = {
        "corpus_sha": "deadbeef",
        "usd_version": "26.11",
        "passed": 2,
        "failed": 1,
        "skipped": 1,
        "referenced_not_scanned": 0,
        "pages": [
            {
                "page": "docs/healthy.md",
                "health": "healthy",
                "passed": 2,
                "failed": 0,
                "skipped": 0,
                "first_reason": "",
                "first_line": None,
            },
            {
                "page": "docs/broken.md",
                "health": "unhealthy",
                "passed": 0,
                "failed": 1,
                "skipped": 0,
                "first_reason": "expected '('",
                "first_line": 12,
            },
            {
                "page": "docs/skipped.md",
                "health": "incomplete",
                "passed": 0,
                "failed": 0,
                "skipped": 1,
                "first_reason": "earlier cell failed",
                "first_line": 20,
            },
        ],
    }
    ordered = [row["page"] for row in sort_pages_for_table(report["pages"])]
    assert ordered == ["docs/broken.md", "docs/skipped.md", "docs/healthy.md"]

    html = render_page_table(report)
    assert html.index("docs/broken.md") < html.index("docs/skipped.md")
    assert html.index("docs/skipped.md") < html.index("docs/healthy.md")
    assert "deadbeef" in html
    assert "docs/broken.md:12" in html
    assert "Referenced, not scanned: 0" in html


def test_build_report_marks_prose_only_page_incomplete(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    page = docs / "prose_only.md"
    page.write_text("# Title\n\nNo fences or cells here.\n", encoding="utf-8")
    report = build_report(tmp_path, [page], [], usd2gltf_calls=0)
    assert report["pages_no_eligible_checks"] == 1
    assert report["referenced_not_scanned"] == 0
    row = report["pages"][0]
    assert row["health"] == "incomplete"
    assert row["first_reason"] == "no eligible checks"
    assert row["referenced_not_scanned"] == 0


def test_build_report_page_health_from_findings(tmp_path):
    page = tmp_path / "docs" / "sample.md"
    page.parent.mkdir()
    page.write_text("```python\nUsd.Stage\n```\n", encoding="utf-8")
    findings = [
        Finding(
            status="pass",
            symbol="Usd.Stage",
            line=2,
            reason="",
            page=str(page),
        )
    ]
    report = build_report(tmp_path, [page], findings, usd2gltf_calls=0)
    row = report["pages"][0]
    assert row["health"] == "healthy"
    assert row["passed"] == 1
    assert row["referenced_not_scanned"] == 0
    assert report["referenced_not_scanned"] == 0


def test_usd_version_string_is_the_pinned_release():
    assert usd_version_string() == "26.11"


def test_count_referenced_not_scanned_ignores_prose_and_option_lines(tmp_path):
    page = tmp_path / "lesson.md"
    page.write_text(
        "# Lesson\n"
        "\n"
        "This lesson includes a literalinclude in the prose.\n"
        "\n"
        "```{include} ./_includes/venv-table.md\n"
        "```\n"
        "\n"
        "    ```{literalinclude} ../exercise_content/example.py\n"
        "    :caption: example.py\n"
        "    :linenos:\n"
        "    ```\n",
        encoding="utf-8",
    )
    assert count_referenced_not_scanned(page) == 2
    assert not (tmp_path / "_includes" / "venv-table.md").exists()
    assert not (tmp_path / "exercise_content" / "example.py").exists()


def test_build_report_marks_include_only_page_referenced_not_scanned(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    prose = docs / "prose.md"
    prose.write_text("# Title\n\nNo fences or cells here.\n", encoding="utf-8")
    included = docs / "included.md"
    included.write_text(
        "# Exercise\n"
        "\n"
        "```{literalinclude} ../exercise.py\n"
        ":caption: exercise.py\n"
        "```\n",
        encoding="utf-8",
    )
    report = build_report(tmp_path, [prose, included], [], usd2gltf_calls=0)
    assert report["referenced_not_scanned"] == 1
    assert report["passed"] == 0
    assert report["failed"] == 0
    assert report["skipped"] == 0
    assert report["pages_no_eligible_checks"] == 1
    rows = {row["page"]: row for row in report["pages"]}
    assert rows[str(prose)]["first_reason"] == "no eligible checks"
    assert rows[str(prose)]["referenced_not_scanned"] == 0
    included_row = rows[str(included)]
    assert included_row["health"] == "incomplete"
    assert included_row["first_reason"] == "referenced, not scanned"
    assert included_row["referenced_not_scanned"] == 1
    assert "Python" not in included_row["first_reason"]
    assert not (tmp_path / "exercise.py").exists()


def test_build_report_keeps_a_passing_page_healthy_when_it_includes_a_file(tmp_path):
    page = tmp_path / "docs" / "mixed.md"
    page.parent.mkdir()
    page.write_text(
        "```python\nUsd.Stage\n```\n\n```{include} note.md\n```\n",
        encoding="utf-8",
    )
    findings = [
        Finding(
            status="pass",
            symbol="Usd.Stage",
            line=2,
            reason="",
            page=str(page),
        )
    ]
    report = build_report(tmp_path, [page], findings, usd2gltf_calls=0)
    row = report["pages"][0]
    assert row["health"] == "healthy"
    assert row["passed"] == 1
    assert row["first_reason"] == ""
    assert row["referenced_not_scanned"] == 1
    assert report["referenced_not_scanned"] == 1
    assert report["pages_no_eligible_checks"] == 0
    assert not (page.parent / "note.md").exists()


def test_build_report_keeps_a_failure_when_the_page_also_includes_a_file(tmp_path):
    page = tmp_path / "docs" / "broken.md"
    page.parent.mkdir()
    page.write_text("```{literalinclude} script.py\n```\n", encoding="utf-8")
    findings = [
        Finding(
            status="fail",
            symbol=None,
            line=4,
            reason="expected '('",
            page=str(page),
        )
    ]
    report = build_report(tmp_path, [page], findings, usd2gltf_calls=0)
    row = report["pages"][0]
    assert row["health"] == "unhealthy"
    assert row["first_reason"] == "expected '('"
    assert row["referenced_not_scanned"] == 1
    assert report["pages_no_eligible_checks"] == 0


def test_build_report_keeps_a_skip_reason_when_the_page_also_includes_a_file(tmp_path):
    page = tmp_path / "docs" / "skipped.md"
    page.parent.mkdir()
    page.write_text("```{include} note.md\n```\n", encoding="utf-8")
    findings = [
        Finding(
            status="skipped",
            symbol=None,
            line=8,
            reason="earlier cell failed",
            page=str(page),
        )
    ]
    report = build_report(tmp_path, [page], findings, usd2gltf_calls=0)
    row = report["pages"][0]
    assert row["health"] == "incomplete"
    assert row["first_reason"] == "earlier cell failed"
    assert row["referenced_not_scanned"] == 1
    assert report["pages_no_eligible_checks"] == 0
