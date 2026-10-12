# Contributing

Thanks for considering a contribution.

## Ground rules

- Python 3.10+, **standard library only** — no new dependencies without a strong justification in an issue first.
- Every behavior change needs a test. Run `python -m unittest discover -s tests -t . -v` from the repo root and keep it green.
- Lint rule ids are stable: never renumber existing rules; add new ids at the end.
- Keep CLI output deterministic (sorted where applicable) so `results/` artifacts stay reproducible.

## Workflow

1. Fork and create a feature branch.
2. Add or update tests alongside the change.
3. Update `docs/USAGE.md` / README rule table if user-visible behavior changes.
4. Open a pull request describing the motivation and the observed before/after behavior.

## Reporting bugs

Include the exact command, the file that triggered the issue (redact private content), the expected rule/report, and your Python version.
