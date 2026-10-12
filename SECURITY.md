# Security policy

## Authorized use

skillmint reads and writes only the local paths you pass to it. Lint skill files you **own or are authorized to modify**. Do not point it at other people's private repositories without permission.

## Safety properties

- **No network access.** The tool never makes HTTP(S) or any other network calls.
- **No code execution.** Skill files are parsed as text; their contents are never imported, evaluated, or executed.
- **No telemetry.** Nothing is uploaded or logged off-machine.
- **Secrets.** Do not put real credentials in skill files; the linter will happily read them as text. Keep private skills in private repositories.

## Agent context

SKILL.md files are instructions that *coding agents* execute. Treat an untrusted skill file like untrusted code: review it (skillmint's lint helps with structure, not with intent) before installing it into an agent's skill directory.

## Reporting issues

Report suspected vulnerabilities in skillmint itself via GitHub security advisories on this repository (or a private message to the maintainer if advisories are unavailable). Please do not open a public issue for exploitable bugs.
