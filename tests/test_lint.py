import os
import tempfile
import unittest

from skillmint import frontmatter, lint, scaffold


def make_skill(name="demo-skill", description="Use when demoing skillmint", extra_body=""):
    return scaffold.build_skill(name, description) + extra_body


def rules(findings):
    return sorted({f.rule for f in findings})


class LintRuleTests(unittest.TestCase):
    def test_clean_skill_has_no_errors(self):
        findings = lint.lint_text(make_skill(), dir_name="demo-skill")
        errors = [f for f in findings if f.severity == lint.ERROR]
        self.assertEqual(errors, [])

    def test_sk001_missing_front_matter(self):
        findings = lint.lint_text("# Just a heading\n", dir_name="x")
        self.assertEqual(rules(findings), ["SK-001"])

    def test_sk001_unterminated(self):
        findings = lint.lint_text("---\nname: a-b\n", dir_name="a-b")
        self.assertEqual(rules(findings), ["SK-001"])

    def test_sk002_missing_description(self):
        text = "---\nname: a-b\n---\n## Heading\n\nbody\n"
        findings = lint.lint_text(text, dir_name="a-b")
        self.assertIn("SK-002", rules(findings))

    def test_sk003_description_too_long(self):
        long_desc = "Use when " + "x" * 1100
        findings = lint.lint_text(make_skill(description=long_desc), dir_name="demo-skill")
        self.assertIn("SK-003", rules(findings))

    def test_sk004_name_not_kebab(self):
        text = "---\nname: Bad Name\ndescription: Use when testing\n---\n## A\n\nbody\n"
        findings = lint.lint_text(text, dir_name="bad")
        self.assertIn("SK-004", rules(findings))

    def test_sk004_name_missing(self):
        text = "---\ndescription: Use when testing\n---\n## A\n\nbody\n"
        findings = lint.lint_text(text)
        self.assertIn("SK-004", rules(findings))

    def test_sk005_name_dir_mismatch_is_warning(self):
        findings = lint.lint_text(make_skill(), dir_name="other-dir")
        matched = [f for f in findings if f.rule == "SK-005"]
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0].severity, lint.WARNING)

    def test_sk006_placeholder_todo(self):
        text = make_skill(extra_body="\nThis section has TODO inside.\n")
        findings = lint.lint_text(text, dir_name="demo-skill")
        self.assertIn("SK-006", rules(findings))

    def test_sk006_placeholder_lorem(self):
        text = make_skill(extra_body="\nlorem ipsum dolor sit amet\n")
        findings = lint.lint_text(text, dir_name="demo-skill")
        self.assertIn("SK-006", rules(findings))

    def test_sk007_no_h2(self):
        text = "---\nname: a-b\ndescription: Use when testing\n---\n# only h1\n"
        findings = lint.lint_text(text, dir_name="a-b")
        self.assertIn("SK-007", rules(findings))

    def test_sk008_empty_section(self):
        text = make_skill(extra_body="\n## Empty section\n\n## Next\n\ncontent\n")
        findings = lint.lint_text(text, dir_name="demo-skill")
        self.assertIn("SK-008", rules(findings))

    def test_sk009_control_char(self):
        text = "---\nname: a-b\ndescription: Use when testing\x07\n---\n## A\n\nbody\n"
        findings = lint.lint_text(text, dir_name="a-b")
        self.assertIn("SK-009", rules(findings))

    def test_sk010_large_file(self):
        text = make_skill(extra_body="\n" + ("filler line\n" * 5000))
        self.assertGreater(len(text.encode("utf-8")), 50 * 1024)
        findings = lint.lint_text(text, dir_name="demo-skill")
        self.assertIn("SK-010", rules(findings))

    def test_sk011_missing_trigger_language_is_warning(self):
        text = make_skill(description="A skill about widgets and gizmos")
        findings = lint.lint_text(text, dir_name="demo-skill")
        matched = [f for f in findings if f.rule == "SK-011"]
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0].severity, lint.WARNING)

    def test_finding_line_numbers_present(self):
        text = "---\nname: a-b\n---\nTODO in body\n"
        findings = lint.lint_text(text, dir_name="a-b")
        sk006 = [f for f in findings if f.rule == "SK-006"][0]
        self.assertEqual(sk006.line, 4)

    def test_to_dict_shape(self):
        findings = lint.lint_text("no fm\n", path="x/SKILL.md")
        data = findings[0].to_dict("x/SKILL.md")
        self.assertEqual(
            sorted(data.keys()), ["file", "line", "message", "rule", "severity"]
        )
        self.assertEqual(data["file"], "x/SKILL.md")


class LintPathTests(unittest.TestCase):
    def test_lint_path_reads_file_and_uses_dir_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = os.path.join(tmp, "demo-skill")
            os.makedirs(skill_dir)
            path = os.path.join(skill_dir, "SKILL.md")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(make_skill())
            findings = lint.lint_path(path)
            self.assertEqual([f for f in findings if f.severity == lint.ERROR], [])

    def test_collect_markdown_recursive_sorted(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "b"))
            for rel in ("a.md", os.path.join("b", "c.md")):
                with open(os.path.join(tmp, rel), "w", encoding="utf-8") as handle:
                    handle.write("x\n")
            with open(os.path.join(tmp, "skip.txt"), "w", encoding="utf-8") as handle:
                handle.write("x\n")
            found = lint.collect_markdown([tmp])
            self.assertTrue(all(p.endswith(".md") for p in found))
            self.assertEqual(len(found), 2)
            self.assertEqual(found, sorted(found))


class ScaffoldTests(unittest.TestCase):
    def test_scaffold_lints_clean(self):
        text = scaffold.build_skill(
            "fresh-skill", "Use when the user needs a fresh scaffold", triggers=["fresh"]
        )
        findings = lint.lint_text(text, dir_name="fresh-skill")
        self.assertEqual([f for f in findings if f.severity == lint.ERROR], [])

    def test_write_skill_creates_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = scaffold.write_skill(
                os.path.join(tmp, "demo-skill"),
                "demo-skill",
                "Use when testing write_skill",
            )
            self.assertTrue(os.path.isfile(path))
            with open(path, "r", encoding="utf-8") as handle:
                meta, body, _ = frontmatter.parse(handle.read())
            self.assertEqual(meta["name"], "demo-skill")
            self.assertIn("## Workflow", body)


if __name__ == "__main__":
    unittest.main()
