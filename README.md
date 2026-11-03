# usd-docs-health

`usd-docs-health` checks code examples and API references in NVIDIA's public Learn OpenUSD documentation against one pinned OpenUSD release. It is an independent project. It is not an official NVIDIA tool.

The static check parses ordinary `python` fences and looks up dotted USD names, such as `Usd.Stage.Open`, in `usd-core` 26.11. It does not run those fences. The same command runs MyST code cells. A cell that calls `DisplayUSD` still flattens the stage. The `usd2gltf` converter is intercepted and counted. It is not run.

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
| 2 | Setup or coverage problem, such as a missing corpus, a docs folder with no ordinary python fences and no code cells, or a code cell that needs an LFS pointer file |
| 3 | Unexpected error in the tool |

If more than one applies, the code is the most serious: 3, then 2, then 1, then 0.

Exit code 0 does not mean every page is healthy. Pages with skipped checks stay incomplete.

## Results

Counts below are findings, not pages. A finding is one dotted name that resolved, one fence that failed to parse, or one code cell. The corpus SHA is `fcbb129ca9c4fe01bd3564c2ca6844c37d85c9c2`. The USD version is 26.11.

### Fences only

Static check of ordinary `python` fences. These numbers do not include code cells.

| Item | Value |
|---|---|
| Passed | 65 |
| Failed | 1 |
| Skipped | 0 |

The failure is `vendor/learnopenusd/docs/composition-basics/references.md`, line 86. A `python` fence there holds USDA text, `def Xform "World"`. Python 3.12 reports `expected '('`. No missing USD symbol was reported.

`skipped 0` means the static check has no skip outcome. `{include}` and `literalinclude` directives, and names such as `prim.GetReferences()`, are outside the count.

### Fences and code cells

On that same corpus, after `git -C vendor/learnopenusd lfs pull`, the check command printed:

```text
passed 208, failed 1, skipped 0
usd2gltf calls 32
```

The one failure is the same fence, `references.md` line 86, `expected '('`. No code cell failed. The 208 includes the fence findings and the code-cell findings. It does not replace the fence-only table. `usd2gltf calls 32` counts intercepted converter calls. That tally is not part of the 208, and it is not a pass of the glTF conversion.

A green CI run means pytest passed and the corpus check finished with exit code 0 or 1. Exit code 1 means a fence or a code cell failed. It does not mean every lesson passed. CI runs `git -C vendor/learnopenusd lfs pull` before that check. If a code cell still needs a pointer file, the check exits 2.

## Limitations

- Code cells run from the check command. `usd2gltf` is intercepted and counted. A code cell that needs a Git LFS pointer file is exit 2, a setup problem, not a failed example.
- Ordinary `python` fences are parsed and checked for module-dotted names. A fence that does not parse fails. The modules in this version are `Usd`, `Sdf`, `UsdGeom`, `UsdShade`, and `UsdLux`. The fence check does not run the code.
- Lesson assets in Git LFS are not required for the static check. CI pulls those assets before the corpus check.
- A failure on 26.11 shows that an example failed on that release. It does not show that 26.11 caused the failure. There is no 25.11 run to compare against.
- Links, prose, `{include}` and `literalinclude` directives, and instance methods such as `prim.GetReferences()` are outside this version.
- There is no score and no hosted dashboard.
