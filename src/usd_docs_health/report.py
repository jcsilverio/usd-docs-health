"""Build per-page JSON reports from check findings."""

import subprocess
from collections import defaultdict
from pathlib import Path

from pxr import Usd

from usd_docs_health.static import Finding

HEALTH_ORDER = {"unhealthy": 0, "incomplete": 1, "healthy": 2}


def corpus_sha(corpus: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(corpus), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return completed.stdout.strip()


def usd_version_string() -> str:
    major, minor, _patch = Usd.GetVersion()
    return f"{major}.{minor}"


def build_report(
    corpus: Path,
    pages: list[Path],
    findings: list[Finding],
    usd2gltf_calls: int,
) -> dict:
    by_page: dict[str, list[Finding]] = defaultdict(list)
    for item in findings:
        by_page[item.page].append(item)

    page_rows = []
    no_eligible = 0
    for page in pages:
        page_key = str(page)
        row = summarize_page(page_key, by_page.get(page_key, []))
        if row["health"] == "incomplete" and row["first_reason"] == "no eligible checks":
            no_eligible += 1
        page_rows.append(row)

    passed = sum(1 for item in findings if item.status == "pass")
    failed = sum(1 for item in findings if item.status == "fail")
    skipped = sum(1 for item in findings if item.status == "skipped")

    return {
        "corpus_sha": corpus_sha(corpus),
        "usd_version": usd_version_string(),
        "pages_discovered": len(pages),
        "checks_discovered": len(findings),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "usd2gltf_calls": usd2gltf_calls,
        "pages_no_eligible_checks": no_eligible,
        "pages": page_rows,
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


def summarize_page(page: str, findings: list[Finding]) -> dict:
    if not findings:
        return {
            "page": page,
            "health": "incomplete",
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "first_reason": "no eligible checks",
            "first_line": None,
        }

    passed = sum(1 for item in findings if item.status == "pass")
    failed = sum(1 for item in findings if item.status == "fail")
    skipped = sum(1 for item in findings if item.status == "skipped")

    if failed:
        health = "unhealthy"
        first = min(
            (item for item in findings if item.status == "fail"),
            key=lambda item: item.line,
        )
    elif skipped:
        health = "incomplete"
        first = min(
            (item for item in findings if item.status == "skipped"),
            key=lambda item: item.line,
        )
    else:
        health = "healthy"
        first = None

    if first is None:
        return {
            "page": page,
            "health": health,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "first_reason": "",
            "first_line": None,
        }

    return {
        "page": page,
        "health": health,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "first_reason": first.reason,
        "first_line": first.line,
    }


def sort_pages_for_table(pages: list[dict]) -> list[dict]:
    return sorted(
        pages,
        key=lambda row: (
            HEALTH_ORDER[row["health"]],
            -row["failed"],
            -row["skipped"],
            row["page"],
        ),
    )
