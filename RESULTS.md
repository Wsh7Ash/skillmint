# Results

## Environment
- OS: Windows 11 (PowerShell)
- Runtime: Python 3.14.3 (mingw64 build)
- Dependency manager: none — standard library only; no pip installs performed

## Validation performed
- install: N/A (no-install `PYTHONPATH=src` route used; `pip install -e .` not attempted on this PEP 668 managed Python)
- build: N/A (interpreted, no build step)
- unit tests: **PASS** — `Ran 53 tests in 0.216s — OK`, exit 0
- integration tests: N/A (covered by CLI tests in-process)
- lint: N/A for third-party linters (none installed); the tool's own lint demo below
- type check: N/A
- demo run: **PASS** — all five demo commands executed, exit codes as expected (see below)

## Commands executed
```shell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -t . -v
python -m skillmint lint examples\skills --format text            # exit 1 (broken example present, by design)
python -m skillmint lint examples\skills --format json
python -m skillmint new --name demo-skill --description "Use when the user wants a demo of skillmint scaffolding" --triggers "demo scaffold,new skill" -o .\examples\generated-demo
python -m skillmint lint .\examples\generated-demo                # exit 0 (round-trip guarantee)
python -m skillmint convert examples\skills\markdown-tidy\SKILL.md --to prompt
python -m skillmint convert examples\skills\markdown-tidy\SKILL.md --to tool
python -m skillmint search examples\skills "markdown style"
```

## Observed result
- Unit tests: `Ran 53 tests ... OK` (parser 14, lint 17, CLI/search/convert 22 across three modules), exit 0.
- `lint examples/skills` → `checked 2 file(s): 4 error(s), 1 warning(s)`, exit 1 (intentionally broken `examples/skills/broken-skill`).
- `lint examples/generated-demo` → `checked 1 file(s): 0 error(s), 1 warning(s)` (SK-005 name/dir mismatch because the output directory was named `generated-demo`), exit 0 — scaffold round-trip holds.
- `search "markdown style"` → `14 markdown-tidy [name, description, body]`.
- `convert --to tool` → single line, 186 chars, under the 1024 cap.

## Generated artifacts
- `results/lint-report.txt`, `results/lint-report.json`
- `results/convert-prompt.txt`, `results/convert-tool.txt`
- `results/search.txt`
- `examples/generated-demo/SKILL.md` (scaffold output, lints clean)

## Known limitations
- The minimal YAML parser rejects nested maps by design (reported as SK-001).
- SK-006/SK-011 keyword lists are English heuristics and can false-positive (e.g. the word "trigger" satisfies SK-011).
- `pip install -e .` was not verified on this machine; the documented no-install route is what ran.
