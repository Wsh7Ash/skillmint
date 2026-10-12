"""Lint rules for SKILL.md files."""

import os
import re

from . import frontmatter

KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PLACEHOLDERS = ("TODO", "TBD", "FIXME", "XXX", "lorem ipsum", "...replace")
TRIGGER_PHRASES = ("use when", "trigger", "when to", "use for", "called when")
MAX_DESCRIPTION = 1024
MAX_FILE_BYTES = 50 * 1024
ERROR = "error"
WARNING = "warning"

RULES = {
    "SK-001": ("missing or unterminated front-matter", ERROR),
    "SK-002": ("missing or empty description", ERROR),
    "SK-003": ("description longer than 1024 characters", ERROR),
    "SK-004": ("name missing or not kebab-case", ERROR),
    "SK-005": ("name differs from directory name", WARNING),
    "SK-006": ("placeholder text left in skill file", ERROR),
    "SK-007": ("body has no level-2 heading", ERROR),
    "SK-008": ("level-2 section has an empty body", WARNING),
    "SK-009": ("control character in front-matter value", ERROR),
    "SK-010": ("file larger than 50 KB", WARNING),
    "SK-011": ("description lacks trigger language", WARNING),
}


class Finding(object):
    def __init__(self, rule, message, line=None, severity=None):
        self.rule = rule
        self.message = message
        self.line = line
        self.severity = severity or RULES[rule][1]

    def to_dict(self, path):
        out = {
            "file": path.replace("\\", "/"),
            "rule": self.rule,
            "severity": self.severity,
            "message": self.message,
        }
        if self.line is not None:
            out["line"] = self.line
        return out


def _control_chars(text):
    return [ch for ch in text if ord(ch) < 32 and ch not in ("\t", "\n", "\r")]


def _empty_h2_sections(body, body_offset):
    """Yield line numbers of '##' headings whose section body is empty."""
    lines = body.splitlines()
    headings = []
    for i, line in enumerate(lines):
        if line.startswith("## "):
            headings.append((i, line.strip()))
    for idx, (i, heading) in enumerate(headings):
        start = i + 1
        end = headings[idx + 1][0] if idx + 1 < len(headings) else len(lines)
        content = [ln for ln in lines[start:end] if ln.strip()]
        if not content:
            yield body_offset + i, heading


def lint_text(text, path="SKILL.md", dir_name=None):
    """Lint one skill file's text; return a list of Finding objects."""
    findings = []
    meta = None
    body = ""
    body_offset = 1

    try:
        meta, body, body_offset = frontmatter.parse(text)
    except frontmatter.FrontMatterError as exc:
        findings.append(Finding("SK-001", "SK-001 %s" % exc, line=exc.line))
        return findings

    description = meta.get("description")
    if not isinstance(description, str) or description.strip() == "":
        findings.append(Finding("SK-002", "SK-002 description is missing or empty"))
    else:
        if len(description) > MAX_DESCRIPTION:
            findings.append(
                Finding(
                    "SK-003",
                    "SK-003 description is %d characters (max %d)" % (len(description), MAX_DESCRIPTION),
                )
            )
        lowered = description.lower()
        if not any(phrase in lowered for phrase in TRIGGER_PHRASES):
            findings.append(
                Finding(
                    "SK-011",
                    "SK-011 description should say when to use the skill "
                    "(contains none of: %s)" % ", ".join(TRIGGER_PHRASES),
                )
            )

    name = meta.get("name")
    if not isinstance(name, str) or not KEBAB_RE.match(name):
        findings.append(
            Finding("SK-004", "SK-004 name %r is missing or not kebab-case" % (name,))
        )
    elif dir_name and name != dir_name:
        findings.append(
            Finding(
                "SK-005",
                "SK-005 name %r does not match directory name %r" % (name, dir_name),
            )
        )

    fm_text = text.split("---", 2)[1] if text.count("---") >= 2 else text
    ctrl = _control_chars(fm_text)
    if ctrl:
        findings.append(
            Finding(
                "SK-009",
                "SK-009 control characters in front-matter: %s"
                % ", ".join("U+%04X" % ord(ch) for ch in ctrl[:5]),
            )
        )

    body_upper = text
    for token in PLACEHOLDERS:
        for i, line in enumerate(text.splitlines(), start=1):
            if token.lower() in line.lower():
                findings.append(
                    Finding("SK-006", "SK-006 placeholder %r found" % token, line=i)
                )
                break

    if not any(line.startswith("## ") for line in body.splitlines()):
        findings.append(Finding("SK-007", "SK-007 body has no '## ' heading"))

    for line_no, heading in _empty_h2_sections(body, body_offset):
        findings.append(
            Finding("SK-008", "SK-008 empty section %r" % heading, line=line_no)
        )

    if len(text.encode("utf-8")) > MAX_FILE_BYTES:
        findings.append(Finding("SK-010", "SK-010 file is larger than 50 KB"))

    return findings


def lint_path(path, dir_name=None):
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    if dir_name is None:
        dir_name = os.path.basename(os.path.dirname(os.path.abspath(path)))
    return lint_text(text, path=path, dir_name=dir_name)


def collect_markdown(paths):
    """Expand files/directories into a sorted list of .md paths."""
    found = []
    for path in paths:
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                dirs[:] = sorted(d for d in dirs if not d.startswith("."))
                for fname in sorted(files):
                    if fname.endswith(".md"):
                        found.append(os.path.join(root, fname))
        else:
            found.append(path)
    return sorted(found)
