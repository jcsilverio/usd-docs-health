"""Command line for usd-docs-health."""

import argparse
import json
import sys
from pathlib import Path

from usd_docs_health.execute import execute_page, pointer_files
from usd_docs_health.page_table import render_page_table
from usd_docs_health.report import build_report
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

    args = parser.parse_args(argv)
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
        pointers.extend(pointer_files(page))
    if pointers:
        for path in pointers:
            print(f"LFS pointer file: {path}", file=sys.stderr)
        return 2

    python_path = corpus / "src"
    if not python_path.is_dir():
        python_path = None

    findings = []
    usd2gltf_calls = 0
    for page in pages:
        findings.extend(check_fences(page))
        executed = execute_page(page, python_path=python_path)
        usd2gltf_calls += executed.usd2gltf_calls
        for item in executed:
            findings.append(
                _cell_finding(page, item.status, item.line, item.reason)
            )

    if not findings:
        print("No ordinary python fences or code cells found.", file=sys.stderr)
        return 2

    report = build_report(corpus, pages, findings, usd2gltf_calls)
    failed = report["failed"]

    if args.html:
        html_path = Path(args.html)
        html_path.write_text(render_page_table(report), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(
            f"passed {report['passed']}, "
            f"failed {report['failed']}, "
            f"skipped {report['skipped']}"
        )
        print(f"usd2gltf calls {report['usd2gltf_calls']}")
        for item in report["findings"]:
            if item["status"] != "fail":
                continue
            name = item["symbol"] if item["symbol"] else ""
            print(
                f"fail {item['page']}:{item['line']} {name} {item['reason']}".rstrip()
            )

    return 1 if failed else 0


def _cell_finding(page: Path, status: str, line: int, reason: str) -> Finding:
    return Finding(status=status, symbol=None, line=line, reason=reason, page=str(page))


def _is_page(path: Path) -> bool:
    parts = set(path.parts)
    return "_includes" not in parts and "_build" not in parts


if __name__ == "__main__":
    raise SystemExit(main())
