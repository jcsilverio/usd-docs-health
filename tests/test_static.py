from pathlib import Path

from usd_docs_health.static import check_fences

PAGES = Path(__file__).parent / "fixtures" / "pages"


def test_valid_dotted_name_passes():
    findings = check_fences(PAGES / "valid_dotted_name.md")
    assert len(findings) == 2
    parse, symbol = findings
    assert parse.status == "pass", parse
    assert parse.symbol is None
    assert parse.line == 4
    assert parse.reason == ""
    assert symbol.status == "pass", symbol
    assert symbol.symbol == "Usd.Stage.Open"
    assert symbol.line == 4


def test_missing_symbol_fails():
    findings = check_fences(PAGES / "missing_symbol.md")
    assert len(findings) == 2
    parse, symbol = findings
    assert parse.status == "pass"
    assert parse.symbol is None
    assert symbol.status == "fail"
    assert symbol.symbol == "Usd.Foo.Bar"
    assert symbol.line == 4


def test_not_python_fails_with_parse_error():
    findings = check_fences(PAGES / "not_python.md")
    assert len(findings) == 1
    assert findings[0].status == "fail"
    assert findings[0].symbol is None
    assert findings[0].line == 6
    assert findings[0].reason == "expected '('"


def test_py_fence_names_create_new():
    findings = check_fences(PAGES / "py_fence.md")
    assert len(findings) == 2
    parse, symbol = findings
    assert parse.status == "pass", parse
    assert parse.symbol is None
    assert symbol.status == "pass", symbol
    assert symbol.symbol == "Usd.Stage.CreateNew"
    assert symbol.line == 4


def test_assignment_only_fence_is_a_parse_pass():
    findings = check_fences(PAGES / "assignment_only.md")
    assert len(findings) == 1
    assert findings[0].status == "pass", findings[0]
    assert findings[0].symbol is None
    assert findings[0].line == 4
    assert findings[0].reason == ""


def test_two_symbols_add_one_finding_each():
    findings = check_fences(PAGES / "two_symbols.md")
    assert len(findings) == 3
    parse = [item for item in findings if item.symbol is None]
    assert len(parse) == 1
    assert parse[0].status == "pass"
    assert parse[0].line == 4
    named = {item.symbol: item for item in findings if item.symbol}
    assert set(named) == {"Usd.Stage.Open", "Usd.Stage.CreateNew"}
    assert named["Usd.Stage.Open"].status == "pass"
    assert named["Usd.Stage.Open"].line == 4
    assert named["Usd.Stage.CreateNew"].status == "pass"
    assert named["Usd.Stage.CreateNew"].line == 5


def test_other_labels_stay_closed():
    findings = check_fences(PAGES / "closed_fences.md")
    assert findings == []
