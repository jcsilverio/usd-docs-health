"""Command line for usd-docs-health."""

import argparse
import json
import sys
from pathlib import Path

from usd_docs_health.static import check_fences


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="usd-docs-health")
    subcommands = parser.add_subparsers(dest="command", required=True)

    check = subcommands.add_parser("check")
    check.add_argument("--corpus", required=True)
    check.add_argument("--format", choices=("text", "json"), default="text")

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
    findings = []
    for page in pages:
        findings.extend(check_fences(page))

    if not findings:
        print("No ordinary python fences found.", file=sys.stderr)
        return 2

    failed = [item for item in findings if item.status == "fail"]
    passed = [item for item in findings if item.status == "pass"]
    summary = {
        "passed": len(passed),
        "failed": len(failed),
        "skipped": 0,
        "findings": [
            {
                "status": item.status,
                "symbol": item.symbol,
                "line": item.line,
                "reason": item.reason,
                "page": item.page,
            }
            for item in findings
        ],
    }

    if args.format == "json":
        print(json.dumps(summary, indent=2))
    else:
        print(
            f"passed {summary['passed']}, "
            f"failed {summary['failed']}, "
            f"skipped {summary['skipped']}"
        )
        for item in summary["findings"]:
            if item["status"] != "fail":
                continue
            name = item["symbol"] if item["symbol"] else ""
            print(f"fail {item['page']}:{item['line']} {name} {item['reason']}".rstrip())

    return 1 if failed else 0


def _is_page(path: Path) -> bool:
    parts = set(path.parts)
    return "_includes" not in parts and "_build" not in parts


if __name__ == "__main__":
    raise SystemExit(main())
