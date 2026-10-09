# -*- coding: utf-8 -*-
"""mkdocs hook: publish repo-root companion material alongside the built site.

Corpus docs link to repo-root experiments/, configs/, and README.md via
relative paths (e.g. ../../experiments/EXP_1101_GPON.md). mkdocs builds only
docs/, so on the deployed site those links would 404. This hook copies the
companion material into site/ after the build so every link resolves; GitHub
Pages serves the raw .md/.yml/.js files as plain text.
"""


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
    import re

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
