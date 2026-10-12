# skillmint

**Offline toolkit for authoring AI agent `SKILL.md` files — scaffold, lint, convert, and search your local skill corpus with zero dependencies.**

Skill files (YAML front-matter + Markdown instruction body, as used by coding agents such as opencode and Claude Code) fail *silently* at runtime when the front-matter is broken, the description is missing or too long, or placeholder text is left behind. `skillmint` gives skill authors a fast, offline validation loop before the skill ever reaches an agent.

## Features

- **`new`** — scaffold a valid `SKILL.md` (front-matter + useful body sections) that already passes the linter.
- **`lint`** — 11 deterministic rules with stable ids (`SK-001`…`SK-011`), error/warning severities, text and JSON reports, strict mode, meaningful exit codes.
- **`convert`** — fold a skill into a system-prompt block (`--to prompt`) or a single-line tool description capped at 1024 chars (`--to tool`).
- **`search`** — weighted keyword search (name ×3, description ×2, body ×1) over a corpus of skill files.
- **Standard library only** — Python 3.10+, no pip installs, no network.

## Real terminal output

```text
$ python -m skillmint lint examples/skills --format text
examples/skills/broken-skill/SKILL.md
  error [SK-001] SK-001 SK-001 description is missing or empty   (truncated for brevity)
  ...
  warning [SK-011] SK-011 description should say when to use the skill (contains none of: use when, trigger, when to, use for, called when)
examples/skills/markdown-tidy/SKILL.md
checked 2 file(s): 4 error(s), 1 warning(s)
exit=1

$ python -m skillmint search examples/skills "markdown style"
   14  markdown-tidy  [name, description, body]  examples/skills/markdown-tidy/SKILL.md

$ python -m skillmint convert examples/skills/markdown-tidy/SKILL.md --to tool
Use when the user wants consistent Markdown style fixes across a docs folder Triggers: tidy markdown, normalize headings, markdown style. Skill: markdown-tidy.
```

Full transcripts are committed under [`results/`](results/).

## Architecture

```text
CLI (argparse)
 ├─ frontmatter.py   minimal YAML front-matter parser (scalars, quoted strings, inline + block lists)
 ├─ lint.py          rule engine SK-001..SK-011, text/JSON reporting
 ├─ scaffold.py      generates skills that lint without errors
 ├─ convert.py       prompt block / tool description renderers
 └─ search.py        weighted keyword ranking over a corpus
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

## Requirements

- Python 3.10+ (developed and tested on 3.14)
- No third-party packages

## Installation

No install required. From a clone:

```shell
$env:PYTHONPATH = "src"          # PowerShell
python -m skillmint --help
```

(`pip install -e .` also works where your environment allows editable installs; this repo's demos were run via the no-install route above.)

## Quick start

```shell
$env:PYTHONPATH = "src"
python -m skillmint new --name release-checklist --description "Use when preparing a release branch" -o .\release-checklist
python -m skillmint lint .\release-checklist
python -m skillmint lint .\skills\ --format json
python -m skillmint convert .\release-checklist\SKILL.md --to prompt
python -m skillmint search .\skills "release"
```

## Usage examples

- **Corpus health check in CI:** `python -m skillmint lint skills/ --format json --strict` — fails the build on errors (and, with `--strict`, warnings).
- **Embedding a skill in a system prompt:** `python -m skillmint convert skills/db-migrate/SKILL.md --to prompt`.
- **Tool descriptions:** `--to tool` renders a single line suitable for a tool registry, truncated safely at 1024 characters (original length reported in JSON).

## Lint rules

| Id | Severity | Check |
|---|---|---|
| SK-001 | error | missing / unterminated front-matter |
| SK-002 | error | missing or empty `description` |
| SK-003 | error | `description` > 1024 characters |
| SK-004 | error | `name` missing or not kebab-case |
| SK-005 | warning | `name` differs from directory name |
| SK-006 | error | placeholder leftovers (TODO / TBD / FIXME / XXX / lorem ipsum / …) |
| SK-007 | error | body has no `##` heading |
| SK-008 | warning | `##` section with an empty body |
| SK-009 | error | control characters in front-matter values |
| SK-010 | warning | file larger than 50 KB |
| SK-011 | warning | `description` lacks trigger language ("use when", "trigger", …) |

Exit codes: `0` no errors (warnings allowed unless `--strict`), `1` errors found, `2` usage/IO error.

## Testing

```shell
python -m unittest discover -s tests -t . -v
```

53 tests cover the parser, every rule (positive and negative cases), the scaffold→lint round-trip, converters, search ranking, and CLI exit codes.

## Project structure

```text
src/skillmint/          package (cli, frontmatter, lint, scaffold, convert, search)
tests/                  unittest suite (adds src/ to sys.path itself)
examples/skills/        one valid skill + one intentionally broken skill
examples/generated-demo scaffold produced by the demo run
docs/                   PROJECT_SPEC, ARCHITECTURE, USAGE
results/                captured demo outputs
```

## Limitations

- The YAML front-matter parser supports a **documented subset** (scalars, quoted strings, inline lists, block lists, comments). Nested maps and multi-line scalars raise a clean SK-001 finding rather than parsing.
- Rules are **heuristic**: SK-006/SK-011 keyword lists can false-positive or miss paraphrases; SK-011 checks English trigger phrases only.
- `search` is keyword-based, not semantic.
- `convert --to tool` truncates at 1024 characters on a word boundary by design.

## Roadmap

- Per-runtime presets (opencode vs Claude Code front-matter differences).
- Corpus diff mode (what changed between two skill revisions).
- Optional semantic ranking when an embedding backend is supplied locally.

## Security notes

skillmint only reads and writes the files you point it at, never executes skill content, and makes no network calls. Skills themselves are instructions executed by *agents* — lint only skill files you own or are authorized to modify. See [SECURITY.md](SECURITY.md).

## License

MIT — see [LICENSE](LICENSE).
