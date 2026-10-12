"""Convert a SKILL.md into a system-prompt block or a tool description."""

from . import frontmatter

MAX_TOOL_LEN = 1024


def to_prompt(text):
    """Fold front-matter into a readable system-prompt block plus body."""
    meta, body, _ = frontmatter.parse(text)
    lines = ["# Skill instructions"]
    for key in sorted(meta):
        value = meta[key]
        if isinstance(value, list):
            lines.append("- %s: %s" % (key, ", ".join(str(v) for v in value)))
        else:
            lines.append("- %s: %s" % (key, value))
    lines.append("")
    lines.append(body.strip())
    return "\n".join(lines) + "\n"


def _truncate(text, limit=MAX_TOOL_LEN):
    if len(text) <= limit:
        return text, len(text)
    cut = text[: limit - 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip() + "…", len(text)


def to_tool(text):
    """Render a single-line tool description capped at 1024 characters."""
    meta, body, _ = frontmatter.parse(text)
    description = str(meta.get("description", "")).strip()
    triggers = meta.get("triggers") or []
    if isinstance(triggers, str):
        triggers = [triggers]
    parts = [description]
    if triggers:
        parts.append("Triggers: %s." % ", ".join(str(t) for t in triggers))
    heading = _first_h1(body)
    if heading:
        parts.append("Skill: %s." % heading)
    joined = " ".join(p for p in parts if p)
    return _truncate(joined)


def _first_h1(body):
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None
