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


def on_page_context(context, page, config, nav):
    """Per-page <meta name="description"> via Material's own emission path.

    Material's base.html emits page.meta.description when present, else the
    identical site_description on EVERY page - the tick-847 census measured
    443/443 pages carrying the same one-line site blurb, so search engines
    (which prefer the meta description for snippets) showed a single generic
    sentence for the whole corpus. Derive the same lede the og:description
    chain uses (first prose paragraph after the h1, meta-line skip) and
    inject it as the page description unless the FM carries one (the corpus
    carries no Description today; the key is future-proofing per tick-844).
    Mutating page.meta before render means Material's if/elif picks it up
    natively - no duplicate tag, no post-build rewrite.
    """
    meta = getattr(page, "meta", None)
    if not isinstance(meta, dict) or "Description" in meta or "description" in meta:
        return context
    content = page.content or ""
    after_h1 = content.split("</h1>", 1)[1] if "</h1>" in content else content
    lede = first_lede(after_h1)
    if lede and len(lede) > 20:
        if len(lede) > 160:
            lede = lede[:157].rsplit(" ", 1)[0].rstrip(",;: ") + "…"
        meta["description"] = lede
    return context


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
    # Accessibility repairs on the built DOM (site plumbing, corpus untouched):
    # 1) pymdownx anchor_linenums emits one EMPTY focusable link per code line
    #    (<a id="__codelineno-N-M" name=... href="#__codelineno-N-M"></a>) -
    #    132,856 across the built corpus - so keyboard users tab through tens
    #    of blank stops inside every line-numbered block and screen readers
    #    announce bare links. The bundle only consumes them as hash-selection
    #    targets (no DOM mutation), so they must stay anchor targets but leave
    #    the tab order and the AT tree: tabindex="-1" + aria-hidden="true".
    #    Guard on id= so a hypothetical authored link to a code line (href
    #    without id) is never muted - census: 0 such links today.
    # 2) Material 9.7.6's edit-this-page button is icon-only (svg) with a
    #    title but NO accessible name on all 442 pages - screen readers
    #    announce a bare "link". Copy the existing title into aria-label.
    # 3) Material 9.7.6 marks the current page's sidebar link with the
    #    md-nav__link--active class only - a purely visual signal (CSS
    #    highlight). No aria-current on any of the 442 pages, so screen
    #    readers get no programmatic "you are here" cue - the location
    #    signal exists only as color/weight. aria-current="page" is the
    #    exact ARIA token for a link pointing at the page it's on.
    nav_active_re = re.compile(r'<a\b[^>]*\bclass="[^"]*md-nav__link--active[^"]*"[^>]*>')
    # 4) Material hardcodes twitter:card to "summary" - X/Twitter's small
    #    square-thumbnail slot - while the social cards render at 1200x630
    #    landscape, so the image face gets cropped to a tiny square on
    #    share previews. summary_large_image is the matching card type for
    #    that aspect and shows the full-width image. The pattern only
    #    matches the exact literal, so an upstream value change is left
    #    alone.
    tw_card_re = re.compile(r'(<meta\s+name="twitter:card"\s+content=")summary(")')
    # 5) Material 9.7.6's og: block carries title/description/type/url but NO
    #    og:site_name on any page, so share previews label the link with the
    #    bare host (minderhq.github.io) instead of the brand. Inject the
    #    configured site_name ahead of og:type, guarded on absence so an
    #    upstream emission can never be doubled.
    og_site_re = re.compile(r'(<meta\s+property="og:type")')
    line_anchor_re = re.compile(r'<a\b[^>]*\bid="__codelineno[^>]*>')
    edit_anchor_re = re.compile(r'<a\b[^>]*\brel="edit"[^>]*>')
    bridged = untabbed = named = current = enlarged = sited = 0
    site_name = (config.get("site_name") or "").replace('"', "&quot;")
    for html in site.rglob("*.html"):
        depth = len(html.parent.relative_to(site).parts)

        def _bridge(m, depth=depth):
            nonlocal bridged
            ups = len(m.group(1)) // 3
            if ups <= depth:
                return m.group(0)
            bridged += 1
            return f'href="{"../" * depth}experiments/{m.group(2)}"'

        def _line(m):
            nonlocal untabbed
            tag = m.group(0)
            if "tabindex" in tag:
                return tag
            untabbed += 1
            return f"{tag[:-1]} tabindex=\"-1\" aria-hidden=\"true\">"

        def _edit(m):
            nonlocal named
            tag = m.group(0)
            if "aria-label" in tag:
                return tag
            t = re.search(r'title="([^"]*)"', tag)
            if not t:
                return tag
            named += 1
            return f"{tag[:-1]} aria-label=\"{t.group(1)}\">"

        def _nav(m):
            nonlocal current
            tag = m.group(0)
            if "aria-current" in tag:
                return tag
            current += 1
            return f"{tag[:-1]} aria-current=\"page\">"

        def _tw(m):
            nonlocal enlarged
            enlarged += 1
            return f"{m.group(1)}summary_large_image{m.group(2)}"

        def _og_site(m):
            nonlocal sited
            sited += 1
            return f'<meta property="og:site_name" content="{site_name}">' + m.group(0)

        text = html.read_bytes().decode("utf-8")
        new_text = href_re.sub(_bridge, text)
        new_text = line_anchor_re.sub(_line, new_text)
        new_text = edit_anchor_re.sub(_edit, new_text)
        new_text = nav_active_re.sub(_nav, new_text)
        new_text = tw_card_re.sub(_tw, new_text)
        if site_name:
            new_text = og_site_re.sub(_og_site, new_text)
        if new_text != text:
            html.write_bytes(new_text.encode("utf-8"))
    print(f"[hooks] bridged {bridged} experiments link(s) from repo depth to site depth")
    print(f"[hooks] a11y: {untabbed} codelineno anchor(s) untabbed, {named} edit button(s) named, {current} nav link(s) aria-current")
    print(f"[hooks] share: {enlarged} twitter:card meta(s) enlarged to summary_large_image")
    print(f"[hooks] share: {sited} og:site_name meta(s) injected")
