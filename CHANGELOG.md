# Changelog

## 0.1.0 — 2026-10-12

Initial release.

- `new` scaffold command producing skills that lint clean
- `lint` with rules SK-001…SK-011, text/JSON formats, `--strict`, exit codes 0/1/2
- `convert --to prompt|tool` with 1024-char tool-description cap
- `search` weighted keyword ranking over a skill corpus
- Minimal YAML front-matter parser (documented subset)
- Example corpus (valid + intentionally broken skill), 53 unit tests, CI workflow
