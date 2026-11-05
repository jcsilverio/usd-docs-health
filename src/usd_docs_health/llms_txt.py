"""llms.txt generated from a check report."""

from usd_docs_health.report import sort_pages_for_table

CHECK_COMMAND = (
    "python -m usd_docs_health check --corpus vendor/learnopenusd "
    "--format json --html page-table.html --llms llms.txt"
)


def render_llms_txt(report: dict) -> str:
    ordered = sort_pages_for_table(report["pages"])
    unhealthy = [row for row in ordered if row["health"] == "unhealthy"]
    incomplete = [row for row in ordered if row["health"] == "incomplete"]
    return (
        "# usd-docs-health\n"
        "\n"
        "> Generated from the check report. "
        "This is not a hosted llms.txt for Learn OpenUSD.\n"
        "\n"
        f"Corpus SHA: `{report['corpus_sha']}`\n"
        "\n"
        f"USD version: `{report['usd_version']}`\n"
        "\n"
        f"Check command: `{CHECK_COMMAND}`\n"
        "\n"
        "## Unhealthy pages\n"
        "\n"
        f"{_page_list(unhealthy)}"
        "\n"
        "## Incomplete pages\n"
        "\n"
        f"{_page_list(incomplete)}"
    )


def _page_list(rows: list[dict]) -> str:
    if not rows:
        return "None.\n"
    return "".join(f"{_page_line(row)}\n" for row in rows)


def _page_line(row: dict) -> str:
    location = row["page"]
    if row["first_line"] is not None:
        location = f"{location}:{row['first_line']}"
    reason = row["first_reason"]
    if reason:
        return f"- {location} {reason}"
    return f"- {location}"
