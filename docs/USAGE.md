# Usage

All examples assume PowerShell from the repository root with `$env:PYTHONPATH = "src"`.

## new — scaffold a skill

```shell
python -m skillmint new --name release-checklist `
  --description "Use when preparing a release branch for tagging" `
  --triggers "release,tag,version bump" --category release `
  -o .\release-checklist
```

Creates `release-checklist/SKILL.md`. The scaffold is guaranteed to pass `lint` with zero errors.

## lint — validate a file or corpus

```shell
python -m skillmint lint .\release-checklist
python -m skillmint lint .\skills --format json
python -m skillmint lint .\skills --strict
```

- Directories are walked recursively for `*.md` files.
- `--format json` prints `{findings: [...], files, errors, warnings}`.
- `--strict` promotes warnings to failure for exit-code purposes.
- Exit codes: `0` clean (errors absent), `1` errors (or warnings with `--strict`), `2` usage/IO error.

### Rule reference

See the lint rules table in [README.md](../README.md). Each finding message starts with its rule id (e.g. `SK-003 description is 1200 characters (max 1024)`).

## convert — prompt block or tool description

```shell
python -m skillmint convert .\skills\markdown-tidy\SKILL.md --to prompt
python -m skillmint convert .\skills\markdown-tidy\SKILL.md --to tool
python -m skillmint convert .\skills\markdown-tidy\SKILL.md --to tool --format json
```

JSON mode for `--to tool` includes `length` (rendered) and `original_length` (before truncation).

## search — keyword search over a corpus

```shell
python -m skillmint search .\skills "markdown style"
python -m skillmint search .\skills "release" --limit 5 --format json
```

Scoring: name ×3, description ×2, body ×1 per matching query word; ties break alphabetically by skill name.

## CI example

```yaml
- name: Lint skills
  run: |
    export PYTHONPATH=src
    python -m skillmint lint skills/ --format json --strict
```

The bundled example corpus contains an *intentionally broken* skill, so linting `examples/skills` exits `1` by design (see `results/lint-report.txt`).
