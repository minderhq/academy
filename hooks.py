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
    natively - no duplicate tag, no post-build rewrite. The value must be
    attribute-escaped here: mkdocs' Jinja env renders with autoescape off
    (proven by the tick-867 census - 17 pages whose lede carries straight
    double quotes shipped a raw " inside content="...", breaking the
    attribute so crawlers read an empty description), while the og:description
    path escapes its own copy with the | e filter, so no double escape.
    """
    import html as _html

    meta = getattr(page, "meta", None)
    if not isinstance(meta, dict) or "Description" in meta or "description" in meta:
        return context
    content = page.content or ""
    after_h1 = content.split("</h1>", 1)[1] if "</h1>" in content else content
    lede = first_lede(after_h1)
    if lede and len(lede) > 20:
        if len(lede) > 160:
            lede = lede[:157].rsplit(" ", 1)[0].rstrip(",;: ") + "…"
        meta["description"] = _html.escape(lede, quote=True)
    return context


def on_post_build(config, **kwargs):
    import html as _html
    import posixpath
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
    #    og:site_name on any page (nor does the social plugin's own meta set -
    #    its default layout tags are og:type/title/description/image±dims/url
    #    plus twitter:*), so share previews label the link with the bare host
    #    (minderhq.github.io) instead of the brand. Inject the configured
    #    site_name ahead of og:type. The social plugin runs before these hooks
    #    (mkdocs loads hooks after configured plugins) and appends its block
    #    before </head>, so CI builds carry TWO og:type per page while local
    #    builds (social off - no cairosvg runtime on Windows) carry one; an
    #    unbounded sub injected a duplicate og:site_name into the social block
    #    too (tick-887 live census: og:site_name 2x on all 442 live pages vs
    #    1x locally). count=1 anchors the injection to the first og:type - the
    #    template block's - so exactly one og:site_name ships per page on
    #    either side.
    og_site_re = re.compile(r'(<meta\s+property="og:type")')
    # 6) 152 pages carry a generic front-matter title (Overview x46,
    #    Prerequisites x33, Practice x33, Quiz x33, Checkpoint x7) while the
    #    page's rendered h1 is informative and different - browser tabs,
    #    history and share previews (og:title) all present that single
    #    generic word, so 46 module indexes are indistinguishable ("Overview
    #    - Minder Academy" x46). This is the title sibling of the tick-847
    #    meta-description disease (one generic value, many pages). Same
    #    corpus-untouched treatment: when the <title> prefix is one of the
    #    generic set AND the rendered h1 differs, rewrite the <title> tag
    #    and the og:title meta to the h1 (keeping Material's
    #    "{title} - {site_name}" tab format). Sidebar nav labels, the search
    #    index and the social cards keep the front-matter title - only the
    #    tab/share face changes, so a deliberate short nav label survives.
    generic_titles = {"Overview", "Prerequisites", "Practice", "Quiz", "Checkpoint"}
    # 8) python-markdown's tables extension emits every header cell as a bare
    #    <th> with no scope attribute - the tick-886 census measured 2,027 th
    #    across 581 tables on 213 pages, 0 with scope - so screen readers
    #    lose the column-header mapping (WCAG 1.3.1) and every data cell is
    #    announced without its column context. The extension puts EVERY th in
    #    <thead> (first-row-header model), so each one is a column header and
    #    scope="col" is the exact token; row-header th (tbody) does not occur
    #    in this corpus. Guarded on absence of scope= so an upstream emission
    #    can never be doubled.
    th_re = re.compile(r"<th\b(?![^>]*\bscope=)([^>]*)>")
    # 9) Material's skip link ("Skip to content", the first focusable element)
    #    targets the page h1 by id, but the h1 carries no tabindex - the
    #    tick-893 census measured 442/442 pages. Activating the link scrolls
    #    the viewport without moving keyboard focus: browsers that do not
    #    transfer focus to non-interactive targets (Safari) leave focus on
    #    the skip link itself, and screen readers that follow focus rather
    #    than scroll stay at the top - the skip becomes a visual-only jump
    #    (WCAG 2.4.1 bypass blocks). tabindex="-1" on the target makes it
    #    programmatically focusable, the canonical skip-link pattern
    #    (WAI tutorials); no visual change, the attribute is not focusable by
    #    Tab. Guarded on absence of tabindex= and anchored to the exact id
    #    the skip link references, so an upstream change cannot be doubled.
    skip_re = re.compile(r'<a\b(?=[^>]*\bclass="[^"]*md-skip)[^>]*\bhref="#([^"]*)"')
    # 10) Material 9.7.7 marks the active header tab with the
    #     md-tabs__item--active class on the <li> only - a purely visual CSS
    #     signal, exactly the disease the sidebar fix (3) cured there: no
    #     aria-current on any tab link, so screen readers get no programmatic
    #     "current section" cue on any of the 442 pages (census: 4,420 tab
    #     links, 0 aria-current, exactly one --active li per page, 0 broken
    #     hrefs). Token is aria-current="true" - "current item within a set":
    #     the active tab points at the section root, not always this page
    #     (the sidebar's "page" token stays exact for its face; here the link
    #     is current-section, which "true" states in both cases). Guarded on
    #     absence of aria-current= so an upstream change cannot be doubled.
    tabs_active_re = re.compile(
        r'(<li class="md-tabs__item md-tabs__item--active">\s*<a\b)(?![^>]*\baria-current=)([^>]*>)')
    # 7) Material 9.7.6 labels the footer prev/next links with the neighboring
    #    page's raw front-matter title (page.previous_page.title), while the
    #    sidebar shows the explicit nav label from mkdocs.yml. For the generic
    #    front-matter set (tick-864's five words) the two faces disagree on
    #    the SAME page: the tick-870 census measured 92 footer anchors whose
    #    visible md-ellipsis and aria-label read "Overview" while the sidebar
    #    - on that very page - names the identical destination "7500 ·
    #    Security" (46 distinct target pages). The footer name is
    #    content-blind: "Next: Overview" says nothing about which module is
    #    next. Rewrite both faces from the sidebar nav label when the raw
    #    label is one of the generic words - the label map comes from the
    #    built home page's own nav tree (the one place hrefs are
    #    root-relative and resolve unambiguously; deep pages carry ../
    #    relative hrefs that only resolve from their own location). Non-
    #    generic label/title divergences are deliberate short nav names and
    #    stay authoring decisions.
    nav_label = {}
    index_html = site / "index.html"
    if index_html.is_file():
        for m in re.finditer(r'<a\b[^>]*\bclass="md-nav__link[^"]*"[^>]*>(.*?)</a>',
                             index_html.read_bytes().decode("utf-8"), re.S):
            h = re.search(r'href="([^"]*)"', m.group(0))
            if not h or h.group(1).startswith(("http", "mailto:", "#")):
                continue
            label = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", m.group(1)))).strip()
            if label:
                nav_label.setdefault(posixpath.normpath(h.group(1)), label)
    footer_re = re.compile(r'<a\b[^>]*\bclass="md-footer__link md-footer__link--(?:prev|next)"[^>]*>.*?</a>', re.S)
    title_re = re.compile(r"<title>([^<]*)</title>")
    og_title_re = re.compile(r'(<meta\s+property="og:title"\s+content=")([^"]*)(")')
    h1_re = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
    line_anchor_re = re.compile(r'<a\b[^>]*\bid="__codelineno[^>]*>')
    edit_anchor_re = re.compile(r'<a\b[^>]*\brel="edit"[^>]*>')
    bridged = untabbed = named = current = enlarged = sited = retitled = footered = scoped = skipped = tabbed = 0
    site_name = (config.get("site_name") or "").replace('"', "&quot;")
    for html in site.rglob("*.html"):
        depth = len(html.parent.relative_to(site).parts)
        rel_posix = html.relative_to(site).as_posix()

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

        def _th(m):
            nonlocal scoped
            scoped += 1
            return f'<th{m.group(1)} scope="col">'

        def _footer(m):
            nonlocal footered
            tag = m.group(0)
            ma = re.search(r'aria-label="((?:Previous|Next): )([^"]*)"', tag)
            mh = re.search(r'href="([^"]*)"', tag)
            if not ma or not mh or ma.group(2) not in generic_titles:
                return tag
            href = mh.group(1)
            if href.startswith(("http", "mailto:", "#")):
                return tag
            label = nav_label.get(posixpath.normpath(posixpath.join(posixpath.dirname(rel_posix), href)))
            if not label or label == ma.group(2):
                return tag
            footered += 1
            esc = label.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
            new_tag = tag.replace(ma.group(0), f'aria-label="{ma.group(1)}{esc}"', 1)
            me = re.search(r'(<div class="md-ellipsis">\s*)([^<]*?)(\s*</div>)', new_tag)
            if me and _html.unescape(me.group(2)).strip() == ma.group(2):
                esc_t = label.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                new_tag = new_tag.replace(me.group(0), f"{me.group(1)}{esc_t}{me.group(3)}", 1)
            return new_tag

        text = html.read_bytes().decode("utf-8")
        new_text = href_re.sub(_bridge, text)
        new_text = line_anchor_re.sub(_line, new_text)
        new_text = edit_anchor_re.sub(_edit, new_text)
        new_text = nav_active_re.sub(_nav, new_text)
        new_text = tw_card_re.sub(_tw, new_text)
        if site_name:
            new_text = og_site_re.sub(_og_site, new_text, count=1)
        # generic-title rewrite (6): h1 -> tab title + og:title
        mh1 = h1_re.search(new_text)
        mt = title_re.search(new_text)
        if mh1 and mt:
            h1 = _html.unescape(re.sub(r"<[^>]+>", " ", mh1.group(1)))
            h1 = re.sub(r"\s+", " ", h1).replace("¶", "").strip()
            fm_title = re.sub(r"\s*-\s*" + re.escape(site_name) + r"$", "", mt.group(1)).strip()
            if h1 and fm_title in generic_titles and h1 != fm_title:
                esc = h1.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
                new_text = new_text.replace(mt.group(0), f"<title>{esc} - {site_name}</title>", 1)
                mog = og_title_re.search(new_text)
                if mog and _html.unescape(mog.group(2)) == fm_title:
                    new_text = new_text.replace(mog.group(0), f"{mog.group(1)}{esc}{mog.group(3)}", 1)
                retitled += 1
        new_text = th_re.sub(_th, new_text)
        new_text = footer_re.sub(_footer, new_text)
        # skip-link focus target (9): tabindex="-1" on the exact h1 the skip
        # link references, so activating the skip moves focus, not just scroll
        mskip = skip_re.search(new_text)
        if mskip:
            frag = mskip.group(1)
            def _h1(m):
                nonlocal skipped
                skipped += 1
                return m.group(0)[:-1] + ' tabindex="-1">'
            new_text = re.sub(
                r'<h1\b(?![^>]*\btabindex=)(?=[^>]*\bid="' + re.escape(frag) + r'")([^>]*)>',
                _h1, new_text, count=1)
        # active header tab (10): aria-current="true" on the link inside the
        # active md-tabs__item li, the programmatic counterpart of the CSS
        # highlight
        def _tabs(m):
            nonlocal tabbed
            tabbed += 1
            return m.group(1) + m.group(2)[:-1] + ' aria-current="true">'
        new_text = tabs_active_re.sub(_tabs, new_text)
        if new_text != text:
            html.write_bytes(new_text.encode("utf-8"))
    print(f"[hooks] bridged {bridged} experiments link(s) from repo depth to site depth")
    print(f"[hooks] a11y: {untabbed} codelineno anchor(s) untabbed, {named} edit button(s) named, {current} nav link(s) aria-current, {skipped} skip target(s) made focusable")
    print(f"[hooks] share: {enlarged} twitter:card meta(s) enlarged to summary_large_image")
    print(f"[hooks] share: {sited} og:site_name meta(s) injected")
    print(f"[hooks] titles: {retitled} generic tab/og title(s) set from the page h1")
    print(f"[hooks] footer: {footered} generic prev/next label(s) set from the sidebar nav label")
    print(f"[hooks] tables: {scoped} table header cell(s) scoped to col")
    print(f"[hooks] tabs: {tabbed} active header tab(s) marked aria-current")
