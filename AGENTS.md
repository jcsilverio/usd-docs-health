# AGENTS.md

`usd-docs-health` checks code examples in the pinned Learn OpenUSD corpus. It is an independent project.

Run the check with:

```text
python -m usd_docs_health check --corpus vendor/learnopenusd --format json --html page-table.html --llms llms.txt
```

That command writes `llms.txt` from the same JSON report as the page table. `llms.txt` lists the corpus SHA, the USD version, this command, unhealthy pages, and incomplete pages. It is not a hosted file for Learn OpenUSD.

A green CI run means pytest passed and the corpus check finished with exit code 0 or 1. Exit code 0 means the run finished and no executed check failed. Exit code 1 means a fence, a USDA example, or a code cell failed. A green run does not mean every page is healthy.

## Before handing back a lesson edit

If you're proposing an edit to a lesson page, run the gate on the edited file before you hand it back:

```text
python -m usd_docs_health gate --page path/to/page.md --corpus vendor/learnopenusd
```

Keep the edited page in the lesson's `docs` folder, either in place or in a copy of that whole folder. Code cells run in a temporary copy of the page's `docs` folder, so a page copied out on its own can fail when it opens files that sat next to it. Keep `--corpus` so code cells can import the lesson helpers in the corpus `src/` directory. The gate reruns the static check, the USDA check, and the execution check on that one file.

The first line is `accept` or `reject`. `accept` (exit code 0) means the page is healthy: at least one check ran, every check passed, and nothing was skipped. `reject` (exit code 1) means a check failed, a check was skipped, or the page had nothing to check. The lines under `reject` list each failure or skip with its line in the page, or give a reason such as `no eligible checks`, `referenced, not scanned`, or `elided, not parsed`. Exit code 2 means the page or corpus path is missing, or a code cell needs an LFS pointer file. Exit code 3 means the tool itself crashed.

Don't hand back an edit the gate rejects. Fix it and rerun, or hand it back with the full gate output and say it was rejected. An `accept` doesn't mean the lesson is right. It means the code examples on that page passed these three checks. The gate doesn't read the prose or check links.
