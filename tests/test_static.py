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


def test_spaced_python_fence_names_create_new():
    findings = check_fences(PAGES / "spaced_python.md")
    assert len(findings) == 2
    parse, symbol = findings
    assert parse.status == "pass", parse
    assert parse.symbol is None
    assert parse.line == 4
    assert parse.reason == ""
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


def test_wrapped_dict_fragment_keeps_the_lesson_line():
    findings = check_fences(PAGES / "dict_fragment.md")
    assert len(findings) == 2
    parse, symbol = findings
    assert parse.status == "pass", parse
    assert parse.symbol is None
    assert parse.line == 4
    assert parse.reason == "fragment, parsed as dict entry"
    assert symbol.status == "pass", symbol
    assert symbol.symbol == "Usd.Stage.Open"
    assert symbol.line == 5
    assert symbol.reason == ""


def test_wrapped_list_fragment_keeps_the_lesson_line():
    findings = check_fences(PAGES / "list_fragment.md")
    assert len(findings) == 2
    parse, symbol = findings
    assert parse.status == "pass", parse
    assert parse.symbol is None
    assert parse.line == 4
    assert parse.reason == "fragment, parsed as list item"
    assert symbol.status == "pass", symbol
    assert symbol.symbol == "Usd.Stage.Open"
    assert symbol.line == 5
    assert symbol.reason == ""


def test_fragment_still_checks_a_missing_symbol_on_the_lesson_line():
    findings = check_fences(PAGES / "dict_fragment_missing.md")
    assert len(findings) == 2
    parse, symbol = findings
    assert parse.status == "pass", parse
    assert parse.symbol is None
    assert parse.line == 4
    assert parse.reason == "fragment, parsed as dict entry"
    assert symbol.status == "fail", symbol
    assert symbol.symbol == "Usd.Foo.Bar"
    assert symbol.line == 4


def test_unclosed_call_keeps_the_original_parse_error():
    findings = check_fences(PAGES / "unclosed_call.md")
    assert len(findings) == 1
    assert findings[0].status == "fail"
    assert findings[0].symbol is None
    assert findings[0].line == 4
    assert findings[0].reason == "'(' was never closed"


def test_indented_tuple_parses_as_dedented():
    page = PAGES / "fragment_py.md"
    findings = check_fences(page)
    assert len(findings) == 1
    assert findings[0].status == "pass", findings[0]
    assert findings[0].symbol is None
    assert findings[0].line == 6
    assert findings[0].reason == "fragment, parsed as dedented"


def test_relocates_line_95_parses_as_dedented():
    page = (
        Path(__file__).resolve().parents[1]
        / "vendor"
        / "learnopenusd"
        / "docs"
        / "creating-composition-arcs"
        / "relocates"
        / "working-with-relocates.md"
    )
    findings = check_fences(page)
    parse = [item for item in findings if item.symbol is None and item.line == 95]
    assert len(parse) == 1
    assert parse[0].status == "pass", parse[0]
    assert parse[0].reason == "fragment, parsed as dedented"
    symbols = [item for item in findings if item.symbol and item.line == 95]
    assert {item.symbol for item in symbols} == {"Sdf.Path", "Sdf.Path.emptyPath"}
    assert all(item.status == "pass" for item in symbols)
    other = [item for item in findings if item.symbol is None and item.line != 95]
    assert other
    assert all(item.status == "pass" and item.reason == "" for item in other)


def test_workstreams_line_92_parses_as_dict_entry():
    page = (
        Path(__file__).resolve().parents[1]
        / "vendor"
        / "learnopenusd"
        / "docs"
        / "asset-structure"
        / "workstreams"
        / "adding-user-workstreams.md"
    )
    findings = check_fences(page)
    parse = [item for item in findings if item.symbol is None and item.line == 92]
    assert len(parse) == 1
    assert parse[0].status == "pass", parse[0]
    assert parse[0].reason == "fragment, parsed as dict entry"
    assert not any(item.symbol and item.line == 92 for item in findings)


def test_references_usda_still_fails():
    page = (
        Path(__file__).resolve().parents[1]
        / "vendor"
        / "learnopenusd"
        / "docs"
        / "composition-basics"
        / "references.md"
    )
    findings = check_fences(page)
    failed = [item for item in findings if item.status == "fail"]
    assert len(failed) == 1
    assert failed[0].symbol is None
    assert failed[0].line == 86
    assert failed[0].reason == "expected '('"
