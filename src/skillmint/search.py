"""Keyword search over a local corpus of SKILL.md files."""

import os
import re

from . import frontmatter

_WORD_RE = re.compile(r"[a-z0-9]+")


def _words(text):
    return _WORD_RE.findall(text.lower())


def _count(haystack_words, query_words):
    return sum(1 for word in haystack_words if word in query_words)


def search_corpus(corpus_dir, query, limit=10):
    """Rank SKILL.md files under ``corpus_dir`` for ``query``.

    Returns a list of dicts: {path, name, score, matched}.
    """
    query_words = set(_words(query))
    results = []
    for root, dirs, files in os.walk(corpus_dir):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for fname in sorted(files):
            if not fname.endswith(".md"):
                continue
            path = os.path.join(root, fname)
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    text = handle.read()
                meta, body, _ = frontmatter.parse(text)
            except Exception:
                continue
            name = str(meta.get("name", fname))
            description = str(meta.get("description", ""))
            name_words = _words(name)
            desc_words = _words(description)
            body_words = _words(body)
            score = 0
            matched = []
            name_hits = _count(name_words, query_words)
            if name_hits:
                score += 3 * name_hits
                matched.append("name")
            desc_hits = _count(desc_words, query_words)
            if desc_hits:
                score += 2 * desc_hits
                matched.append("description")
            body_hits = _count(body_words, query_words)
            if body_hits:
                score += body_hits
                matched.append("body")
            if score > 0:
                results.append(
                    {"path": path.replace("\\", "/"), "name": name, "score": score, "matched": matched}
                )
    results.sort(key=lambda item: (-item["score"], item["name"]))
    return results[:limit]
