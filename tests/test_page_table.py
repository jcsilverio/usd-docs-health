from usd_docs_health.page_table import render_page_table
from usd_docs_health.report import build_report, sort_pages_for_table, usd_version_string
from usd_docs_health.static import Finding


def test_page_table_lists_unhealthy_pages_first():
    report = {
        "corpus_sha": "deadbeef",
        "usd_version": "26.11",
        "passed": 2,
        "failed": 1,
        "skipped": 1,
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


def test_build_report_marks_prose_only_page_incomplete(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    page = docs / "prose_only.md"
    page.write_text("# Title\n\nNo fences or cells here.\n", encoding="utf-8")
    report = build_report(tmp_path, [page], [], usd2gltf_calls=0)
    assert report["pages_no_eligible_checks"] == 1
    row = report["pages"][0]
    assert row["health"] == "incomplete"
    assert row["first_reason"] == "no eligible checks"


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


def test_usd_version_string_is_the_pinned_release():
    assert usd_version_string() == "26.11"
