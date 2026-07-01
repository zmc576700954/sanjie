"""Tests for Markdown parsing utilities."""

from agents_dev.docs.parser.markdown_parser import parse_frontmatter


def test_parse_frontmatter_extracts_metadata():
    text = """---
title: API Deploy
author: alice
doc_type: how-to
tags: [api, deploy]
---
Run pytest.
"""
    meta, body = parse_frontmatter(text)
    assert meta["title"] == "API Deploy"
    assert meta["author"] == "alice"
    assert "Run pytest" in body


def test_parse_frontmatter_without_frontmatter():
    meta, body = parse_frontmatter("Plain content.")
    assert meta == {}
    assert body == "Plain content."
