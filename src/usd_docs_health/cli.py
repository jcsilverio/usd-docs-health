"""Command line for usd-docs-health."""

import argparse
import json
import sys
from pathlib import Path

from usd_docs_health.execute import execute_page
from usd_docs_health.static import Finding, check_fences


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

    failed = [item for item in findings if item.status == "fail"]
    passed = [item for item in findings if item.status == "pass"]
    skipped = [item for item in findings if item.status == "skipped"]
    summary = {
        "passed": len(passed),
        "failed": len(failed),
        "skipped": len(skipped),
        "usd2gltf_calls": usd2gltf_calls,
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
        print(f"usd2gltf calls {summary['usd2gltf_calls']}")
        for item in summary["findings"]:
            if item["status"] != "fail":
                continue
            name = item["symbol"] if item["symbol"] else ""
            print(f"fail {item['page']}:{item['line']} {name} {item['reason']}".rstrip())

    return 1 if failed else 0


def _cell_finding(page: Path, status: str, line: int, reason: str) -> Finding:
    return Finding(status=status, symbol=None, line=line, reason=reason, page=str(page))


def _is_page(path: Path) -> bool:
    parts = set(path.parts)
    return "_includes" not in parts and "_build" not in parts


if __name__ == "__main__":
    raise SystemExit(main())
