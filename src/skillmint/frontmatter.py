"""Minimal YAML front-matter parser for SKILL.md files (stdlib only).

Supported subset:
- ``key: value`` scalars (plain, single-quoted, double-quoted)
- inline lists: ``key: [a, b, c]``
- block lists:
      key:
        - a
        - b
- ``#`` comments and blank lines
Anything else (tabs, nested maps, multi-line scalars) raises FrontMatterError
so callers can report a clean lint finding instead of crashing.
"""

import re

_KV_RE = re.compile(r"^([A-Za-z0-9_-]+):(.*)$")
_BLOCK_ITEM_RE = re.compile(r"^-\s+(.*)$")
_KEY_START_RE = re.compile(r"[A-Za-z0-9_-]")


class FrontMatterError(Exception):
    """Raised when front-matter cannot be parsed with the supported subset."""

    def __init__(self, message, line=None):
        super().__init__(message)
        self.line = line


def _strip_comment(value):
    """Remove an unquoted trailing ``#`` comment from a scalar value."""
    if not value:
        return value
    quote = None
    for i, ch in enumerate(value):
        if quote:
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
        elif ch == "#" and i > 0 and value[i - 1] in (" ", "\t"):
            return value[:i].rstrip()
    return value


def _parse_scalar(raw, line_no):
    value = _strip_comment(raw.strip())
    if value == "":
        return ""
    if value[0] == value[-1] and len(value) >= 2 and value[0] in ("'", '"'):
        inner = value[1:-1]
        if value[0] == '"':
            inner = inner.replace('\\"', '"').replace("\\\\", "\\")
        else:
            inner = inner.replace("''", "'")
        return inner
    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    if value.lower() in ("null", "~"):
        return None
    return value


def _parse_inline_list(raw, line_no):
    inner = raw.strip()[1:-1].strip()
    if inner == "":
        return []
    items = []
    buf = []
    quote = None
    for ch in inner:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            buf.append(ch)
        elif ch == ",":
            items.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if quote:
        raise FrontMatterError("unterminated quote in inline list", line=line_no)
    items.append("".join(buf))
    return [_parse_scalar(item, line_no) for item in items]


def parse(text):
    """Parse ``---`` delimited front-matter.

    Returns ``(meta, body, body_start_line)`` where ``meta`` is a dict of
    scalars or lists, ``body`` is the text after the closing ``---`` and
    ``body_start_line`` is the 1-based line number of the body's first line.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise FrontMatterError("missing front-matter opening '---'", line=1)
    close_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            close_idx = i
            break
    if close_idx is None:
        raise FrontMatterError("unterminated front-matter (no closing '---')", line=1)

    meta = {}
    current_list_key = None
    for offset, raw_line in enumerate(lines[1:close_idx], start=2):
        if "\t" in raw_line:
            raise FrontMatterError("tab characters are not supported", line=offset)
        stripped = raw_line.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        item_match = _BLOCK_ITEM_RE.match(stripped)
        if item_match:
            if current_list_key is None:
                raise FrontMatterError("list item without a preceding key", line=offset)
            meta[current_list_key].append(_parse_scalar(item_match.group(1), offset))
            continue
        kv = _KV_RE.match(stripped)
        if not kv or not _KEY_START_RE.match(stripped):
            raise FrontMatterError("unsupported front-matter line (expected 'key: value')", line=offset)
        key = kv.group(1)
        rest = kv.group(2).strip()
        if rest == "":
            meta[key] = []
            current_list_key = key
        elif rest.startswith("[") and rest.endswith("]"):
            meta[key] = _parse_inline_list(rest, offset)
            current_list_key = None
        else:
            meta[key] = _parse_scalar(rest, offset)
            current_list_key = None

    body = "\n".join(lines[close_idx + 1 :])
    if text.endswith("\n") and body:
        body += "\n"
    return meta, body, close_idx + 2


def format_front_matter(meta, order=("name", "description", "category", "triggers")):
    """Render a dict back to front-matter text (used by the scaffold)."""
    out = ["---"]
    seen = set()
    for key in order:
        if key not in meta:
            continue
        seen.add(key)
        value = meta[key]
        if isinstance(value, list):
            out.append("%s:" % key)
            for item in value:
                out.append("  - %s" % item)
        else:
            out.append('%s: "%s"' % (key, str(value).replace('"', '\\"')))
    for key in meta:
        if key in seen:
            continue
        value = meta[key]
        if isinstance(value, list):
            out.append("%s:" % key)
            for item in value:
                out.append("  - %s" % item)
        else:
            out.append('%s: "%s"' % (key, str(value).replace('"', '\\"')))
    out.append("---")
    return "\n".join(out) + "\n"
