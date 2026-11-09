"""Command line for usd-docs-health."""

import argparse
import json
import sys
import traceback
from pathlib import Path

from usd_docs_health.execute import execute_page, pointer_files
from usd_docs_health.llms_txt import render_llms_txt
from usd_docs_health.page_table import render_page_table
from usd_docs_health.report import (
    build_report,
    count_fragments,
    count_referenced_not_scanned,
    summarize_page,
)
from usd_docs_health.static import Finding, check_fences


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="usd-docs-health")
    subcommands = parser.add_subparsers(dest="command", required=True)

    check = subcommands.add_parser("check")
    check.add_argument("--corpus", required=True)
    check.add_argument("--format", choices=("text", "json"), default="text")
    check.add_argument(
        "--html",
        metavar="PATH",
        help="Write a static page table HTML file generated from the check results",
    )
    check.add_argument(
        "--llms",
        metavar="PATH",
        help="Write an llms.txt file generated from the check results",
    )

    gate = subcommands.add_parser("gate")
    gate.add_argument("--page", required=True)
    gate.add_argument("--corpus")

    args = parser.parse_args(argv)
    if args.command == "gate":
        corpus = None if args.corpus is None else Path(args.corpus)
        return _gate(Path(args.page), corpus)
    return _check(args)


def _unexpected_error(page: Path | None) -> int:
    if page is None:
        print("unexpected checker error", file=sys.stderr)
    else:
        print(f"unexpected checker error: {page}", file=sys.stderr)
    traceback.print_exc()
    return 3


def _check(args) -> int:
    page_in_progress = None
    try:
        corpus = Path(args.corpus)
        if not corpus.is_dir():
            print(f"corpus not found: {corpus}", file=sys.stderr)
            return 2

        docs = corpus / "docs"
        if not docs.is_dir():
            print(f"docs directory not found: {docs}", file=sys.stderr)
            return 2

        pages = sorted(path for path in docs.rglob("*.md") if _is_page(path))
        pointers = []
        for page in pages:
            page_in_progress = page
            pointers.extend(pointer_files(page))
            page_in_progress = None
        if pointers:
            for path in pointers:
                print(f"LFS pointer file: {path}", file=sys.stderr)
            return 2

        python_path = _corpus_src(corpus)
        findings = []
        usd2gltf_calls = 0
        for page in pages:
            page_in_progress = page
            findings.extend(check_fences(page))
            executed = execute_page(page, python_path=python_path)
            usd2gltf_calls += executed.usd2gltf_calls
            for item in executed:
                findings.append(
                    _cell_finding(page, item.status, item.line, item.reason)
                )
            page_in_progress = None

        if not findings:
            print("No ordinary python fences or code cells found.", file=sys.stderr)
            return 2

        report = build_report(corpus, pages, findings, usd2gltf_calls)
        failed = report["failed"]

        if args.html:
            html_path = Path(args.html)
            html_path.write_text(render_page_table(report), encoding="utf-8")

        if args.llms:
            llms_path = Path(args.llms)
            llms_path.write_text(render_llms_txt(report), encoding="utf-8")

        if args.format == "json":
            print(json.dumps(report, indent=2))
        else:
            print(
                f"passed {report['passed']}, "
                f"failed {report['failed']}, "
                f"skipped {report['skipped']}"
            )
            print(f"usd2gltf calls {report['usd2gltf_calls']}")
            print(f"fragments {report['fragments']}")
            print(f"referenced, not scanned {report['referenced_not_scanned']}")
            for item in report["findings"]:
                if item["status"] != "fail":
                    continue
                name = item["symbol"] if item["symbol"] else ""
                print(
                    f"fail {item['page']}:{item['line']} {name} {item['reason']}".rstrip()
                )

        return 1 if failed else 0
    except Exception:
        return _unexpected_error(page_in_progress)


def _gate(page: Path, corpus: Path | None) -> int:
    try:
        if not page.is_file():
            print(f"page not found: {page}", file=sys.stderr)
            return 2
        if corpus is not None and not corpus.is_dir():
            print(f"corpus not found: {corpus}", file=sys.stderr)
            return 2

        pointers = pointer_files(page)
        if pointers:
            for path in pointers:
                print(f"LFS pointer file: {path}", file=sys.stderr)
            return 2

        python_path = _corpus_src(corpus)
        findings = list(check_fences(page))
        executed = execute_page(page, python_path=python_path)
        usd2gltf_calls = executed.usd2gltf_calls
        for item in executed:
            findings.append(_cell_finding(page, item.status, item.line, item.reason))
        referenced = count_referenced_not_scanned(page)
        row = summarize_page(str(page), findings, referenced)

        decision = "accept" if row["health"] == "healthy" else "reject"
        print(decision)
        print(
            f"passed {row['passed']}, failed {row['failed']}, skipped {row['skipped']}"
        )
        if decision == "reject":
            for line in _gate_reasons(findings, referenced):
                print(line)
        print(f"usd2gltf calls {usd2gltf_calls}")
        print(f"fragments {count_fragments(findings)}")
        print(f"referenced, not scanned {referenced}")
        return 0 if decision == "accept" else 1
    except Exception:
        return _unexpected_error(page)


def _gate_reasons(findings: list[Finding], referenced_not_scanned: int) -> list[str]:
    if not findings:
        if referenced_not_scanned:
            return ["referenced, not scanned"]
        return ["no eligible checks"]
    lines = []
    for item in sorted(findings, key=lambda item: (item.line, item.status)):
        if item.status == "pass":
            continue
        if item.status == "fail":
            name = item.symbol if item.symbol else ""
            lines.append(
                f"fail {item.page}:{item.line} {name} {item.reason}".rstrip()
            )
        else:
            lines.append(f"skipped {item.page}:{item.line} {item.reason}".rstrip())
    if lines:
        return lines
    return ["no eligible checks"]


def _corpus_src(corpus: Path | None) -> Path | None:
    if corpus is None:
        return None
    python_path = corpus / "src"
    if python_path.is_dir():
        return python_path
    return None


def _cell_finding(page: Path, status: str, line: int, reason: str) -> Finding:
    return Finding(status=status, symbol=None, line=line, reason=reason, page=str(page))


def _is_page(path: Path) -> bool:
    parts = set(path.parts)
    return "_includes" not in parts and "_build" not in parts


if __name__ == "__main__":
    raise SystemExit(main())
