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
    # 11) Material 9.7.7 emits the two visible header icon toggles - search
    #     ("for=__search") and drawer/menu ("for=__drawer") - as bare
    #     <label class="md-header__button md-icon"> wrapping an icon svg: no
    #     title, no aria-label, no tabindex (census: 443+443 BARE page-wide).
    #     Material's own convention for the SAME element type in the SAME
    #     header names the palette labels with title="Switch to ...", and the
    #     en locale ships the "Search" string - the bare pair is an upstream
    #     naming gap, the visible pointer affordance carrying no name. Fix
    #     mirrors the palette precedent: aria-label (explicit name) plus title
    #     (tooltip + AT fallback) - "Search" from the en locale, "Menu" the
    #     standard drawer token. Guarded on absence of aria-label= so an
    #     upstream change cannot be doubled.
    hdr_search_label_re = re.compile(
        r'<label\b(?![^>]*\baria-label=)([^>]*\bclass="md-header__button md-icon"[^>]*\bfor="__search"[^>]*)>')
    hdr_drawer_label_re = re.compile(
        r'<label\b(?![^>]*\baria-label=)([^>]*\bclass="md-header__button md-icon"[^>]*\bfor="__drawer"[^>]*)>')
    # 13) The header drawer toggle is the one visible header control with no
    #     keyboard path at all (WCAG 2.1.1, tick-924 census): Material emits
    #     it as a bare <label for="__drawer"> driving the hidden __drawer
    #     checkbox through native label semantics, and the bundle contains
    #     ZERO references to __drawer - no JS wiring, unlike the search label
    #     (its click focuses the input) and the palette form (upstream ships
    #     it its own Enter handler that clicks the radios). Native behavior
    #     makes labels keyboard-inert even when focusable: Enter and Space
    #     fire no activation on a <label>. On mobile viewports the label is
    #     the ONLY way to open the navigation drawer (the __drawer checkbox
    #     itself is display:none), so without this fix a keyboard user could
    #     not open site navigation at all - pointer-only operation. Two-part
    #     fix, both guarded so an upstream fix cannot be doubled: (a)
    #     tabindex="0" puts the label in the tab order on exactly the
    #     viewports where it is visible (desktop hides it with display:none,
    #     and hidden elements drop out of the tab order, so desktop tab
    #     sequence is unchanged); (b) a document-level keydown delegate
    #     translates Enter/Space on the label into click() - the same idiom
    #     upstream's palette handler uses (Enter -> click + focus) - and
    #     label.click() activates the labeled checkbox through the native
    #     path, so the #__drawer:checked CSS cascade opens the drawer exactly
    #     as a pointer tap does. The script is injected before </body>,
    #     outside the data-md-component="container" element that instant
    #     navigation re-scripts on every route change, so the listener
    #     attaches once per document and survives instant navigation as a
    #     delegate. No window-level re-entry guard: window properties
    #     outlive the document across same-tab navigations, so a flag set
    #     by one page load would silently skip attaching the listener on
    #     the next reload (the listener dies with the document, the flag
    #     does not). The hooks-side "not already injected" check is the
    #     only dedup needed - per document, there is exactly one run.
    #     Tick-925 adds the Escape arm: with the drawer OPEN, Escape did
    #     nothing live (verified: checkbox stayed checked) because the
    #     bundle's only case"Escape" handler is the search overlay's - the
    #     open trigger had no keyboard counterpart for closing. Not a WCAG
    #     2.1.2 trap (the drawer is not modal; focus roams freely and
    #     Space/Enter on the toggle still toggles), so this is UX polish on
    #     the user's own bar, not a hard violation: Escape while the drawer
    #     is checked unchecks it directly (the bundle never observes the
    #     checkbox, so a plain write is safe and the :checked CSS cascade
    #     animates the close) and returns focus to the toggle label - the
    #     trigger-return focus idiom. The arm no-ops when the drawer is
    #     closed, so the search overlay's own Escape behavior is untouched.
    hdr_drawer_tab_re = re.compile(
        r'<label\b(?![^>]*\btabindex=)([^>]*\bclass="md-header__button md-icon"[^>]*\bfor="__drawer"[^>]*)>')
    drawer_keys_html = (
        '<script>document.addEventListener("keydown",function(e){'
        'if("Escape"===e.key){'
        'var c=document.getElementById("__drawer");'
        'if(c&&c.checked){c.checked=!1;'
        'var l=document.querySelector(\'label.md-header__button[for="__drawer"]\');'
        'l&&l.focus();e.preventDefault()}return}'
        'if("Enter"!==e.key&&" "!==e.key)return;'
        'var t=e.target;'
        't&&t.matches&&t.matches(\'label.md-header__button[for="__drawer"]\')'
        '&&(e.preventDefault(),t.click())});</script>')
    # 14) reduced-motion JS-scroll shim, the one live gap measured by the
    #     tick-926 prefers-reduced-motion coverage census. The CSS face of
    #     this axis is already TOTAL upstream: the shipped 9.7.7 stylesheet
    #     carries exactly one @media (prefers-reduced-motion) block and it
    #     is the universal nuker - *,:after,:before{transition:none
    #     !important} - which defeats all 118 transition declarations in
    #     the file at once; the six @keyframes animations (consent, overlay,
    #     facts, fact, pulse, hoverfix) are outside it, but every owner is
    #     a config-dead surface on this site (consent overlay, repo facts,
    #     version selector, count annotations all zero-hit in the corpus),
    #     so no animation actually plays anywhere to reduce. The gap is the
    #     JS face: the bundle contains zero occurrences of the media query,
    #     and toc.follow (mkdocs.yml, live in every page's embedded config)
    #     scrolls the sidebar to the active TOC entry with an explicit
    #     behavior:"smooth" 250ms after scrolling starts - and per the
    #     CSSOM-View spec an explicit behavior in the options object
    #     OVERRIDES the container's computed scroll-behavior, so no CSS
    #     rule can ever downgrade it (the other two bundle smooth scrolls
    #     belong to the tabbed-set indicator, a zero-block dead surface
    #     here). For a user with reduce set, the browser silences every
    #     color/opacity/transform transition on the page and then the
    #     sidebar keeps performing its own smooth scroll on every scroll
    #     tick - the one motion the preference never reaches. Fix: a
    #     document-level shim that patches Element.prototype.scrollTo/
    #     scrollBy ONLY while the media query matches: calls carrying a
    #     behavior get a copied options object with behavior:"auto"
    #     (instant), calls without one forward byte-identically, and
    #     nothing else on the page is touched - window.scrollTo calls in
    #     the bundle carry no behavior and need nothing. The patch installs
    #     and uninstalls on matchMedia change events so the preference can
    #     flip at runtime, and stays inert in a normal-motion browser
    #     (prototypes untouched). Same guarded-injection pattern as the
    #     drawer delegate: string-absence per document, no listener state.
    motion_scroll_html = (
        '<script>(function(){'
        'var q=window.matchMedia?matchMedia("(prefers-reduced-motion: reduce)"):null;'
        'if(!q)return;'
        'function on(r){'
        'if(r){'
        'if(!Element.prototype.__rmScrollTo){'
        'Element.prototype.__rmScrollTo=Element.prototype.scrollTo;'
        'Element.prototype.scrollTo=function(o){'
        'return o&&"behavior"in o?'
        'Element.prototype.__rmScrollTo.call(this,Object.assign({},o,{behavior:"auto"})):'
        'Element.prototype.__rmScrollTo.apply(this,arguments)};'
        'Element.prototype.__rmScrollBy=Element.prototype.scrollBy;'
        'Element.prototype.scrollBy=function(o){'
        'return o&&"behavior"in o?'
        'Element.prototype.__rmScrollBy.call(this,Object.assign({},o,{behavior:"auto"})):'
        'Element.prototype.__rmScrollBy.apply(this,arguments)};'
        '}'
        '}else if(Element.prototype.__rmScrollTo){'
        'Element.prototype.scrollTo=Element.prototype.__rmScrollTo;'
        'delete Element.prototype.__rmScrollTo;'
        'Element.prototype.scrollBy=Element.prototype.__rmScrollBy;'
        'delete Element.prototype.__rmScrollBy;'
        '}'
        '}'
        'on(q.matches);'
        'if(q.addEventListener)q.addEventListener("change",function(){on(q.matches)});'
        '})();</script>')
    # 15) search-overlay focus management, the interaction-parity gap the
    #     tick-928 overlay-focus census measured live. Opening the search is
    #     focus-correct on every path - the bundle moves focus into the
    #     query input on open whether the search was opened by the mobile
    #     magnifier, the desktop "s" shortcut, or a Tab onto the
    #     focus-to-open mobile input (focusing it checks __search and the
    #     overlay opens) - but every close path strands the keyboard user:
    #     Escape closes and blurs (live-verified: focus drops to body on
    #     both mobile and desktop), and on the mobile overlay a Tab is the
    #     bundle's own dismiss gesture (close + focus to the results
    #     scrollwrap), leaving focus on an element the close animation
    #     turns invisible (live: focus-visible class on an opacity-0
    #     scrollwrap). The drawer already got its trigger-return fix in
    #     tick-925; the search never restores anywhere. Fix: a document-
    #     level pair of capture listeners - focusin records the last real
    #     focus target outside .md-search (the anchor), keydown watches
    #     Escape/Tab while __search is checked, and 120ms later - the
    #     bundle's close and blur having settled - the anchor is refocused
    #     ONLY if the search did close and focus is still stranded (body,
    #     or inside the search element). Keydown detection instead of a
    #     change listener because the bundle may uncheck the checkbox
    #     programmatically, which fires no change event. The anchor can
    #     never be the input itself (inside-search targets are skipped),
    #     so a restore can never re-open the search; a stale anchor after
    #     an instant-navigation swap fails the isConnected check and is
    #     skipped; a close where focus already moved somewhere real
    #     (result-link navigation, the tick-925 drawer restore) is a
    #     no-op. Same guarded-injection pattern as blocks 13 and 14.
    search_focus_html = (
        '<script>(function(){'
        'var d=document,anchor=null;'
        'd.addEventListener("focusin",function(e){'
        'var t=e.target;'
        'if(!t||!t.classList||t===d.body||(t.closest&&t.closest(".md-search")))return;'
        'anchor=t},!0);'
        'd.addEventListener("keydown",function(e){'
        'if("Escape"!==e.key&&"Tab"!==e.key)return;'
        'var c=document.getElementById("__search");'
        'if(!c||!c.checked)return;'
        'var a0=anchor;'
        'setTimeout(function(){'
        'if(c.checked)return;'
        'var a=d.activeElement;'
        'if(!a0||a0===d.body||!a0.isConnected)return;'
        'if(!a||a===d.body||(a.closest&&a.closest(".md-search")))'
        '{try{a0.focus({preventScroll:!0})}catch(_){a0.focus()}}'
        '},120)},!0);'
        '})();</script>')
    # 16) search-highlight "undefined" fix, the upstream bug the user
    #     reported live ("gsq-rco diye aratınca ... gsq yerine undefined
    #     yazıyor"), reproduced locally and root-caused to the bundle's
    #     own highlighter: xi() builds the match regex as
    #     (^|{separator}|)(query) and its replace callback reads only
    #     (match, p1, p2) - but the shipped separator from
    #     search_index.json carries a capture group of its own
    #     ([?]+(\s|$)), which shifts every later group right, so the
    #     term actually lands in p3 and p2 is undefined in the common
    #     case; the template then stringifies it and every mark on every
    #     ?h= page reads the literal text "undefined" (node repro:
    #     "GSQ-RCO" -> "<mark>undefined</mark>-RCO", matches the live
    #     DOM exactly; match POSITIONS are all correct - only the text
    #     inside the mark is lost). The original term cannot be repaired
    #     afterwards because the replacement has already consumed it,
    #     so the fix must run before xi() compiles its regex: a guarded
    #     RegExp wrapper - armed only when the URL has ?h= (zero risk on
    #     every other page) - intercepts the one shape xi() produces
    #     (string pattern starting "(^|", containing "|)(", flags
    #     exactly "img"; the bundle's only two "img" RegExp sites are
    #     xi's own, grep-verified) and rewrites the capture groups
    #     INSIDE the leading (^|...|) group to non-capturing, which
    #     restores p2 to the term. The decap walk is escape- and
    #     character-class-aware, leaves lookaheads ((?= (?! (?:)
    #     untouched, never touches the query group, and on any failure
    #     the wrapper compiles the original pattern unchanged, so a
    #     pathological input degrades to the shipped bug instead of a
    #     broken page. Instant navigation re-runs Ai() per swap with the
    #     wrapper already installed; the wrapper is a plain function
    #     with RegExp.prototype re-linked, so instanceof and species
    #     semantics are preserved. Same guarded-injection pattern as
    #     blocks 13-15.
    highlight_fix_html = (
        '<script>(function(){'
        'try{'
        'if(!new URLSearchParams(location.search).has("h"))return;'
        'var NR=RegExp;'
        'function decap(p){'
        'var depth=0,i=0,sIn=-1,sOut=-1,c;'
        'for(i=0;i<p.length;i++){'
        'c=p[i];'
        'if(c==="\\\\"){i++;continue;}'
        'if(c==="["){i++;while(i<p.length&&p[i]!=="]"){if(p[i]==="\\\\")i++;i++;}continue;}'
        'if(c==="("){depth++;if(depth===2&&sIn<0)sIn=i;}'
        'else if(c===")"){depth--;if(depth===0){sOut=i;break;}}'
        '}'
        'if(sIn<0||sOut<0)return p;'
        'var inner=p.slice(sIn+1,sOut),out="",j=0,ch,k;'
        'while(j<inner.length){'
        'ch=inner[j];'
        'if(ch==="\\\\"){out+=inner.substr(j,2);j+=2;continue;}'
        'if(ch==="["){k=j+1;while(k<inner.length&&inner[k]!=="]"){if(inner[k]==="\\\\")k++;k++;}out+=inner.slice(j,k+1);j=k+1;continue;}'
        'if(ch==="("){'
        'if(inner[j+1]==="?"){out+=inner.substr(j,3);j+=3;continue;}'
        'out+="(?:";j++;continue;'
        '}'
        'out+=ch;j++;'
        '}'
        'return p.slice(0,sIn)+"("+out+")"+p.slice(sOut+1);'
        '}'
        'window.RegExp=function(p,f){'
        'var o=p;'
        'try{'
        'if(typeof p==="string"&&f==="img"&&p.indexOf("(^|")===0&&p.indexOf("|)(")>0){'
        'var cut=p.lastIndexOf("(");'
        'p=decap(p.slice(0,cut))+p.slice(cut);'
        '}'
        '}catch(e){p=o}'
        'try{return new NR(p,f)}catch(e){return new NR(o,f)}'
        '};'
        'window.RegExp.prototype=NR.prototype;'
        '}catch(e){}'
        '})();</script>')
    # 18) alert-live region (tick-931): the bundle renders async status
    #     messages ("Copied to clipboard" and friends) as a transient
    #     role="dialog" toast that never receives focus and carries no
    #     aria-live/role=status - visually visible for ~2s, programmatically
    #     invisible to assistive tech (WCAG 4.1.3). Upstream exports the
    #     message stream itself as window.alert$, so subscribe to it and
    #     mirror every message into a visually-hidden polite live region.
    alert_live_html = (
        '<script>(function(){'
        'try{'
        'if(window.__mdAlertLive)return;'
        'window.__mdAlertLive=1;'
        'var live;'
        'function ensure(){'
        'if(live&&live.isConnected)return live;'
        'live=document.createElement("div");'
        'live.setAttribute("role","status");'
        'live.setAttribute("aria-live","polite");'
        'live.style.cssText="position:absolute;width:1px;height:1px;margin:-1px;padding:0;border:0;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap";'
        '(document.body||document.documentElement).appendChild(live);'
        'return live;'
        '}'
        'var tries=0;'
        '(function arm(){'
        'if(window.alert$&&typeof window.alert$.subscribe==="function"){'
        'ensure();'
        'window.alert$.subscribe(function(msg){'
        'try{'
        'var r=ensure();'
        'r.textContent="";'
        'setTimeout(function(){try{r.textContent=String(msg);}catch(e){}},50);'
        '}catch(e){}'
        '});'
        '} else if(++tries<50){setTimeout(arm,100);}'
        '})();'
        '}catch(e){}'
        '})();</script>')
    # 12) label-hygiene face, two upstream gaps measured by the tick-904
    #     label[for]->input[id] wiring census. (a) With navigation.indexes
    #     active, every nested sidebar section's expand/collapse control is
    #     a bare <label class="md-nav__link" for="__nav_X" id="__nav_X_label"
    #     tabindex="0"> containing ONLY the icon span - no text, no
    #     aria-label (19,890 site-wide). The label is focusable and unnamed
    #     (WCAG 4.1.2), and each panel's aria-labelledby points at its id,
    #     so the nested nav panel computes an empty accessible name too.
    #     Fix: copy the section title from the sibling <a>'s md-ellipsis
    #     text into aria-label on the bare label - the panel's
    #     aria-labelledby then resolves to a real name through the same id.
    #     (b) On the 46 section-root pages whose own nav item takes the
    #     indexes branch, the TOC panel title carries for="__toc" while the
    #     __toc checkbox input is never emitted - a dead for= (WCAG 1.3.1
    #     wiring; the click was already a no-op). Fix: drop the for= on
    #     title labels only on pages with no __toc input - zero behavior
    #     change, wiring made honest. Both guarded so an upstream fix can
    #     never be doubled.
    nav_idx_container_re = re.compile(
        r'(<div class="md-nav__link md-nav__container">\s*<a\b[^>]*>(.*?)</a>\s*<label\b)'
        r'(?![^>]*\baria-label=)([^>]*\bid="__nav_\d+(?:_\d+)*_label"[^>]*)>'
        r'(\s*<span class="md-nav__icon md-icon"></span>\s*</label>)', re.S)
    toc_title_label = '<label class="md-nav__title" for="__toc">'
    # (12c) companion: upstream also writes aria-labelledby="{{path}}_label"
    # on every nested panel unconditionally, but skips emitting the toggle
    # label when the index container has a single child (children|length > 1
    # guard) - a broken idref on all 443 pages for that one section
    # (__nav_10_3_6). The minted id below re-points the panel at its own
    # md-nav__title text.
    lly_re = re.compile(r'aria-labelledby="(__nav_\d+(?:_\d+)*_label)"')
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
    searchlab = drawerlab = drawertab = drawerkey = motionin = searchfocus = hlf = 0
    labelname = 0
    alertlive = 0
    navlab = tocdead = 0
    navtitle = 0
    svgdec = 0
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
        # header icon toggle labels (11): name the bare search/drawer labels
        def _slabel(m):
            nonlocal searchlab
            searchlab += 1
            return m.group(0)[:-1] + ' aria-label="Search" title="Search">'
        def _dlabel(m):
            nonlocal drawerlab
            drawerlab += 1
            return m.group(0)[:-1] + ' aria-label="Menu" title="Menu">'
        new_text = hdr_search_label_re.sub(_slabel, new_text)
        new_text = hdr_drawer_label_re.sub(_dlabel, new_text)
        # drawer keyboard path (13): mint tabindex on the toggle label and,
        # when any was made focusable, inject the Enter/Space delegate that
        # clicks it through the native label->checkbox path, plus the
        # Escape arm that closes an open drawer and refocuses the toggle
        def _dtab(m):
            nonlocal drawertab
            drawertab += 1
            return m.group(0)[:-1] + ' tabindex="0">'
        new_text = hdr_drawer_tab_re.sub(_dtab, new_text)
        if drawertab and "</body>" in new_text and drawer_keys_html not in new_text:
            new_text = new_text.replace("</body>", drawer_keys_html + "</body>", 1)
            drawerkey += 1
        # reduced-motion scroll shim (14): patch scrollTo/scrollBy while the
        # user prefers reduced motion, so the bundle's toc.follow smooth
        # scroll cannot override it
        if "</body>" in new_text and motion_scroll_html not in new_text:
            new_text = new_text.replace("</body>", motion_scroll_html + "</body>", 1)
            motionin += 1
        # search focus-return (15): refocus the last real anchor after the
        # search overlay closes, so Escape/Tab dismissals do not strand
        # keyboard focus on body or an invisible element
        if "</body>" in new_text and search_focus_html not in new_text:
            new_text = new_text.replace("</body>", search_focus_html + "</body>", 1)
            searchfocus += 1
        # search-highlight fix (16): intercept the bundle highlighter's
        # regex construction on ?h= pages so the term lands in p2 and
        # marks carry the matched text instead of the string "undefined"
        if "</body>" in new_text and highlight_fix_html not in new_text:
            new_text = new_text.replace("</body>", highlight_fix_html + "</body>", 1)
            hlf += 1
        # label-in-name parity (17): upstream renders the footer prev/next
        # links as visible "Previous"/"Next" + page title but names them
        # aria-label="Previous: {title}" - the inserted colon breaks WCAG
        # 2.5.3 containment (ACT afw4f7: the accessible name must contain
        # the visible label text; punctuation is not ignored) - drop the
        # colon so the name reads exactly like the visible text. The
        # literal prefixes are corpus-unique to the footer links (census:
        # 441+441 hits, zero elsewhere).
        for _pre, _rep in (('aria-label="Previous: ', 'aria-label="Previous '),
                           ('aria-label="Next: ', 'aria-label="Next ')):
            _n = new_text.count(_pre)
            if _n:
                labelname += _n
                new_text = new_text.replace(_pre, _rep)
        # alert-live region (18): mirror the bundle's alert$ status stream
        # ("Copied to clipboard" etc.) into a polite live region so WCAG
        # 4.1.3 status messages reach assistive tech without focus
        if "</body>" in new_text and alert_live_html not in new_text:
            new_text = new_text.replace("</body>", alert_live_html + "</body>", 1)
            alertlive += 1
        # decorative icon svgs (19): Material emits every icon as a bare
        # <svg xmlns="http://www.w3.org/2000/svg" viewBox=...> with no role,
        # no <title> and no aria-hidden - 7,083 across the built corpus, and
        # every one of them is a chrome/content icon sitting inside a control
        # that already carries its accessible name (upstream aria-label, the
        # label's own text, or blocks 2/11/12 above). A bare inline svg
        # computes no accessible name and conveys nothing on its own, so
        # this is not a 1.1.1 hard fail - but some AT combos surface an
        # unmarked inline svg as an unlabeled "graphic" between the named
        # controls, and the standard decorative marker aria-hidden="true"
        # is missing corpus-wide. The literal prefix
        # '<svg xmlns="http://www.w3.org/2000/svg"' is corpus-unique
        # (7,083/7,083 open tags carry xmlns as the first attribute - census
        # before the fix), so a prefix rewrite covers every svg and only
        # svgs; runtime-created svgs (mermaid diagrams) are not in the
        # static HTML and are untouched. The negative lookahead keeps the
        # rewrite idempotent if it ever sees already-patched text.
        new_text, _nsvg = re.subn(
            r'<svg xmlns="http://www\.w3\.org/2000/svg"(?! aria-hidden=)',
            '<svg xmlns="http://www.w3.org/2000/svg" aria-hidden="true"',
            new_text)
        svgdec += _nsvg
        # sidebar index-toggle labels (12a): name the bare icon-only section
        # toggles from their sibling <a> title, and (12b) drop the dead
        # __toc for= on pages whose __toc input was never emitted
        def _navlab(m):
            nonlocal navlab
            title = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", m.group(2)))).strip()
            if not title:
                return m.group(0)
            navlab += 1
            return m.group(1) + m.group(3) + f' aria-label="{_html.escape(title, quote=True)}">' + m.group(4)
        new_text = nav_idx_container_re.sub(_navlab, new_text)
        if toc_title_label in new_text and 'id="__toc"' not in new_text:
            tocdead += new_text.count(toc_title_label)
            new_text = new_text.replace(toc_title_label, '<label class="md-nav__title">')
        # broken panel aria-labelledby (12c): mint the missing id on the
        # panel's own title label so the reference resolves to real text
        for p in set(lly_re.findall(new_text)):
            if f'id="{p}"' not in new_text:
                base = p[:-len("_label")]
                old = f'<label class="md-nav__title" for="{base}">'
                if old in new_text:
                    navtitle += new_text.count(old)
                    new_text = new_text.replace(
                        old, f'<label class="md-nav__title" id="{p}" for="{base}">')
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
    print(f"[hooks] header labels: {searchlab} search + {drawerlab} drawer icon toggle(s) named")
    print(f"[hooks] drawer keyboard: {drawertab} toggle(s) made focusable; {drawerkey} key handler(s) injected")
    print(f"[hooks] reduced-motion: {motionin} scroll shim(s) injected")
    print(f"[hooks] search-focus: {searchfocus} return handler(s) injected")
    print(f"[hooks] highlight-fix: {hlf} guard script(s) injected")
    print(f"[hooks] label-in-name: {labelname} footer prev/next aria-label(s) colon-aligned")
    print(f"[hooks] alert-live: {alertlive} status region script(s) injected")
    print(f"[hooks] svg decorative: {svgdec} icon svg(s) marked aria-hidden")
    print(f"[hooks] nav labels: {navlab} index toggle(s) named; {tocdead} dead __toc for= dropped; {navtitle} broken panel aria-labelledby re-pointed")
