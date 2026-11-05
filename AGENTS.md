# AGENTS.md

`usd-docs-health` checks code examples in the pinned Learn OpenUSD corpus. It is an independent project.

Run the check with:

```text
python -m usd_docs_health check --corpus vendor/learnopenusd --format json --html page-table.html --llms llms.txt
```

That command writes `llms.txt` from the same JSON report as the page table. `llms.txt` lists the corpus SHA, the USD version, this command, unhealthy pages, and incomplete pages. It is not a hosted file for Learn OpenUSD.

A green CI run means pytest passed and the corpus check finished with exit code 0 or 1. Exit code 0 means the run finished and no executed check failed. Exit code 1 means a fence or a code cell failed. A green run does not mean every page is healthy.
