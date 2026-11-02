# usd-docs-health

`usd-docs-health` checks code examples and API references in NVIDIA's public Learn OpenUSD documentation against one pinned OpenUSD release. It is an independent project. It is not an official NVIDIA tool.

The checks are not implemented yet. The command below returns exit code 2 until they exist. Exit code 2 means the run could not perform a real check. The tests in `tests/` lock that behavior in.

## Setup

Python 3.12. Run the commands below with that interpreter. If `python` starts another version, call the 3.12 program by its path.

The lesson corpus is a Git submodule at `vendor/learnopenusd`, pinned to `fcbb129ca9c4fe01bd3564c2ca6844c37d85c9c2`. Large assets use Git LFS (Large File Storage: Git keeps a small pointer, and the big file lives on another server). The current tests do not read those assets.

```text
git lfs install
git submodule update --init --recursive
git -C vendor/learnopenusd lfs pull
python -m pip install -e ".[dev]"
```

`usd-core` is pinned to 26.11. pytest is pinned to 9.2.0.

## Run

```text
python -m usd_docs_health check --corpus vendor/learnopenusd --format json
```

The install name is `usd-docs-health`. The Python package is `usd_docs_health`, under `src/`.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | The run finished, at least one check ran, and no executed check failed |
| 1 | One or more documentation checks failed |
| 2 | Setup or coverage problem, including no checks implemented yet |
| 3 | Unexpected error in the tool |

If more than one applies, the code is the most serious: 3, then 2, then 1, then 0.

Exit code 0 does not mean every page is healthy. Pages with skipped checks stay incomplete.

## Results

The pinned corpus has not been checked yet. These are placeholders, not a baseline.

| Item | Value |
|---|---|
| Corpus SHA | `fcbb129ca9c4fe01bd3564c2ca6844c37d85c9c2` |
| USD version | 26.11 |
| Pages | not run |
| Pass | not run |
| Fail | not run |
| Skipped | not run |

A green CI run means pytest passed. It does not mean the Learn OpenUSD lessons passed.

## Limitations

- Code cells are not executed yet.
- Ordinary Python fences are not parsed or symbol-checked yet.
- Lesson assets in Git LFS are not required for the current tests. CI checks the submodule out and leaves LFS pointer files in place.
- A failure on 26.11, once checks exist, shows that an example failed on that release. It does not show that 26.11 caused the failure. There is no 25.11 run to compare against.
- Links, prose, `{include}` and `literalinclude` directives, and instance methods such as `prim.GetReferences()` are outside this version.
- There is no score and no hosted dashboard.
