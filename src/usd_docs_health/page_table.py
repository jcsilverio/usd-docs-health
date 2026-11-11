"""Static HTML page table from a check report."""

import html

from usd_docs_health.report import sort_pages_for_table


def render_page_table(report: dict) -> str:
    rows = sort_pages_for_table(report["pages"])
    body_rows = []
    for row in rows:
        location = ""
        if row["first_line"] is not None:
            location = f"{row['page']}:{row['first_line']}"
        body_rows.append(
            "<tr>"
            f"<td>{html.escape(row['health'])}</td>"
            f"<td>{html.escape(row['page'])}</td>"
            f"<td>{row['failed']}</td>"
            f"<td>{row['skipped']}</td>"
            f"<td>{html.escape(row['first_reason'])}</td>"
            f"<td>{html.escape(location)}</td>"
            "</tr>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Learn OpenUSD static page table</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 1.5rem; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 0.35rem 0.5rem; text-align: left; vertical-align: top; }}
    th {{ background: #f4f4f4; }}
    .meta {{ margin-bottom: 1rem; }}
  </style>
</head>
<body>
  <h1>Static page table</h1>
  <p class="meta">Generated from the check results. This is not a hosted dashboard.</p>
  <p class="meta">
    Corpus SHA: <code>{html.escape(report['corpus_sha'])}</code><br>
    USD version: <code>{html.escape(report['usd_version'])}</code><br>
    Passed: {report['passed']} &nbsp; Failed: {report['failed']} &nbsp; Skipped: {report['skipped']}<br>
    Fragments: {report['fragments']} &nbsp; Elided: {report['elided']}<br>
    Referenced, not scanned: {report['referenced_not_scanned']}
  </p>
  <table>
    <thead>
      <tr>
        <th>Health</th>
        <th>Page</th>
        <th>Failed checks</th>
        <th>Skipped checks</th>
        <th>First reason</th>
        <th>Source location</th>
      </tr>
    </thead>
    <tbody>
      {"".join(body_rows)}
    </tbody>
  </table>
</body>
</html>
"""
