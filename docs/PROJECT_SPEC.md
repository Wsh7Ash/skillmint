# Project spec — skillmint

- **Name:** skillmint
- **Category:** ai-skill
- **Target user:** an author maintaining a local corpus of AI agent skill files (SKILL.md for opencode / Claude Code style agents).
- **Problem:** skill files fail silently at runtime when front-matter is missing, descriptions are vague or too long, or placeholder text is left behind; authors have no offline validation loop.
- **Solution:** a stdlib-only CLI that scaffolds valid skills, lints a corpus with stable rule ids, converts skills into system-prompt blocks and tool descriptions, and keyword-searches the corpus.
- **Core workflow:** `new` a skill → `lint` the corpus → `convert` for embedding → `search` to reuse.
- **Must-have features:** minimal YAML front-matter parser; 11 deterministic lint rules (SK-001..SK-011) with error/warning severities and stable exit codes; scaffold that lints clean; prompt/tool converters with a 1024-char cap; weighted keyword search; text + JSON output.
- **Nice-to-have features (not in 0.1.0):** semantic/embedded search, corpus-wide cross-link checking, per-runtime skill format presets.
- **Stack:** Python 3.10+ standard library only; unittest; no third-party dependencies.
- **Test strategy:** 53 unittest cases over the parser, every rule (positive + negative), scaffold round-trip, converters, search ranking, and CLI exit codes.
- **Demo/result strategy:** real CLI runs over `examples/skills/` (valid + intentionally broken) captured under `results/`.
- **Safety considerations:** lints only local files the user points it at; no network; no code execution of skill content. See SECURITY.md.
- **Definition of done:** all tests green, demo commands verified, examples included, docs and RESULTS.md match observed behavior.
