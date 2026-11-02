# usd-docs-health

`usd-docs-health` checks code examples and API references in NVIDIA's public Learn OpenUSD documentation against one pinned OpenUSD release. It is an independent project. It is not an official NVIDIA tool.

The static check parses ordinary `python` fences and looks up dotted USD names, such as `Usd.Stage.Open`, in `usd-core` 26.11. It does not run those fences. Code cells are not executed yet.

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
python -m usd_docs_health check --corpus vendor/learnopenusd --format json
```

The install name is `usd-docs-health`. The Python package is `usd_docs_health`, under `src/`.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | The run finished, at least one check ran, and no executed check failed |
| 1 | One or more documentation checks failed |
| 2 | Setup or coverage problem, such as a missing corpus or a docs folder with no ordinary python fences |
| 3 | Unexpected error in the tool |

If more than one applies, the code is the most serious: 3, then 2, then 1, then 0.

Exit code 0 does not mean every page is healthy. Pages with skipped checks stay incomplete.

## Results

Static check of ordinary `python` fences on the pinned corpus. These counts are findings. A finding is one dotted name that resolved, or one fence that failed to parse. They are not page counts.

| Item | Value |
|---|---|
| Corpus SHA | `fcbb129ca9c4fe01bd3564c2ca6844c37d85c9c2` |
| USD version | 26.11 |
| Passed | 65 |
| Failed | 1 |
| Skipped | 0 |

The failure is `vendor/learnopenusd/docs/composition-basics/references.md`, line 86. A `python` fence there holds USDA text, `def Xform "World"`. Python 3.12 reports `expected '('`. No missing USD symbol was reported.

`skipped 0` means this check has no skip outcome. Code cells, `{include}` and `literalinclude` directives, and names such as `prim.GetReferences()` are outside the count.

A green CI run means pytest passed and the static check finished with exit code 0 or 1. Exit code 1 means a fence failed. It does not mean every lesson passed.

## Limitations

- Code cells are not executed yet.
- Ordinary `python` fences are parsed and checked for module-dotted names. A fence that does not parse fails. The modules in this version are `Usd`, `Sdf`, `UsdGeom`, `UsdShade`, and `UsdLux`.
- Lesson assets in Git LFS are not required for the static check. CI checks the submodule out and leaves LFS pointer files in place.
- A failure on 26.11 shows that an example failed on that release. It does not show that 26.11 caused the failure. There is no 25.11 run to compare against.
- Links, prose, `{include}` and `literalinclude` directives, and instance methods such as `prim.GetReferences()` are outside this version.
- There is no score and no hosted dashboard.
