import contextlib
import io
import json
import os
import tempfile
import unittest

from skillmint import convert, scaffold, search
from skillmint.cli import main


def run_cli(argv):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


class ConvertTests(unittest.TestCase):
    def test_to_prompt_contains_meta_and_body(self):
        text = scaffold.build_skill("demo-skill", "Use when converting prompts")
        out = convert.to_prompt(text)
        self.assertIn("# Skill instructions", out)
        self.assertIn("name: demo-skill", out)
        self.assertIn("## Workflow", out)

    def test_to_tool_single_line(self):
        text = scaffold.build_skill(
            "demo-skill", "Use when converting to a tool", triggers=["alpha", "beta"]
        )
        out, original = convert.to_tool(text)
        self.assertNotIn("\n", out)
        self.assertIn("Triggers: alpha, beta.", out)
        self.assertLessEqual(len(out), 1024)
        self.assertEqual(original, len(out))

    def test_to_tool_truncates_long_description(self):
        long_desc = "Use when " + ("word " * 400)
        text = scaffold.build_skill("demo-skill", long_desc)
        out, original = convert.to_tool(text)
        self.assertLessEqual(len(out), 1024)
        self.assertGreater(original, 1024)
        self.assertTrue(out.endswith("…"))


class SearchTests(unittest.TestCase):
    def test_search_ranks_name_match_higher(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name, desc in (
                ("alpha-skill", "Use when handling alpha tasks"),
                ("beta-skill", "Use when handling general tasks"),
            ):
                d = os.path.join(tmp, name)
                os.makedirs(d)
                with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as handle:
                    handle.write(scaffold.build_skill(name, desc))
            results = search.search_corpus(tmp, "alpha")
            self.assertGreaterEqual(len(results), 1)
            self.assertEqual(results[0]["name"], "alpha-skill")
            self.assertIn("name", results[0]["matched"])

    def test_search_no_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = os.path.join(tmp, "beta-skill")
            os.makedirs(d)
            with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as handle:
                handle.write(scaffold.build_skill("beta-skill", "Use when handling beta"))
            self.assertEqual(search.search_corpus(tmp, "zebra"), [])

    def test_search_deterministic_tiebreak(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("aaa-skill", "bbb-skill"):
                d = os.path.join(tmp, name)
                os.makedirs(d)
                with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as handle:
                    handle.write(scaffold.build_skill(name, "Use when demoing ties"))
            results = search.search_corpus(tmp, "demoing")
            self.assertEqual([r["name"] for r in results], ["aaa-skill", "bbb-skill"])


class CliTests(unittest.TestCase):
    def test_new_then_lint_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = os.path.join(tmp, "roundtrip-skill")
            code, out, _ = run_cli(
                [
                    "new",
                    "--name",
                    "roundtrip-skill",
                    "--description",
                    "Use when checking the scaffold round trip",
                    "-o",
                    out_dir,
                ]
            )
            self.assertEqual(code, 0)
            self.assertIn("created", out)
            code, out, _ = run_cli(["lint", out_dir])
            self.assertEqual(code, 0, out)
            self.assertIn("0 error(s)", out)

    def test_lint_examples_dir(self):
        examples = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples", "skills")
        code, out, _ = run_cli(["lint", examples])
        self.assertEqual(code, 1)
        self.assertIn("SK-00", out)

    def test_lint_json_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = os.path.join(tmp, "bad-skill")
            os.makedirs(bad)
            with open(os.path.join(bad, "SKILL.md"), "w", encoding="utf-8") as handle:
                handle.write("# no front matter\n")
            code, out, _ = run_cli(["lint", bad, "--format", "json"])
            self.assertEqual(code, 1)
            payload = json.loads(out)
            self.assertIn("findings", payload)
            self.assertEqual(payload["errors"], 1)
            self.assertEqual(payload["findings"][0]["rule"], "SK-001")

    def test_lint_strict_promotes_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = os.path.join(tmp, "warn-skill")
            os.makedirs(d)
            with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as handle:
                handle.write(scaffold.build_skill("warn-skill", "A skill about widgets and gadgets"))
            code, _, _ = run_cli(["lint", d])
            self.assertEqual(code, 0)
            code, _, _ = run_cli(["lint", d, "--strict"])
            self.assertEqual(code, 1)

    def test_lint_no_files_is_usage_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty = os.path.join(tmp, "empty")
            os.makedirs(empty)
            code, _, err = run_cli(["lint", empty])
            self.assertEqual(code, 2)
            self.assertIn("no markdown files", err)

    def test_convert_prompt_json(self):
        examples = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "examples", "skills", "markdown-tidy", "SKILL.md"
        )
        code, out, _ = run_cli(["convert", examples, "--to", "prompt", "--format", "json"])
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["to"], "prompt")
        self.assertIn("## Workflow", payload["text"])

    def test_convert_tool_text(self):
        examples = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "examples", "skills", "markdown-tidy", "SKILL.md"
        )
        code, out, _ = run_cli(["convert", examples, "--to", "tool"])
        self.assertEqual(code, 0)
        self.assertNotIn("\n", out.strip())

    def test_convert_missing_file(self):
        code, _, err = run_cli(["convert", "does/not/exist.md", "--to", "tool"])
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)

    def test_convert_invalid_front_matter(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "SKILL.md")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("---\nbroken line without colon\n---\n## A\n\nb\n")
            code, _, err = run_cli(["convert", path, "--to", "prompt"])
            self.assertEqual(code, 2)
            self.assertIn("error", err)

    def test_search_cli(self):
        examples = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples", "skills")
        code, out, _ = run_cli(["search", examples, "markdown"])
        self.assertEqual(code, 0)
        self.assertIn("markdown-tidy", out)

    def test_search_cli_json(self):
        examples = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples", "skills")
        code, out, _ = run_cli(["search", examples, "lint", "--format", "json"])
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["query"], "lint")
        self.assertIsInstance(payload["results"], list)

    def test_search_missing_corpus(self):
        code, _, err = run_cli(["search", "no/such/dir", "x"])
        self.assertEqual(code, 2)
        self.assertIn("corpus directory not found", err)


if __name__ == "__main__":
    unittest.main()
