from pathlib import Path

from usd_docs_health.cli import main
from usd_docs_health.llms_txt import CHECK_COMMAND, render_llms_txt

FIXTURES = Path(__file__).parent / "fixtures" / "pages"
ROOT = Path(__file__).resolve().parents[1]


def _row(page, health, reason, line, failed=0, skipped=0):
    return {
        "page": page,
        "health": health,
        "passed": 0,
        "failed": failed,
        "skipped": skipped,
        "first_reason": reason,
        "first_line": line,
    }


def test_llms_txt_lists_sha_version_command_and_problem_pages():
    report = {
        "corpus_sha": "deadbeef",
        "usd_version": "26.11",
        "pages": [
            _row("docs/healthy.md", "healthy", "", None),
            _row("docs/minor.md", "unhealthy", "missing symbol", 2, failed=1),
            _row("docs/worse.md", "unhealthy", "expected '('", 4, failed=3),
            _row("docs/prose.md", "incomplete", "no eligible checks", None),
        ],
    }
    text = render_llms_txt(report)
    assert "Corpus SHA: `deadbeef`" in text
    assert "USD version: `26.11`" in text
    assert f"Check command: `{CHECK_COMMAND}`" in text
    assert "docs/healthy.md" not in text
    assert text.index("docs/worse.md:4 expected '('") < text.index(
        "docs/minor.md:2 missing symbol"
    )
    assert text.index("docs/minor.md:2 missing symbol") < text.index(
        "## Incomplete pages"
    )
    assert "docs/prose.md no eligible checks" in text.split("## Incomplete pages", 1)[1]


def test_llms_txt_says_none_when_a_section_is_empty():
    report = {
        "corpus_sha": "abc",
        "usd_version": "26.11",
        "pages": [_row("docs/prose.md", "incomplete", "no eligible checks", None)],
    }
    text = render_llms_txt(report)
    unhealthy = text.split("## Unhealthy pages", 1)[1].split("## Incomplete pages", 1)[0]
    assert "None." in unhealthy
    assert "docs/prose.md" not in unhealthy


def test_check_writes_llms_txt(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    for name in ("not_python.md", "valid_dotted_name.md"):
        (docs / name).write_text((FIXTURES / name).read_text(encoding="utf-8"), encoding="utf-8")
    (docs / "prose.md").write_text("# Title\n\nNo fences or cells here.\n", encoding="utf-8")
    destination = tmp_path / "out" / "llms.txt"
    destination.parent.mkdir()
    code = main(["check", "--corpus", str(tmp_path), "--llms", str(destination)])
    assert code == 1
    text = destination.read_text(encoding="utf-8")
    assert "not_python.md" in text
    assert "expected '('" in text
    assert "prose.md no eligible checks" in text
    assert "valid_dotted_name.md" not in text
    assert "USD version: `26.11`" in text
    assert CHECK_COMMAND in text


def test_agents_md_and_readme_point_at_the_check_command():
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert CHECK_COMMAND in agents
    assert CHECK_COMMAND in readme
    assert CHECK_COMMAND in workflow
    assert "path: llms.txt" in workflow
    assert "exit code 0 or 1" in agents
    assert "does not mean every page is healthy" in agents
