# usd-docs-health

![CI](https://github.com/jcsilverio/usd-docs-health/actions/workflows/ci.yml/badge.svg)

`usd-docs-health` checks code examples and API references in NVIDIA's public Learn OpenUSD documentation against one pinned OpenUSD release. It is an independent project. It is not an official NVIDIA tool.

The static check parses ordinary fences labeled `python` or `py` and looks up dotted USD names, such as `Usd.Stage.Open`, in `usd-core` 26.11. It does not run those fences. The same command runs MyST code cells. A cell that calls `DisplayUSD` still flattens the stage. The `usd2gltf` converter is intercepted and counted. It is not run.

## Setup

Python 3.12. Run the commands below with that interpreter. If `python` starts another version, call the 3.12 program by its path.

The lesson corpus is a Git submodule at `vendor/learnopenusd`, pinned to `fcbb129ca9c4fe01bd3564c2ca6844c37d85c9c2`. Large assets use Git LFS (Large File Storage: Git keeps a small pointer, and the big file lives on another server). The static check does not read those assets.

```text
git lfs install
git submodule update --init --recursive
git -C vendor/learnopenusd lfs pull
python -m pip install -e ".[dev]"
```

`usd-core` is pinned to 26.11. pytest is pinned to 9.2.0.

## Run

```text
python -m usd_docs_health check --corpus vendor/learnopenusd --format json --html page-table.html --llms llms.txt
```

The JSON report lists every finding. The text summary, that JSON report, and the page table also count `{include}` and `literalinclude` directives as referenced, not scanned. That count is not a pass, a fail, or a skip. The text summary and the JSON report also count fragment retries beside the intercepted `usd2gltf` calls. That count is not part of the pass, fail, or skipped totals. The `--html` file is a static page table generated from that report: one row per lesson page, failures first, with no score or scripts. The `--llms` file is generated from that same report. It lists the corpus SHA, the USD version, this command, unhealthy pages, and incomplete pages. It is not a hosted file for Learn OpenUSD. CI uploads the JSON report, the page table, and `llms.txt` as artifacts.

The gate decides whether one proposed page can ship. It reruns the static check and the execution check on that file.

```text
python -m usd_docs_health gate --page path/to/page.md --corpus vendor/learnopenusd
```

`--page` is the Markdown file, including a temporary copy. `--corpus` is optional. Pass it when the page imports lesson helpers from the corpus `src/` directory. The gate prints `accept` when the page is healthy: at least one check ran, every check passed, and nothing was skipped. It prints `reject` when the page is unhealthy or incomplete. A `py` fence that does not parse is a reject. A page with no eligible checks is a reject. A page whose only signal is an `{include}` or `literalinclude` is a reject, with the reason `referenced, not scanned`. You supply the page. The command accepts or rejects that file.

Pytest runs a few handwritten pages through that same command. The gate must reject USDA text in a `python` fence, a code cell that calls `prim_range` before that name exists, a visible `create_new_stage()` call with no setup cell, and a wording-only edit of the USDA page. Changing the wording leaves the failing block in place, so that edit is still a reject. An indented `py` fragment that parses after its common indent is removed is a pass, not a reject.

```text
reject
passed 0, failed 1, skipped 0
fail path/to/page.md:4 expected '('
usd2gltf calls 0
fragments 0
referenced, not scanned 0
```

The install name is `usd-docs-health`. The Python package is `usd_docs_health`, under `src/`.

## Exit codes

`check` uses these codes.

| Code | Meaning |
|---|---|
| 0 | The run finished, at least one check ran, and no executed check failed |
| 1 | One or more documentation checks failed |
| 2 | Setup or coverage problem, such as a missing corpus, a docs folder with no ordinary `python` or `py` fences and no code cells, or a code cell that needs an LFS pointer file |
| 3 | Unexpected error in the tool |

If more than one applies, the code is the most serious: 3, then 2, then 1, then 0.

For `check`, exit code 0 means the run finished and no executed check failed. Pages with skipped checks stay incomplete. For `gate`, exit code 0 means that one page is healthy. Exit code 1 means `reject`, including a page with no eligible checks or a skipped check. Exit code 2 means the page is missing, the corpus path is missing, or a code cell needs an LFS pointer file. Exit code 3 means an unexpected error.

## Results

Counts below are from that corpus run. They are findings, not pages. In that run, a finding is one dotted name that resolved, one fence that failed to parse, or one code cell. The corpus SHA is `fcbb129ca9c4fe01bd3564c2ca6844c37d85c9c2`. The USD version is 26.11.

### Fences only

Static check of ordinary `python` and `py` fences. These numbers do not include code cells.

| Item | Value |
|---|---|
| Passed | 279 |
| Failed | 3 |
| Skipped | 0 |

Of those 279 passes, 214 are dotted names in `py` fences and 65 are dotted names in `python` fences. The three failures are parse errors. Every dotted USD name that was checked was found in the installed modules.

- `vendor/learnopenusd/docs/composition-basics/references.md`, line 86. A `python` fence holds USDA text, `def Xform "World"`. Python 3.12 reports `expected '('`.
- `vendor/learnopenusd/docs/asset-structure/workstreams/adding-user-workstreams.md`, line 92. A `py` fence holds one dictionary entry, `"roof": {"diffuseColor": (0.0, 0.0, 1.0), "roughness": 1.0, "metallic": 1.0},`. Python 3.12 reports `illegal target for annotation`.
- `vendor/learnopenusd/docs/creating-composition-arcs/relocates/working-with-relocates.md`, line 95. A `py` fence holds one indented list item, meant to be inserted into a larger list. Python 3.12 reports `unexpected indent`.

`skipped 0` means the static check has no skip outcome. `{include}` and `literalinclude` directives are not findings. They are counted separately as referenced, not scanned. Names such as `prim.GetReferences()` stay outside this check.

That run did not retry a fence that failed to parse. The checker now retries one as a fragment. The fragment tally is not part of the pass, fail, and skipped totals above. The next corpus run replaces these counts.

### Fences and code cells

On that same corpus, after `git -C vendor/learnopenusd lfs pull`, the check command printed:

```text
passed 422, failed 3, skipped 0
usd2gltf calls 32
```

The three failures are the fences above. Every code cell passed. The 422 is 279 fence passes plus 143 code-cell passes. `usd2gltf calls 32` counts intercepted converter calls. That tally is not part of the 422, and it is not a pass of the glTF conversion.

The checker discovered 147 lesson pages. 52 were healthy, 3 were unhealthy, and 92 were incomplete. Every incomplete page had the reason "no eligible checks." Those figures are from that run. `{include}` and `literalinclude` directives are now counted separately, and an include-only page is incomplete with the reason "referenced, not scanned."

A green CI run means pytest passed and the corpus check finished with exit code 0 or 1. Exit code 1 means a fence or a code cell failed. It does not mean every lesson passed. CI runs `git -C vendor/learnopenusd lfs pull` before that check. If a code cell still needs a pointer file, the check exits 2.

## Limitations

- Code cells run from the check command. `usd2gltf` is intercepted and counted. A code cell that needs a Git LFS pointer file is exit 2, a setup problem, not a failed example.
- Ordinary `python` and `py` fences are parsed and checked for module-dotted names. Each fence adds one parse finding. A fence that parses is a pass, including a fence that names no module-dotted USD symbol. Each dotted name in that fence is a separate finding. A fence that still does not parse after a fragment retry fails. A retry that parses is a pass, counted separately, and the symbol's line stays the line in the lesson. The modules in this version are `Usd`, `Sdf`, `UsdGeom`, `UsdShade`, and `UsdLux`. The fence check does not run the code.
- Lesson assets in Git LFS are not required for the static check. CI pulls those assets before the corpus check.
- A failure on 26.11 shows that an example failed on that release. It does not show that 26.11 caused the failure. There is no 25.11 run to compare against.
- Links, prose, and instance methods such as `prim.GetReferences()` are outside this version. `{include}` and `literalinclude` directives are counted, and the named file is not read or run. Many of those files are Markdown. The count is not a pass, a fail, or a skip, so a page that already has a passing check stays healthy. A page with no eligible check whose only signal is one of those directives is incomplete, with the reason "referenced, not scanned." A prose-only page stays "no eligible checks."
- There is no score and no hosted dashboard. The local static page table comes from `--html` on the check command. `llms.txt` comes from `--llms` on that same command.
- `gate` judges one Markdown file with the same two checks. The rest of the corpus stays unread.

## How this was built

I wrote SPEC.md first, as I worked through the Learn OpenUSD examples. It says what done looks like for each check and how that check is tested. Coding agents drafted checker and test code, and I wrote some of it by hand. I reviewed each change, reproduced failures, and merged it when it matched the spec and the tests passed. The counts above are from running that checker, and they include the three fences that fail to parse.
