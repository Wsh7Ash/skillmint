import unittest

from skillmint import frontmatter


class ParseTests(unittest.TestCase):
    def test_parse_basic_scalars(self):
        text = "---\nname: my-skill\ndescription: Use when testing\n---\n# Body\n"
        meta, body, start = frontmatter.parse(text)
        self.assertEqual(meta["name"], "my-skill")
        self.assertEqual(meta["description"], "Use when testing")
        self.assertEqual(body, "# Body\n")
        self.assertEqual(start, 5)

    def test_parse_quoted_strings(self):
        text = '---\nname: "quoted name"\ndescription: \'single: ok\'\n---\n'
        meta, _, _ = frontmatter.parse(text)
        self.assertEqual(meta["name"], "quoted name")
        self.assertEqual(meta["description"], "single: ok")

    def test_parse_inline_list(self):
        text = "---\nname: a-b\ntriggers: [one, two, \"three four\"]\n---\n"
        meta, _, _ = frontmatter.parse(text)
        self.assertEqual(meta["triggers"], ["one", "two", "three four"])

    def test_parse_block_list(self):
        text = "---\nname: a-b\ntriggers:\n  - alpha\n  - beta\n---\nbody\n"
        meta, body, _ = frontmatter.parse(text)
        self.assertEqual(meta["triggers"], ["alpha", "beta"])
        self.assertEqual(body, "body\n")

    def test_parse_comments_and_blanks(self):
        text = "---\n# a comment\n\nname: a-b\n---\n"
        meta, _, _ = frontmatter.parse(text)
        self.assertEqual(meta["name"], "a-b")

    def test_missing_opening_raises(self):
        with self.assertRaises(frontmatter.FrontMatterError) as ctx:
            frontmatter.parse("no front matter here\n")
        self.assertEqual(ctx.exception.line, 1)

    def test_unterminated_raises(self):
        with self.assertRaises(frontmatter.FrontMatterError):
            frontmatter.parse("---\nname: a-b\n# no close\n")

    def test_tab_raises(self):
        with self.assertRaises(frontmatter.FrontMatterError) as ctx:
            frontmatter.parse("---\n\tname: a-b\n---\n")
        self.assertEqual(ctx.exception.line, 2)

    def test_unsupported_line_raises(self):
        with self.assertRaises(frontmatter.FrontMatterError):
            frontmatter.parse("---\njust some text\n---\n")

    def test_orphan_list_item_raises(self):
        with self.assertRaises(frontmatter.FrontMatterError):
            frontmatter.parse("---\n- orphan\n---\n")

    def test_scalar_true_null(self):
        text = "---\nname: a-b\nflag: true\nnothing: null\n---\n"
        meta, _, _ = frontmatter.parse(text)
        self.assertIs(meta["flag"], True)
        self.assertIsNone(meta["nothing"])

    def test_comment_stripped_outside_quotes(self):
        text = "---\nname: a-b  # trailing note\n---\n"
        meta, _, _ = frontmatter.parse(text)
        self.assertEqual(meta["name"], "a-b")

    def test_hash_inside_quotes_kept(self):
        text = '---\nname: a-b\ndescription: "use when colors like #fff matter"\n---\n'
        meta, _, _ = frontmatter.parse(text)
        self.assertEqual(meta["description"], "use when colors like #fff matter")

    def test_format_round_trip(self):
        meta = {"name": "demo-skill", "description": "Use when demoing", "triggers": ["alpha", "beta"]}
        text = frontmatter.format_front_matter(meta)
        parsed, _, _ = frontmatter.parse(text)
        self.assertEqual(parsed["name"], "demo-skill")
        self.assertEqual(parsed["triggers"], ["alpha", "beta"])


if __name__ == "__main__":
    unittest.main()
