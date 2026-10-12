"""SKILL.md scaffolding."""

from .frontmatter import format_front_matter

_BODY = """# {name}

## When to use this skill

Use when the user asks for {purpose}.

## Workflow

1. Confirm the user's goal matches this skill.
2. Collect the required inputs listed below.
3. Perform the task step by step, checking results as you go.
4. Report the outcome and any limitations clearly.

## Inputs

- List the files, flags, or context this skill needs.

## Output

- Describe what the skill produces: a report, a file, a command result.

## Safety notes

- Only operate on data the user owns or is authorized to modify.
- Ask for confirmation before any destructive or irreversible action.
- Never embed secrets or credentials in skill output.
"""


def build_skill(name, description, triggers=None, category=None):
    """Return the text of a new SKILL.md that lints without errors."""
    meta = {"name": name, "description": description}
    if category:
        meta["category"] = category
    if triggers:
        meta["triggers"] = list(triggers)
    purpose = description.rstrip(".")
    if purpose.lower().startswith("use when "):
        purpose = purpose[len("use when ") :]
    text = format_front_matter(meta)
    text += "\n" + _BODY.format(name=name, purpose=purpose)
    return text


def write_skill(directory, name, description, triggers=None, category=None):
    """Create ``directory/SKILL.md``; return the written path."""
    import os

    if not os.path.isdir(directory):
        os.makedirs(directory)
    path = os.path.join(directory, "SKILL.md")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(build_skill(name, description, triggers=triggers, category=category))
    return path
