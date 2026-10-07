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
