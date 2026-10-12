# Architecture

## Overview

skillmint is a single Python package with five modules behind one argparse CLI. Everything is standard library; there is no plugin system and no I/O beyond the filesystem paths the user passes in.

```text
cli.py
  ├─ frontmatter.parse / format_front_matter
  ├─ lint.lint_text / lint_path / collect_markdown
  ├─ scaffold.build_skill / write_skill
  ├─ convert.to_prompt / to_tool
  └─ search.search_corpus
```

## Front-matter parser (`frontmatter.py`)

Skills use a YAML front-matter subset. The parser walks lines between the opening and closing `---` markers and accepts:

- `key: value` scalars (plain, single-quoted with `''` escapes, double-quoted with `\"` and `\\` escapes)
- booleans (`true`/`false`) and `null`/`~` → Python `None`
- inline lists `key: [a, b, "c d"]`
- block lists:
  ```yaml
  triggers:
    - one
    - two
  ```
- blank lines and `#` comments; trailing comments after unquoted scalars

Anything else (tabs, nested maps, orphan list items, unquoted multi-word lines) raises `FrontMatterError` with a line number. The linter maps that to a single SK-001 finding, so a malformed file produces one actionable error instead of a traceback.

`parse` returns `(meta, body, body_start_line)`; `body_start_line` is the 1-based line number of the first body line, used for finding line numbers.

## Lint engine (`lint.py`)

Rules are pure functions of `(text, dir_name)` returning a list of `Finding` objects with stable ids. Severity drives the exit code:

- exit `1` if any **error**-severity finding exists, or if `--strict` and any warning exists
- exit `0` otherwise
- exit `2` for usage/IO problems (no files found, unreadable path)

`Finding.to_dict` produces the JSON report shape: `{file, rule, severity, message, line?}`, sorted for deterministic output.

## Scaffold (`scaffold.py`)

`build_skill` renders front-matter via `format_front_matter` plus a body with `##` sections (When to use / Workflow / Inputs / Output / Safety notes). Template wording deliberately avoids SK-006 placeholder tokens and includes an English "Use when…" sentence so a fresh scaffold lints with zero errors (the round-trip is asserted in the test suite and in the demo run).

## Converters (`convert.py`)

- `to_prompt` folds every front-matter key into a readable bullet list under `# Skill instructions`, then appends the full body — suitable for pasting into a system prompt.
- `to_tool` joins `description`, `triggers`, and the first `#` heading into one line and truncates on a word boundary at 1024 characters (the common tool-description cap), returning the original length for reporting.

## Search (`search.py`)

Tokenizes name, description, and body with a `[a-z0-9]+` word regex. Score = 3× name hits + 2× description hits + 1× body hits (per distinct query word present). Results sort by `(-score, name)` for determinism.

## Test layout

`tests/__init__.py` inserts `<repo>/src` on `sys.path` so `python -m unittest discover -s tests -t .` works from the repository root with no environment variables. CLI tests call `skillmint.cli.main` in-process with redirected stdout/stderr to assert exit codes and output shapes.
