# usd-docs-health

![CI](https://github.com/jcsilverio/usd-docs-health/actions/workflows/ci.yml/badge.svg)

`usd-docs-health` checks code examples and API references in NVIDIA's public Learn OpenUSD documentation against one pinned OpenUSD release. It is an independent project. It is not an official NVIDIA tool.

## Result

On Learn OpenUSD at `fcbb129` with `usd-core` 26.11, 10 examples fail, on 6 of the 147 lesson pages. Every code cell passed. Paths are under `vendor/learnopenusd/docs/`, and lines are lines in the lesson file.

Four are syntax errors:

- `asset-structure/reference-payload-pattern/what-is-ref-payload-pattern.md`, line 29. `variantSets "color_variant" {` uses the list keyword where a variant set is defined. The block form is `variantSet "color_variant" = {`. USD reports `Expected }`.
- `asset-modularity-instancing/refining-scenegraph-instances/scenegraph-instance-refinement.md`, line 43. `color3f primvars:asset_color = [(1, 0, 0)]` puts an array on a single `color3f`. USD reports `Type name missing [] for shaped value.`
- Same page, line 70. `double3 xformOp:rotateX = 10` declares a single-axis rotation with a three-value type. It should be a single value, such as `double`. USD's first message is `Not enough values to parse value of type Vec3d`.
- `composition-basics/references.md`, line 86. A `python` fence holds USDA text. Python 3.12 reports `expected '('`.

Eight USDA examples are indented with non-breaking spaces (U+00A0), which USD rejects. Two of them hold the type errors at lines 43 and 70 above, and the checker reports those two at their first non-breaking space, lines 29 and 58.

- `asset-modularity-instancing/refining-scenegraph-instances/scenegraph-instance-refinement.md`, lines 29, 58, and 88.
- `asset-modularity-instancing/authoring-scenegraph-instancing/scenegraph-instancing-intro.md`, lines 79 and 145. Line 79 is the Warehouse example. The published page's copy text has the same characters, and USD rejects it. That was checked by reading the text the page's copy button builds, not by pasting it.
- `asset-modularity-instancing/refining-point-instances.md`, line 12. The example is also elided (`[...]`), so the rest isn't parsed.
- `asset-modularity-instancing/authoring-point-instancing/point-instancing-intro.md`, lines 29 and 84. Both examples are also elided.

The counting rules, the full counts, and the limits are under [Results](#results) and [Limitations](#limitations).

The static check parses ordinary fences labeled `python` or `py` and looks up dotted USD names, such as `Usd.Stage.Open`, in `usd-core` 26.11. It does not run those fences. The same command runs MyST code cells. A cell that calls `DisplayUSD` still flattens the stage. The `usd2gltf` converter is intercepted and counted. It is not run. The USDA check parses each `usda` fence and `{code-block} usda` example with USD's own text parser. It doesn't compose the layer, run anything, or open the asset paths it names.

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

The JSON report lists every finding. The text summary, that JSON report, and the page table also count `{include}` and `literalinclude` directives as referenced, not scanned. The text summary and the JSON report also count fragment retries and elided USDA examples beside the intercepted `usd2gltf` calls. The page table shows the fragment and elided counts too. The `--html` file is a static page table generated from that report: one row per lesson page, failures first, with no score or scripts. The `--llms` file is generated from that same report. It lists the corpus SHA, the USD version, this command, unhealthy pages, and incomplete pages. It is not a hosted file for Learn OpenUSD. CI uploads the JSON report, the page table, and `llms.txt` as artifacts.

The gate decides whether one proposed page can ship. It reruns the static check, the USDA check, and the execution check on that file.

```text
python -m usd_docs_health gate --page path/to/page.md --corpus vendor/learnopenusd
```

`--page` is the Markdown file. Keep it in the lesson's `docs` folder, either in place or in a copy of that whole folder. Code cells run in a temporary copy of the page's `docs` folder, so a page copied out on its own can fail when it opens files that sat next to it. `--corpus` is optional. Pass it when the page imports lesson helpers from the corpus `src/` directory. The gate prints `accept` when the page is healthy: at least one check ran, every check passed, and nothing was skipped. It prints `reject` when the page is unhealthy or incomplete. A `python` or `py` fence that still does not parse after the fragment retries is a reject. A page with no eligible checks is a reject. A page whose only signal is an `{include}` or `literalinclude` is a reject, with the reason `referenced, not scanned`. A USDA example that doesn't parse, or that has a non-breaking space (U+00A0), is a reject. A page whose only USDA examples are elided is a reject, with the reason `elided, not parsed`. You supply the page. The command accepts or rejects that file.

Pytest runs a few handwritten pages through that same command. The gate must reject USDA text in a `python` fence, a code cell that calls `prim_range` before that name exists, a visible `create_new_stage()` call with no setup cell, and a wording-only edit of the USDA page. Changing the wording leaves the failing block in place, so that edit is still a reject. An indented `py` fragment that parses after its common indent is removed is a pass, not a reject.

```text
reject
passed 0, failed 1, skipped 0
fail path/to/page.md:4 expected '('
usd2gltf calls 0
fragments 0
elided 0
referenced, not scanned 0
```

The install name is `usd-docs-health`. The Python package is `usd_docs_health`, under `src/`.

## Exit codes

`check` uses these codes.

| Code | Meaning |
|---|---|
| 0 | The run finished, at least one check ran, and no executed check failed |
| 1 | One or more documentation checks failed |
| 2 | Setup or coverage problem, such as a missing corpus, a docs folder with nothing to check (no ordinary `python` or `py` fences, no code cells, and no USDA examples), or a code cell that needs an LFS pointer file |
| 3 | Unexpected error in the tool |

If more than one applies, the code is the most serious: 3, then 2, then 1, then 0.

For `check`, exit code 0 means the run finished and no executed check failed. Pages with skipped checks stay incomplete. For `gate`, exit code 0 means that one page is healthy. Exit code 1 means `reject`, including a page with no eligible checks, a skipped check, or only elided USDA examples. Exit code 2 means the page is missing, the corpus path is missing, or a code cell needs an LFS pointer file. Exit code 3 means an unexpected error.

## Results

Counts below are from that corpus run. They are findings, not pages. A finding is one parse result per fence, one lookup per dotted name, one parse result per USDA example, or one code cell. Fragment retries, intercepted `usd2gltf` calls, elided USDA examples, and referenced-not-scanned directives are counted beside those findings. That tally is not part of the pass, fail, or skipped totals. A fragment retry is also a parse pass, so that fence or USDA example is in the pass total and in the fragment tally. The corpus SHA is `fcbb129ca9c4fe01bd3564c2ca6844c37d85c9c2`. The USD version is 26.11.

### Fences only

Static check of ordinary `python` and `py` fences. These numbers do not include code cells.

| Item | Value |
|---|---|
| Passed | 400 |
| Failed | 1 |
| Skipped | 0 |

Of those 400 passes, 115 are parse findings and 285 are dotted names. 216 of the dotted names are in `py` fences and 69 are in `python` fences. 56 of the parse findings are `py` fences and 59 are `python` fences. Two of the `py` parse findings parsed only after a fragment retry. The other 113 fences parsed on the first try. The one failure is a parse error. Every dotted USD name that was checked was found in the installed modules.

- `vendor/learnopenusd/docs/composition-basics/references.md`, line 86. A `python` fence holds USDA text, `def Xform "World"`. Python 3.12 reports `expected '('`.
- `vendor/learnopenusd/docs/asset-structure/workstreams/adding-user-workstreams.md`, line 92. A `py` fence holds one dictionary entry, `"roof": {"diffuseColor": (0.0, 0.0, 1.0), "roughness": 1.0, "metallic": 1.0},`. It parses as a fragment, with reason `fragment, parsed as dict entry`. That fence names no dotted USD symbol.
- `vendor/learnopenusd/docs/creating-composition-arcs/relocates/working-with-relocates.md`, line 95. A `py` fence holds one indented entry, meant to be added to a larger list. It parses as a fragment, with reason `fragment, parsed as dedented`. `Sdf.Path` and `Sdf.Path.emptyPath` on that line also pass.

`skipped 0` means the static check has no skip outcome. `{include}` and `literalinclude` directives are not findings. They are the referenced-not-scanned tally. Names such as `prim.GetReferences()` stay outside this check.

These two fences are 2 of the 4 fragment retries in the full run.

### USDA examples

USDA check of `usda` fences and `{code-block} usda` examples. The corpus has 32.

| Item | Value |
|---|---|
| Passed | 21 |
| Failed | 9 |
| Elided | 5 |

Three of the elided examples also have non-breaking spaces, so they're failures too. The other two add no finding. That's 30 findings from 32 examples. The nine failing USDA examples are listed under [Result](#result). Two of them appear there twice, once at the type error and once at the first non-breaking space, because the checker reports the non-breaking-space line.

- Eight failures have non-breaking spaces (U+00A0). Each one is reported at the first such line in its example. In two of them, USD still fails after the spaces are replaced, at lines 43 and 70 of `scenegraph-instance-refinement.md`, and the reason gives both. The lesson labels both of those examples "NOT editable" and explains why in composition terms. The parse errors are separate from that.
- One failure, `what-is-ref-payload-pattern.md` line 29, has no non-breaking space. It fails on the `variantSets` line alone.
- Two passes parsed only after the layer-metadata retry: `vendor/learnopenusd/docs/creating-composition-arcs/relocates/working-with-relocates.md`, lines 29 and 68. Each is a `relocates = {` excerpt, with reason `fragment, parsed as layer metadata`.

The five elided examples, by the line where each one opens:

- `vendor/learnopenusd/docs/asset-structure/asset-structure-principles/asset-interface-pt3.md`, line 2. It's the only example on that page, so the page is incomplete with the reason "elided, not parsed."
- `vendor/learnopenusd/docs/asset-structure/asset-parameterization/what-is-asset-parameterization.md`, line 28. The page's other example passes, so the page stays healthy.
- `vendor/learnopenusd/docs/asset-modularity-instancing/refining-point-instances.md`, line 8. It also fails for non-breaking spaces.
- `vendor/learnopenusd/docs/asset-modularity-instancing/authoring-point-instancing/point-instancing-intro.md`, lines 25 and 79. Both also fail for non-breaking spaces.

### All checks

On that same corpus, after `git -C vendor/learnopenusd lfs pull`, the check command's summary was:

```text
passed 564, failed 10, skipped 0
usd2gltf calls 32
fragments 4
elided 5
referenced, not scanned 31
```

A `fail` line follows for each of the 10 failures: the fence and the nine USDA examples above. Every code cell passed. The 564 is 400 fence passes, 21 USDA passes, and 143 code-cell passes. `usd2gltf calls 32` counts intercepted converter calls. It is not a pass of the glTF conversion. `fragments 4` is the two fence retries and the two layer-metadata retries. `elided 5` is the five elided USDA examples. `referenced, not scanned 31` counts `{include}` and `literalinclude` directives.

The checker discovered 147 lesson pages. 65 were healthy, 6 were unhealthy, and 76 were incomplete. 69 incomplete pages had the reason "no eligible checks." 6 had the reason "referenced, not scanned." 1 had the reason "elided, not parsed."

A green CI run means pytest passed and the corpus check finished with exit code 0 or 1. Exit code 1 means a fence, a USDA example, or a code cell failed. It does not mean every lesson passed. CI runs `git -C vendor/learnopenusd lfs pull` before that check. If a code cell still needs a pointer file, the check exits 2.

## Limitations

- Code cells run from the check command. `usd2gltf` is intercepted and counted. A code cell that needs a Git LFS pointer file is exit 2, a setup problem, not a failed example.
- Ordinary `python` and `py` fences are parsed and checked for module-dotted names. Each fence adds one parse finding. A fence that parses is a pass, including a fence that names no module-dotted USD symbol. Each dotted name in that fence is a separate finding. A fence that still does not parse after a fragment retry fails. A retry that parses is a pass, counted separately, and the symbol's line stays the line in the lesson. The modules in this version are `Usd`, `Sdf`, `UsdGeom`, `UsdShade`, and `UsdLux`. The fence check does not run the code.
- USDA examples are parsed, not composed or run, and the asset paths they name aren't opened. An example that fails to parse and has a literal `...` outside a quoted string is elided. It's counted, and it adds no finding. A non-breaking space (U+00A0) is a fail even when the rest of the example parses, because USD rejects that character and a reader can't see it. One retry wraps the example as layer metadata. A retry that parses is a pass, counted with the fragments.
- Lesson assets in Git LFS aren't required for the static check or the USDA check. CI pulls those assets before the corpus check.
- A failure on 26.11 shows that an example failed on that release. It does not show that 26.11 caused the failure. There is no 25.11 run to compare against.
- Links, prose, and instance methods such as `prim.GetReferences()` are outside this version. `{include}` and `literalinclude` directives are counted, and the named file is not read or run. Many of those files are Markdown. A page that already has a passing check stays healthy. A page with no eligible check whose only signal is one of those directives is incomplete, with the reason "referenced, not scanned." A prose-only page stays "no eligible checks."
- There is no score and no hosted dashboard. The local static page table comes from `--html` on the check command. `llms.txt` comes from `--llms` on that same command.
- `gate` judges one Markdown file with the same three checks. The rest of the corpus stays unread.

## How this was built

I wrote SPEC.md first, as I worked through the Learn OpenUSD examples. It says what done looks like for each check and how that check is tested. I wrote the first version of the checker myself, with coding agents suggesting code and reviewing it for errors and best practices. After that, they drafted the new checks and their tests. I reviewed each change, reproduced failures, and merged it when it matched the spec and the tests passed. The counts above are from running that checker, and they include the 10 examples that fail.
