from pathlib import Path

from usd_docs_health.static import check_fences

PAGES = Path(__file__).parent / "fixtures" / "pages"


def test_valid_dotted_name_passes():
    findings = check_fences(PAGES / "valid_dotted_name.md")
    assert len(findings) == 1
    assert findings[0].status == "pass", findings[0]
    assert findings[0].symbol == "Usd.Stage.Open"
    assert findings[0].line == 4


def test_missing_symbol_fails():
    findings = check_fences(PAGES / "missing_symbol.md")
    assert len(findings) == 1
    assert findings[0].status == "fail"
    assert findings[0].symbol == "Usd.Foo.Bar"
    assert findings[0].line == 4


def test_not_python_fails_with_parse_error():
    findings = check_fences(PAGES / "not_python.md")
    assert len(findings) == 1
    assert findings[0].status == "fail"
    assert findings[0].symbol is None
    assert findings[0].line == 6
    assert findings[0].reason == "expected '('"


def test_py_fence_names_create_new():
    findings = check_fences(PAGES / "py_fence.md")
    assert len(findings) == 1
    assert findings[0].status == "pass", findings[0]
    assert findings[0].symbol == "Usd.Stage.CreateNew"
    assert findings[0].line == 4


def test_other_labels_stay_closed():
    findings = check_fences(PAGES / "closed_fences.md")
    assert findings == []
