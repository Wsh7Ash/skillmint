"""Command-line interface for skillmint."""

import argparse
import json
import os
import sys

from . import __version__, convert, lint, scaffold, search as search_mod


def _print_json(payload):
    print(json.dumps(payload, indent=2, sort_keys=True))


def cmd_new(args):
    directory = args.output or args.name
    path = scaffold.write_skill(
        directory,
        args.name,
        args.description,
        triggers=args.triggers.split(",") if args.triggers else None,
        category=args.category,
    )
    print("created %s" % path.replace("\\", "/"))
    return 0


def cmd_lint(args):
    paths = lint.collect_markdown(args.paths)
    if not paths:
        print("error: no markdown files found", file=sys.stderr)
        return 2
    all_findings = []
    for path in paths:
        try:
            findings = lint.lint_path(path)
        except OSError as exc:
            print("error: cannot read %s: %s" % (path, exc), file=sys.stderr)
            return 2
        all_findings.extend((path, finding) for finding in findings)

    strict_errors = args.strict
    errors = [item for item in all_findings if item[1].severity == lint.ERROR]
    warnings = [item for item in all_findings if item[1].severity == lint.WARNING]

    if args.format == "json":
        payload = [finding.to_dict(path) for path, finding in all_findings]
        payload.sort(key=lambda item: (item["file"], item["rule"]))
        _payload = {
            "findings": payload,
            "files": len(paths),
            "errors": len(errors),
            "warnings": len(warnings),
        }
        print(json.dumps(_payload, indent=2, sort_keys=True))
    else:
        by_file = {}
        for path, finding in all_findings:
            by_file.setdefault(path, []).append(finding)
        for path in sorted(by_file):
            print(path.replace("\\", "/"))
            for finding in sorted(by_file[path], key=lambda f: f.rule):
                loc = ":%d" % finding.line if finding.line is not None else ""
                print("  %s [%s] %s%s" % (finding.severity, finding.rule, finding.message, loc))
        print(
            "checked %d file(s): %d error(s), %d warning(s)"
            % (len(paths), len(errors), len(warnings))
        )

    if errors or (strict_errors and warnings):
        return 1
    return 0


def cmd_convert(args):
    try:
        with open(args.file, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        print("error: cannot read %s: %s" % (args.file, exc), file=sys.stderr)
        return 2
    try:
        if args.to == "prompt":
            output = convert.to_prompt(text)
            if args.format == "json":
                _payload = {"to": "prompt", "text": output}
                print(json.dumps(_payload, indent=2, sort_keys=True))
            else:
                print(output, end="")
        else:
            text_out, original_len = convert.to_tool(text)
            if args.format == "json":
                _payload = {
                    "to": "tool",
                    "text": text_out,
                    "length": len(text_out),
                    "original_length": original_len,
                }
                print(json.dumps(_payload, indent=2, sort_keys=True))
            else:
                print(text_out)
    except Exception as exc:  # front-matter errors surface as usage problems
        print("error: %s" % exc, file=sys.stderr)
        return 2
    return 0


def cmd_search(args):
    if not os.path.isdir(args.corpus):
        print("error: corpus directory not found: %s" % args.corpus, file=sys.stderr)
        return 2
    results = search_mod.search_corpus(args.corpus, args.query, limit=args.limit)
    if args.format == "json":
        print(json.dumps({"query": args.query, "results": results}, indent=2, sort_keys=True))
    else:
        if not results:
            print("no matches for %r" % args.query)
        for item in results:
            print(
                "%5d  %s  [%s]  %s"
                % (item["score"], item["name"], ", ".join(item["matched"]), item["path"])
            )
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="skillmint",
        description="Offline toolkit for authoring AI agent SKILL.md files.",
    )
    parser.add_argument("--version", action="version", version="skillmint %s" % __version__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new", help="scaffold a new SKILL.md")
    p_new.add_argument("--name", required=True, help="kebab-case skill name")
    p_new.add_argument("--description", required=True, help="one-line description (say when to use it)")
    p_new.add_argument("-o", "--output", help="output directory (default: ./<name>)")
    p_new.add_argument("--triggers", help="comma-separated trigger phrases")
    p_new.add_argument("--category", help="optional category label")
    p_new.set_defaults(func=cmd_new)

    p_lint = sub.add_parser("lint", help="lint SKILL.md files or directories")
    p_lint.add_argument("paths", nargs="+", help="files or directories")
    p_lint.add_argument("--format", choices=("text", "json"), default="text")
    p_lint.add_argument("--strict", action="store_true", help="treat warnings as errors for exit code")
    p_lint.set_defaults(func=cmd_lint)

    p_conv = sub.add_parser("convert", help="convert a skill to a prompt block or tool description")
    p_conv.add_argument("file", help="path to SKILL.md")
    p_conv.add_argument("--to", choices=("prompt", "tool"), required=True)
    p_conv.add_argument("--format", choices=("text", "json"), default="text")
    p_conv.set_defaults(func=cmd_convert)

    p_search = sub.add_parser("search", help="keyword search over a skill corpus")
    p_search.add_argument("corpus", help="corpus directory")
    p_search.add_argument("query", help="search query")
    p_search.add_argument("--limit", type=int, default=10)
    p_search.add_argument("--format", choices=("text", "json"), default="text")
    p_search.set_defaults(func=cmd_search)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
