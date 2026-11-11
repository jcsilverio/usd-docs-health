# usd-docs-health v0: Specification

## 1. What I'm building

`usd-docs-health` is a small, independent tool that checks whether the code examples and API references in NVIDIA's public Learn OpenUSD documentation still work with a specific version of OpenUSD.

While working through Learn OpenUSD hands-on, I ran into three things worth checking automatically:

- The [References](https://docs.nvidia.com/learn-openusd/latest/composition-basics/references.html) lesson's examples call `create_new_stage()`, a helper imported from `lousd.utils.helperfunctions` in a hidden setup cell. A note on the page explains this and tells readers to use `Usd.Stage.CreateNew()` in their own scripts.
- The [Stage Traversal](https://docs.nvidia.com/learn-openusd/latest/beyond-basics/stage-traversal.html) lesson's pruning snippet calls `prim_range.PruneChildren()`, but `prim_range` is never defined. Running it raises `NameError`.
- The [Prims](https://docs.nvidia.com/learn-openusd/latest/stage-setting/prims.html) lesson lists a prim's type (`Cube`) where its name (`Box`) belongs.

I also noticed that the rendered pages don't say which OpenUSD release they target. The Learn OpenUSD build installs `usd-core` 25.11: its `uv.lock` and the exported `requirements.txt` both pin that version, and `pyproject.toml` sets a floor of 25.5. My local environment runs 26.11. I want to turn observations like these into repeatable checks instead of relying on someone to catch the same problems by hand.

Learn OpenUSD already has CI. On every push and pull request, its workflow builds the site with the lesson code cells executed on `usd-core` 25.11, then runs a pytest suite against the lessons. Three things fall outside it. The same cells may not still run on a newer release. Ordinary fences labeled `python` or `py` are displayed and never executed. USDA examples are displayed and never parsed. Upstream's tests check the `.usda` files the code cells write, not the examples printed on the page. v0 runs the same cells on 26.11. It checks those fences without running them. It parses each one as Python and checks USD names reached through a module, such as `Usd.Stage.Open`. It parses each USDA example with USD, without composing it.

For v0, the tool checks a fixed snapshot of Learn OpenUSD against `usd-core==26.11`. It runs each lesson's code cells, checks ordinary fences labeled `python` or `py` without running them, parses USDA examples without composing them, and reports what passed, failed, or couldn't be tested. If a check fails, the affected example or page can't be reported as healthy, and skipped examples are reported as skipped, never quietly counted as successes.

The three things above don't all map to v0 checks:

| What I found | Caught by v0 in the corpus? | Why |
|---|---|---|
| References: `create_new_stage()` | No | The hidden setup cell imports the helper, so the name is defined once that cell runs. Upstream's workflow executes these cells on 25.11. The 26.11 result will come from the corpus run. The page is expected to fail the parse check for another reason: its first USDA sample is in a `python` fence. |
| Stage Traversal: `prim_range` | No | The snippet is an ordinary fence, which v0 parses but doesn't run, and `prim_range` is a local name, not a USD symbol. A fixture puts the same mistake in a code cell, where the execution check catches it. |
| Prims: `Cube` for `Box` | No | It's in prose, which v0 doesn't scan. |

So v0 doesn't flag any of the three where they sit in the pinned snapshot. They showed me which checks are worth building. The corpus run will show what those checks actually find.

This isn't a fork of Learn OpenUSD or a general-purpose documentation linter. I'm keeping the first version small enough to build, test, and explain clearly.

## 2. Scope and pinned versions

The same inputs must produce comparable results locally and in CI, so both the documentation source and the USD version are fixed before any check runs.

| Item | Decision |
|---|---|
| Documentation source | `NVIDIA-Omniverse/LearnOpenUSD` |
| Source branch | `main`, pinned to one commit |
| Corpus location | `vendor/learnopenusd` |
| Commit SHA | `fcbb129ca9c4fe01bd3564c2ca6844c37d85c9c2` (tip of `main` on Nov 2, 2026, committed Oct 22, 2026) |
| Python | 3.12 |
| USD package | `usd-core==26.11` |
| CI environment | GitHub Actions, Linux runner |
| GPU requirement | None |
| Documentation unit | One lesson Markdown file under `vendor/learnopenusd/docs/` equals one page. Files the Sphinx build excludes from the site, such as `docs/_includes/`, aren't pages. |

I'll use a Git submodule rather than downloading the documentation on every test run. The submodule makes the exact source revision visible in Git, and local and CI runs use the same files. For the first pin, I'll use the commit at the tip of `main` on the day I pin the corpus and record its full SHA and date. I won't assume that commit matches the public documentation deployment unless I can verify it separately. They can differ: on Nov 2, 2026, the published References page said LIVRPS where `main` said LIVERPS.

The README and every report include the full corpus SHA and the installed USD version. Upstream changes aren't pulled in automatically.

The version difference is intentional: I'm testing compatibility with 26.11, not claiming NVIDIA wrote these lessons for that version. Reports must make this clear when describing failures. Without a run on 25.11 to compare against, a failure shows that an example fails on 26.11, not that 26.11 caused it.

### Git LFS and local setup

The `LearnOpenUSD` repo uses Git LFS for images, videos, and USD assets. A plain submodule checkout can leave LFS pointer files instead of usable assets if LFS hasn't been initialized. The documented setup is:

1. `git lfs install`
2. `git submodule update --init --recursive`
3. `git -C vendor/learnopenusd lfs pull`

CI also initializes submodules and retrieves the LFS files the selected examples need. Only the execution check needs LFS content. The static check and the USDA check read only the Markdown. Missing LFS content is reported as a setup problem, not as a broken documentation example. The checker detects it by finding LFS pointer files where the execution check needs real assets.

## 3. Checks included in v0

v0 has three checks. An execution check runs the MyST code cells. A static check covers ordinary fences labeled `python` or `py`. A USDA check parses USDA examples (Section 3.6).

### 3.1 Finding Python examples

All three checks scan Markdown files under the pinned corpus's `docs/` directory (`vendor/learnopenusd/docs/`), not this repository's own files. Learn OpenUSD mixes ordinary fences labeled `python` or `py` with MyST notebook-style code cells. The Stage Traversal lesson is a useful test case. It has both, along with hidden setup code that prepares a USD stage.

The extractor recognizes three things.

- An ordinary fence whose first word after the backticks is `python` or `py`. Spaces before the backticks, between the backticks and the word, and after the word still count. `` ``` python `` and `` ``` py `` count. `` ```python3 `` does not, because that word is `python3`.
- A MyST `{code-cell}` directive that contains Python
- Cell metadata, such as the `remove-input` tag on hidden setup cells

The pinned lessons use both labels. Working with Sublayers opens a snippet with `py`. Earlier lessons open snippets with `python`. Parser tests cover both. v0 doesn't execute `.ipynb` files or reproduce the full Sphinx and MyST-NB build.

A label of `python3` stays out. A `{code-block}` directive stays out of the Python checks. A `{code-block}` with the argument `usda` is a USDA example (Section 3.6), and so is a fence labeled `usda`. Fences labeled `powershell` or `sh` stay out. Working with Sublayers uses those last two for terminal commands. A shell command parsed as Python would fail for the wrong reason.

MyST code cells are what the Learn OpenUSD build executes, so v0 executes them too (Section 3.2). Ordinary fences labeled `python` or `py` are displayed and never executed by the build. Some are fragments with undefined variables, so v0 doesn't run them either. The static check parses each one as Python and checks its USD symbols (Section 3.4). A fence that still does not parse after the fragment tries (Section 3.5) fails, and the original parse error is the reason. A reader who copies that fence gets something that isn't Python.

### 3.2 How code cells run

Some Learn OpenUSD lessons build up state across several cells: an earlier cell creates a stage, and a later cell uses it without creating it again. Hidden setup cells, tagged `remove-input`, import helpers such as `create_new_stage()` from the corpus's `lousd` package, and the visible cells call them. So v0 runs each lesson page the way the documentation build does: as a notebook.

Each Markdown page is converted to a notebook with jupytext and executed with nbclient, in a fresh kernel per page, with the hidden setup cells included. The working directory is the page's own folder inside a temporary copy of the corpus's `docs/` directory, because lessons use relative paths to their assets. The corpus's `src/` directory is on `PYTHONPATH`, so setup cells can import its `lousd` helper package. I don't install that package, because its dependencies include the full documentation toolchain. nbclient needs a registered Jupyter kernel, so the environment also installs `ipykernel`, which provides the `IPython` module that `lousd`'s display helpers import.

Results are recorded per cell, with source locations and error details. When a cell fails, the page stops, and its remaining cells are marked skipped with the reason "earlier cell failed". Their results would otherwise reflect the first failure, not their own code. Each cell has an execution timeout. A cell that times out fails, and the rest of the page is skipped the same way.

Running pages as notebooks follows the build's semantics closely, but it isn't a replacement for the full documentation build: v0 doesn't render pages or check their output.

### 3.3 Display cells and skips

Lesson cells that show a stage in a 3D viewer call `DisplayUSD` from the `lousd` package. It flattens the stage with USD and then calls an external converter, `usd2gltf`, to produce a glTF file for the viewer. The helper never checks the converter's result, and no lesson code reads the converted file. So v0 intercepts only that converter call inside each page's kernel. The USD code around it still runs, and so do the cells after it. The report counts how many converter calls were intercepted. That count is a separate tally of unchecked conversions, neither a pass of the conversion nor a skip, so a page can be healthy while every conversion on it was intercepted. v0 doesn't check the glTF conversion itself.

Examples are skipped when they require:

- `usdview`, Omniverse Kit, Isaac Sim, or GPU-specific functionality
- Network access or external services
- Missing generated assets or prerequisites that cannot be reproduced
- Earlier cells that failed or were skipped

Every skip must include a specific reason and source location. An example is skipped only when its unsupported prerequisite or dependency can be identified. An unexpected Python exception isn't enough. If an eligible example raises an unexpected exception, it fails. If an earlier cell fails, that failure stays visible even though the cells after it are skipped. These rules are explicit so the checker can't raise its pass rate by turning real failures into skips.

### 3.4 Static check of ordinary fences

The second check covers ordinary fences labeled `python` or `py`. No build executes them. For each fence, it first checks that the code parses as Python. Every fence adds one parse finding. If the fence parses, that finding is a pass, even when the fence names no USD symbol. If it still doesn't parse after the fragment tries (Section 3.5), that finding is a fail. Then it looks for USD API symbols and verifies that they exist in the installed version. Code cells aren't symbol-checked, because running them already exercises the same calls, and checking both would count one bug twice. General Markdown prose, inline backticks, and MyST cross-reference roles aren't scanned yet, which keeps the scope manageable and avoids false positives from descriptive text.

The check starts with modules such as `Usd`, `Sdf`, `UsdGeom`, `UsdShade`, and `UsdLux`. If a code block refers to `Usd.Stage.Open`, the checker resolves that dotted name through the installed `pxr` modules. A fake reference such as `Usd.Foo.Bar` fails. It uses a lightweight static parser and Python introspection, not full type inference.

That means only names reached through a module are checked. Instance methods such as `prim.GetReferences()` would need type inference, and undefined local names such as `prim_range` aren't USD symbols, so neither is covered in v0.

Dynamic references such as `getattr(Usd.Stage, name)` are out of scope for v0. The checker doesn't guess the value of `name`. Dynamic lookups are excluded from symbol validation rather than reported as missing APIs.

Each finding must include the page, source location, referenced symbol or parse error, and reason for failure.

### 3.5 Exercise fragments

Some lesson fences are Python fragments for a larger script. Any ordinary `python` or `py` fence that fails to parse gets the same three tries, in order. The fence is still not executed. It should not fail simply because it is not a complete Python script.

1. Remove common leading indentation (dedent).
2. Wrap the dedented text in square brackets (`[` and `]`), each on its own line, to test whether it is a list item.
3. Wrap the dedented text in curly braces (`{` and `}`), each on its own line, to test whether it is a dictionary entry.

Stop at the first successful parse. Treat the fence as a fragment, check its dotted USD names as usual, and record the parse as a pass with one of these reasons:

- `fragment, parsed as dedented`
- `fragment, parsed as list item`
- `fragment, parsed as dict entry`

The line in the finding is the line in the lesson. The bracket on its own line is there so the fragment can be parsed, and that extra line is not reported.

If all three attempts fail, report the original parse error and its line in the lesson. No other transformations are allowed.

The report counts these fragments beside the intercepted `usd2gltf` calls (Section 3.3). The count is separate from the pass, fail, and skipped totals. The parse finding is the pass, so a reader can see how many passing fences required a retry.

**Fragments are not skipped.** They still receive the normal USD name checks.

### 3.6 USDA examples

Many lessons show scene description as USDA, USD's text format, instead of Python. No build parses these examples. A reader who copies one into a `.usda` file expects USD to open it. So v0 parses each one with USD's own parser. It does not compose the layer, run anything, or open the asset paths it names, such as `@./RobotArm.usd@`.

An example is one of two things:

- An ordinary fence whose first word after the backticks is `usda`. Spaces count the same way as for `python` and `py` (Section 3.1), so `` ``` usda `` counts.
- A `{code-block}` directive with the argument `usda`. Option lines that start with `:`, such as `:linenos:` and `:emphasize-lines:`, and the blank line after them, are not part of the example.

Each example is checked in this order.

1. If the example does not start with `#usda`, add the line `#usda 1.0` before it. USD needs that header to read the text. The added line is never reported.
2. Replace each non-breaking space (U+00A0) with an ordinary space. A reader can't see that character, and USD rejects it. The example still fails, but USD still checks everything else in it. Failing before the parse would hide a second bug in the same example, which happens on the Introduction to Scenegraph Instance Refinement page.
3. Parse the text with `Sdf.Layer.CreateAnonymous(".usda").ImportFromString(text)`. USD raises an error when the text does not parse.
4. If the parse fails and the example contains a literal `...` outside a quoted string, the example is elided: the lesson left part of it out on purpose. It adds no finding and is counted in the `elided` tally.
5. If the parse fails and the example is not elided, retry once with the text after the header wrapped in `(` and `)`, each on its own line, as layer metadata. A retry that parses is a fragment with the reason `fragment, parsed as layer metadata`, counted in the same `fragments` tally as Section 3.5. Some lessons show only a layer's metadata, such as a `relocates` entry. It should not fail simply because it is not a complete layer. No other retries are allowed.

Each example that is not elided adds one finding:

- **A fail when the example had a non-breaking space.** The reason is `non-breaking space (U+00A0) at line N`, where N is the first such line in the lesson. If the parse still failed, the reason also gives USD's error and its line. The finding's line is N. An example with both a non-breaking space and `...` gets this fail, without USD's error, and is also counted in `elided`, because its USD content still wasn't checked.
- **Otherwise, a pass** when the parse or the retry succeeded.
- **Otherwise, a fail** with USD's error. When USD reports several errors, the reason lists every message in order. The finding's line comes from the last message, because only the last one says which line failed.

The line in the finding is the line in the lesson. The `#usda 1.0` line is there so USD can read the text, and that extra line is not reported. In a `{code-block}`, counting starts after the options and the blank line. If the retry also fails, report the first parse's error, not the retry's.

The report counts elided examples beside the fragments (Section 3.5), the intercepted `usd2gltf` calls (Section 3.3), and the referenced files (Section 4). That count is not a pass, a fail, or a skip. A page whose only signal is an elided example is incomplete, with the reason `elided, not parsed`.

## 4. Results and exit codes

Each individual check has one of three outcomes:

| Result | Meaning |
|---|---|
| `pass` | The check ran successfully |
| `fail` | The example failed, a fence or USDA example didn't parse, or an expected API symbol was missing |
| `skipped` | The check wasn't run, with a documented reason |

v0 has no warnings and no scoring system.

### Page-level health

Page-level health combines the execution check, the static check, and the USDA check for the same Markdown file, so a page can be unhealthy because of a missing API symbol in a fence, or a USDA example that doesn't parse, even when all its code cells passed. A page is one of three things.

- **Healthy** when at least one check ran, all checks passed, and nothing was skipped. Intercepted converter calls aren't skips (Section 3.3), a referenced file that was not scanned isn't a skip, and an elided USDA example isn't a skip either (Section 3.6).
- **Unhealthy** when any check failed.
- **Incomplete** when nothing failed but some checks were skipped, or the page had no eligible checks.

A page with only skipped examples hasn't been verified, which is why it's incomplete rather than healthy. A page with no eligible checks at all, such as a prose-only lesson, is also incomplete, with the reason "no eligible checks," and the report counts those pages separately so they aren't mistaken for pages with skips.

`{include}` and `literalinclude` name a file and leave its contents unscanned. v0 counts each of those directives as referenced, not scanned, and leaves the file unread and unrun. The count sits beside the results the way intercepted `usd2gltf` calls do (Section 3.3). It is neither a pass nor a skip, so a page that already has a passing check stays healthy.

Working with Sublayers is the mixed case. Its `py` fence is an eligible check. Its exercise script is a `literalinclude`. When the fence passes and nothing else fails, the page is healthy, and the script appears only in the count.

Authoring Point Instancing has a `literalinclude` and no eligible fence or code cell. That page stays incomplete, with the reason "referenced, not scanned". A prose-only lesson keeps the reason "no eligible checks". The report counts those prose pages separately.

A page whose only USDA examples are elided, with no other check, is incomplete, with the reason `elided, not parsed`. If that page also has an `{include}` or `literalinclude`, the reason is still `elided, not parsed`, because the elided text is on the page itself and an edit to the lesson can fix it.

### CLI exit codes

| Code | Meaning |
|---|---|
| `0` | The run completed, at least one check executed, and no executed checks failed |
| `1` | One or more documentation checks failed |
| `2` | Setup, configuration, or coverage problem, such as a missing submodule, wrong USD version, missing required LFS assets, or no executable checks in the selected run |
| `3` | Unexpected runner or internal tool error |

Once the arguments are parsed, an unexpected error anywhere in the run returns 3, in both `check` and `gate`. In `check`, that covers the page search, the LFS pointer scan, the page loop, the report, the HTML and `llms.txt` files, and the final summary. In `gate`, it covers the same steps for one page. A usage error, such as a missing `--corpus` or `--page`, isn't caught. The argument parser exits with code 2. If a run hits more than one of these, it returns the most serious one, in the order 3, then 2, then 1, then 0.

Exit code `0` doesn't mean every page is healthy. It means the runner completed, at least one check executed, and no executed checks failed. Pages with skipped checks are still marked incomplete, and the report must show that coverage gap rather than claim the whole corpus is healthy. The command never returns success if it couldn't load the corpus, verify its environment, or execute any checks.

## 5. CLI and local workflow

v0 has two commands:

```
python -m usd_docs_health check --corpus vendor/learnopenusd --format json
python -m usd_docs_health gate --page path/to/page.md --corpus vendor/learnopenusd
```

`check` scans the corpus. `gate` reruns every check on one page and prints accept or reject.

The distribution name in `pyproject.toml` is `usd-docs-health`. The Python package is `usd_docs_health`, under `src/`, so the repository root and the importable module stay separate.

`check` produces a readable terminal summary, a JSON report, and a static HTML page table generated from that report. All three include:

- Corpus commit SHA and USD version
- Number of pages and code blocks discovered
- Pass, fail, and skipped counts
- Page-level results and source locations
- Failure details and skip reasons
- How many `{include}` and `literalinclude` directives were referenced and not scanned
- How many fences and USDA examples parsed as fragments, and how many USDA examples were elided

The exit code tells a reader whether the run hit documentation failures, a setup problem, or a checker error. Each failure keeps its full traceback, so a single failure's cause can be read rather than guessed.

The page table has one row per page, with its health, fail and skip counts, the first failure or skip reason, and the source location, sorted with failures first. Its header shows the corpus SHA, the USD version, and the pass, fail, and skipped totals. It's a single generated file with no scoring, charts, or scripts.

The tool runs without a GPU, and code cells execute in a fresh kernel per page, with timeouts and temporary working directories. Because the checker executes code from an external repository, CI must run it without access to repository secrets or privileged credentials. A kernel isn't a security sandbox, so the pinned corpus and the execution environment remain part of the trust boundary.

## 6. Tests and acceptance criteria

What done means for each v0 deliverable, and how I'll check it:

| Milestone | Done when | How I'll verify it |
|---|---|---|
| **Pinning** | Python 3.12, `usd-core==26.11`, the corpus SHA, and LFS setup are documented | `Usd.GetVersion()` reports the expected version. `git submodule status` matches the recorded SHA. Required assets are available |
| **CI** | GitHub Actions initializes submodules and LFS, installs pinned dependencies, runs pytest, and records corpus results | CI fails the job on checker failures and publishes real corpus findings |
| **Static check** | Ordinary fences labeled `python` or `py` are parsed, and supported dotted API references are checked against the installed package | Valid API fixtures pass. A fake symbol such as `Usd.Foo.Bar` fails. A fence that isn't Python fails. A page whose only Python is a `py` fence naming `Usd.Stage.CreateNew` produces a finding |
| **USDA check** | `usda` fences and `{code-block} usda` directives are parsed with USD, and elided examples are counted | A valid example passes, with and without `#usda 1.0`. `variantSets "x" {`, a `color3f` array, and `double3 xformOp:rotateX = 10` fail. A non-breaking space fails with its own reason. An elided example adds no finding. A `relocates` excerpt passes as a fragment. The gate rejects a page whose only USDA is elided |
| **Execution check** | Code cells run per page as a notebook, hidden setup cells included, in page order | A corpus run produces accurate pass, fail, and skipped results, including dependency, timeout, and display-cell cases |
| **Pytest fixtures** | Known-good and known-bad Markdown fixtures exist | `pytest` confirms that expected successes pass and known failures are detected |
| **Page table** | A static HTML page table is generated from the JSON report | A fixture report produces the expected rows, with failures first |
| **README** | Setup, exit codes, supported formats, versions, limitations, and actual results are documented | Another developer can reproduce the run and understand the numbers |

### Fixtures I'll start with

Small Markdown examples with known outcomes live in `tests/fixtures/pages/`. The first set covers a working USD example, a nonexistent API reference, a `python` fence that isn't Python, a broken Python example, two cells where the second depends on state from the first, and a cell that times out. A skipped-example fixture checks that missing prerequisites don't become false passes or unrelated runtime failures.

One fixture page has no code cell and no `python` fence. Its only Python is a `py` fence that names `Usd.Stage.CreateNew`. Until the parser accepts `py`, that page is incomplete. Once the parser accepts `py`, the same page produces a finding.

A regression fixture is based on the `prim_range` mistake in the Stage Traversal lesson. It's a `{code-cell}` with the setup the mistake needs to produce a real `NameError`, so it shows the kind of bug the execution check catches. In the corpus itself, the snippet is an ordinary fence, which v0 doesn't run (Section 1).

I'll write each check's fixtures before the check itself, so it has expected behavior to test against.

## 7. CI and reporting policy

GitHub Actions runs on pushes and pull requests with Python 3.12 and the pinned dependencies, with read-only repository permissions. The workflow checks out the repository and submodule, retrieves the required LFS content with an explicit `git -C vendor/learnopenusd lfs pull` step, installs dependencies, and runs the automated tests.

CI keeps two questions separate:

1. Is `usd-docs-health` itself working correctly?
2. Does the pinned Learn OpenUSD corpus pass every check?

For v0, **checker failures fail the CI job, and known corpus failures are reported without failing that job.** I treat a red checker run as not mergeable. Pytest failures, setup errors, missing dependencies, and unexpected runner crashes fail CI. A completed corpus run that finds documentation failures returns exit code `1`. The workflow recognizes that result, keeps the report, and lets the job pass if the checker tests and other required steps succeeded. Exit codes `2` and `3` still fail the job. There's no blanket `continue-on-error` setting that could hide real setup or tool failures.

The corpus step sets `pipefail`, a shell setting that makes a pipeline report the check command's exit code when that output is piped into `tee`. Exit code 1 still lets the job pass. Exit codes 2 and 3 still fail the job.

The corpus report and the page table are available as CI artifacts, with a summary of failures and skipped examples. Once I've run the pinned corpus, the README shows the real baseline, and it says plainly that a green CI badge means the checker passed its own validation, not that every upstream example is healthy.

Making corpus regressions a blocking gate later would be a separate decision, with a documented baseline.

## 8. Source, licenses, and attribution

The `LearnOpenUSD` repo is licensed under Apache 2.0. The checker consumes the pinned source through a Git submodule and doesn't modify the upstream repository. If I copy upstream examples into local test fixtures, I'll keep the required attribution and license notices.

I describe `usd-docs-health` as an independent project and avoid branding that suggests it's an official NVIDIA tool.

If the checks uncover a genuine documentation issue, I may file an upstream issue with a minimal reproduction. Upstream fixes aren't required for v0.

## 9. What I'm leaving out

v0 defers:

- Link checking
- Hosted dashboards and historical trend tracking
- Automated LLM-generated fixes
- A larger evaluation set beyond the handwritten known-bad pages already in the tests
- A Sphinx documentation site for this repository
- Weighted health scores
- Automatic upstream corpus updates
- A second CI run on `usd-core` 25.11, to show which failures are specific to 26.11
- The contents of files named by `{include}` or `literalinclude`. v0 counts each directive and leaves the named file unread and unrun.
- Composing USDA examples, or opening the asset paths they name
- Reproducing the full Sphinx build, and dynamic API analysis

These could be useful later, but first the basic checks need to be reproducible and trustworthy. The gate command already reruns every check on one proposed page.

## 10. How I'll build it

The order is:

1. Pin the corpus commit, record the SHA in this spec, and verify the Markdown formats that snapshot uses.
2. Set up the package skeleton, the CLI with its exit codes, pytest, and CI, so every later change is tested on each push and pull request.
3. Write the static check's fixtures, then build the check until they pass. It comes first because it needs only the Markdown, not the LFS assets.
4. Write the execution check's fixtures, then build the check until they pass.
5. Run the full pinned corpus, record the actual baseline, and finish the README with real output rather than placeholder results.
6. Generate the page table from the corpus report.

Coding agents propose implementation code and tests. I inspect the changes, reproduce failures, and decide whether the behavior matches this spec. That review step matters: while I worked through the lessons, agents suggested URLs, commands, and API details that turned out to be wrong when I ran them. Tests and reports are how those assumptions become visible.

## 11. Remaining decisions

These implementation details are still open.

- The exact signals that mark a skip prerequisite, for example an import of an `omni` or `isaacsim` module.
- The timeout values and resource limits, to be set and tested during implementation.

The corpus SHA is recorded in Section 2. The fence labels are settled from the pinned lessons. An ordinary fence is accepted by the Python checks only when the first word after the backticks is `python` or `py`. Spaces before the backticks, between the backticks and the word, and after the word still count. `` ``` python `` and `` ``` py `` count. `` ```python3 `` does not, because that word is `python3`. A `{code-cell}` directive stays the only form v0 executes. Labels `python3`, `powershell`, and `sh` stay out. A `{code-block}` directive stays out of the Python checks. A `{code-block}` with the argument `usda` is a USDA example (Section 3.6), and so is a fence labeled `usda`. A fence that fails to parse is retried as a fragment (Section 3.5). It is not skipped.

Expanding scope, for example to weighted scoring or hosted dashboards, needs an explicit spec change, even if the first corpus run produces more failures or skips than expected.

## 12. What success looks like

v0 is complete when another developer can clone the repository, reproduce the pinned environment, run the checks, and see exactly what worked, what failed, and what wasn't tested. Every pass, failure, and skip in the report traces back to a page, a source location, and a reason.
