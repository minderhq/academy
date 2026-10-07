# -*- coding: utf-8 -*-
"""GitHub-accurate slugify for the mkdocs build.

The corpus's in-document anchors are written GitHub-style (the QA fleet's
anchor_check enforces them with its own GitHub-accurate slugger), but
python-markdown's default toc slugger collapses hyphen runs - so headings
like "CI/CD & Automation" produced ids (week-3-cicd-automation) that did
not match the shipped links (#week-3-cicd--automation). Plugging the
gate's own slugger into the toc extension makes one implementation the
single source of truth: ids on the deployed site are identical to GitHub
and identical to what anchor_check verifies.

Loaded from mkdocs.yml via:  toc: slugify: !!python/name:gh_slugify.slugify
"""
import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "anchor_check", Path(__file__).parent / "scripts" / "qa" / "anchor_check.py")
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)


def slugify(value, separator="-"):
    """python-markdown toc slugify signature; delegates to the gate."""
    return _MOD.gh_slug(value)
