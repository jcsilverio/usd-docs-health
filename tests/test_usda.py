from pathlib import Path

from usd_docs_health.usda import check_usda

PAGES = Path(__file__).parent / "fixtures" / "pages"
CASES = Path(__file__).parent / "fixtures" / "known_bad"
NBSP = "\u00a0"


def _usda_page(tmp_path: Path, *body: str) -> Path:
    """Write a page with one usda fence. The first body line is line 4."""
    page = tmp_path / "page.md"
    page.write_text(
        "# Page\n\n```usda\n" + "\n".join(body) + "\n```\n",
        encoding="utf-8",
    )
    return page


def test_usda_fence_passes():
    findings = check_usda(PAGES / "usda_fence.md")
    assert len(findings) == 1
    assert findings[0].status == "pass", findings[0]
    assert findings[0].symbol is None
    assert findings[0].line == 4
    assert findings[0].reason == ""
    assert findings.elided == 0


def test_code_block_option_lines_are_not_parsed():
    findings = check_usda(PAGES / "usda_code_block.md")
    assert len(findings) == 1
    assert findings[0].status == "pass", findings[0]
    assert findings[0].line == 7
    assert findings[0].reason == ""


def test_spaced_usda_opener_counts():
    findings = check_usda(PAGES / "usda_spaced.md")
    assert len(findings) == 1
    assert findings[0].status == "pass", findings[0]
    assert findings[0].line == 4


def test_missing_header_is_added():
    findings = check_usda(PAGES / "usda_no_header.md")
    assert len(findings) == 1
    assert findings[0].status == "pass", findings[0]
    assert findings[0].line == 4
    assert findings[0].reason == ""


def test_blank_line_before_the_header_is_not_part_of_the_example():
    findings = check_usda(PAGES / "usda_blank_first.md")
    assert len(findings) == 1
    assert findings[0].status == "pass", findings[0]
    assert findings[0].line == 5
    assert findings[0].reason == ""


def test_variant_sets_typo_fails_on_the_lesson_line():
    findings = check_usda(PAGES / "usda_variant_sets.md")
    assert len(findings) == 1
    assert findings[0].status == "fail", findings[0]
    assert findings[0].symbol is None
    assert findings[0].line == 5
    assert "Expected }" in findings[0].reason


def test_color3f_array_fails():
    findings = check_usda(PAGES / "usda_color3f.md")
    assert len(findings) == 1
    assert findings[0].status == "fail", findings[0]
    assert findings[0].line == 8
    assert "Type name missing [] for shaped value" in findings[0].reason


def test_rotatex_reason_lists_both_messages_in_order():
    findings = check_usda(PAGES / "usda_rotatex.md")
    assert len(findings) == 1
    assert findings[0].status == "fail", findings[0]
    assert findings[0].line == 8
    reason = findings[0].reason
    first = "Not enough values to parse value of type Vec3d"
    last = "Error parsing simple value"
    assert first in reason and last in reason, reason
    assert reason.index(first) < reason.index(last)


def test_elided_example_adds_no_finding():
    findings = check_usda(PAGES / "usda_elided.md")
    assert list(findings) == []
    assert findings.elided == 1


def test_dots_inside_a_string_are_not_elided():
    findings = check_usda(PAGES / "usda_dots_in_string.md")
    assert len(findings) == 1
    assert findings[0].status == "fail", findings[0]
    assert findings[0].line == 8
    assert "Expected }" in findings[0].reason
    assert findings.elided == 0


def test_relocates_excerpt_parses_as_layer_metadata():
    findings = check_usda(PAGES / "usda_relocates.md")
    assert len(findings) == 1
    assert findings[0].status == "pass", findings[0]
    assert findings[0].line == 4
    assert findings[0].reason == "fragment, parsed as layer metadata"
    assert findings.elided == 0


def test_non_breaking_space_fails_with_its_own_reason(tmp_path):
    page = _usda_page(
        tmp_path,
        "#usda 1.0",
        "",
        'def Xform "World"',
        "{",
        NBSP + NBSP + "  custom int x = 1",
        "}",
    )
    findings = check_usda(page)
    assert len(findings) == 1
    assert findings[0].status == "fail", findings[0]
    assert findings[0].line == 8
    assert findings[0].reason == "non-breaking space (U+00A0) at line 8"


def test_non_breaking_space_does_not_hide_a_second_bug(tmp_path):
    page = _usda_page(
        tmp_path,
        "#usda 1.0",
        "",
        'def Mesh "Box"',
        "{",
        NBSP + NBSP + "  custom int x = 1",
        "    color3f primvars:displayColor = [(1, 0, 0)]",
        "}",
    )
    findings = check_usda(page)
    assert len(findings) == 1
    assert findings[0].status == "fail", findings[0]
    assert findings[0].line == 8
    reason = findings[0].reason
    assert reason.startswith("non-breaking space (U+00A0) at line 8"), reason
    assert "Type name missing [] for shaped value" in reason
    assert "line 9" in reason


def test_non_breaking_space_in_an_elided_example_still_fails(tmp_path):
    page = _usda_page(
        tmp_path,
        'def Xform "World"',
        "{",
        NBSP + NBSP + "  ...",
        "}",
    )
    findings = check_usda(page)
    assert len(findings) == 1
    assert findings[0].status == "fail", findings[0]
    assert findings[0].line == 6
    assert findings[0].reason == "non-breaking space (U+00A0) at line 6"
    assert findings.elided == 1


def test_usda_in_a_python_fence_is_not_a_usda_example():
    findings = check_usda(CASES / "usda_python.md")
    assert list(findings) == []
    assert findings.elided == 0
