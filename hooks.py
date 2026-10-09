# -*- coding: utf-8 -*-
"""mkdocs hook: publish repo-root companion material alongside the built site.

Corpus docs link to repo-root experiments/, configs/, and README.md via
relative paths (e.g. ../../experiments/EXP_1101_GPON.md). mkdocs builds only
docs/, so on the deployed site those links would 404. This hook copies the
companion material into site/ after the build so every link resolves; GitHub
Pages serves the raw .md/.yml/.js files as plain text.
"""

import re

_P_RE = re.compile(r"<p(?:\s[^>]*)?>")
_P_END = "</p>"
_META_LEDE = re.compile(
    r"^(?:Last Updated|Updated|Last updated|Difficulty|Time|Estimated Time|"
    r"Reading Time|Prerequisites|Document ID|Module|Duration)\s*:",
    re.I,
)


def first_lede(value):
    """Jinja filter: first real prose paragraph from rendered page content.

    overrides/main.html derives og:description from the rendered content after
    the first h1. Stripping all tags there yields the in-page Table of
    Contents text on 158/443 pages (the corpus opens most pages with a
    Contents heading plus a link list), so share previews on Discord/Slack/X
    showed menu text instead of prose. Instead return the text inside the
    first <p> after the h1: TOC entries render as <li>, never <p>, so the
    first paragraph is the page's actual lede. Leading key-value meta lines
    ("Last Updated:", "Difficulty:", "Time:", "Prerequisites:", ...) are
    skipped in favor of the first prose paragraph - some pages (assessment
    banks, tutorials) open with a chain of three to five of them - and
    pages without any <p> fall back to plain tag-stripping (the previous
    behavior).
    """
    import html as _html

    text = value or ""
    for _ in range(8):
        m = _P_RE.search(text)
        if not m:
            break
        inner = text[m.end(): text.find(_P_END, m.end())]
        stripped = _html.unescape(re.sub(r"<[^>]+>", " ", inner))
        stripped = re.sub(r"\s+", " ", stripped).strip()
        if stripped and not _META_LEDE.match(stripped):
            return stripped
        text = text[text.find(_P_END, m.end()) + len(_P_END):]
    stripped = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", stripped).strip()


def on_env(env, config, files):
    env.filters["first_lede"] = first_lede
    return env


def on_post_build(config, **kwargs):
    import shutil
    from pathlib import Path

    root = Path(__file__).parent
    site = Path(config["site_dir"])
    copied = []
    for name in ("experiments", "configs"):
        src = root / name
        if src.is_dir():
            shutil.copytree(src, site / name, dirs_exist_ok=True)
            copied.append(name)
    readme = root / "README.md"
    if readme.is_file():
        shutil.copy2(readme, site / "README.md")
        copied.append("README.md")
    # robots.txt for the crawler entry point: allow all + point at the
    # sitemap.xml mkdocs itself emits into site/. Generated here rather than
    # shipped as docs/robots.txt - mkdocs copies non-md docs/ files verbatim,
    # and a file under docs/ inflates the corpus file counts that the README
    # footer and SITEMAP statistics pin (the fleet's claims gates read them:
    # tick-846 added docs/robots.txt and the claims gates flagged 496 -> 497).
    # A crawler policy file is site plumbing, not documentation - it belongs
    # in the same completion layer as the companion copy and the bridge below.
    site_url = (config.get("site_url") or "").rstrip("/")
    if site_url:
        robots = f"User-agent: *\nAllow: /\n\nSitemap: {site_url}/sitemap.xml\n"
        (site / "robots.txt").write_bytes(robots.encode("utf-8"))
    print(f"[hooks] copied companion material into site/: {', '.join(copied)}")

    # Bridging repo link depth to site link depth: repo paths carry the extra
    # docs/ prefix, so README-authored experiments links resolve one level
    # higher inside the repo than on the deployed site (README pages render at
    # their own directory depth, without the docs/ segment). mkdocs leaves
    # those links untouched (they resolve outside docs/), and after the copy
    # above they would still escape the site root by one level and 404. Drop
    # the escaping ../ levels so every experiments href lands on
    # site/experiments/; links that already resolve inside the site (e.g. the
    # lesson-file pages, whose file-as-dir render depth compensates the docs/
    # prefix) are left alone.
    href_re = re.compile(r'href="((?:\.\./)+)experiments/(EXP_[A-Z0-9_]+\.md)"')
    bridged = 0
    for html in site.rglob("*.html"):
        depth = len(html.parent.relative_to(site).parts)

        def _bridge(m, depth=depth):
            nonlocal bridged
            ups = len(m.group(1)) // 3
            if ups <= depth:
                return m.group(0)
            bridged += 1
            return f'href="{"../" * depth}experiments/{m.group(2)}"'

        text = html.read_bytes().decode("utf-8")
        new_text = href_re.sub(_bridge, text)
        if new_text != text:
            html.write_bytes(new_text.encode("utf-8"))
    print(f"[hooks] bridged {bridged} experiments link(s) from repo depth to site depth")
