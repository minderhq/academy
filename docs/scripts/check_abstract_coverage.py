#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check main documents for Abstract section compliance.
"""

import os
import re
import sys
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def is_main_document(filepath):
    """Check if file is a main technical document."""
    filename = os.path.basename(filepath)
    return bool(re.match(r'^\d{4}-.*\.md$', filename))

def has_abstract(filepath):
    """Check if file has Abstract section (not Overview)."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Check for ## Abstract (not Overview, not numbered sections)
            return bool(re.search(r'^## Abstract$', content, re.MULTILINE))
    except:
        return False

def has_overview_instead(filepath):
    """Check if file has Overview where Abstract should be."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            # Find the title line (# XXXX: Title)
            title_idx = -1
            for i, line in enumerate(lines):
                if re.match(r'^# \d{4}:', line):
                    title_idx = i
                    break

            # Check next 10 lines for ## Overview (should be ## Abstract)
            if title_idx >= 0:
                for i in range(title_idx + 1, min(title_idx + 11, len(lines))):
                    if lines[i].strip() == '## Overview':
                        return True
            return False
    except:
        return False

def main():
    phases_dir = Path("C:/AI-Studio/PROJECT-OMEGA/docs/phases")

    all_main_docs = []
    with_abstract = []
    with_overview = []
    missing_both = []

    for filepath in phases_dir.rglob("*.md"):
        if is_main_document(filepath):
            all_main_docs.append(filepath)

            if has_abstract(filepath):
                with_abstract.append(filepath)
            elif has_overview_instead(filepath):
                with_overview.append(filepath)
            else:
                missing_both.append(filepath)

    print(f"Total main documents: {len(all_main_docs)}")
    print(f"With Abstract section: {len(with_abstract)} ({100*len(with_abstract)/len(all_main_docs):.1f}%)")
    print(f"With Overview instead of Abstract: {len(with_overview)} ({100*len(with_overview)/len(all_main_docs):.1f}%)")
    print(f"Missing both: {len(missing_both)} ({100*len(missing_both)/len(all_main_docs):.1f}%)")
    print()

    if with_overview:
        print("Documents using 'Overview' instead of 'Abstract':")
        for filepath in with_overview:
            rel_path = filepath.relative_to(phases_dir)
            print(f"  - {rel_path}")

    if missing_both:
        print("\nDocuments missing both Abstract and Overview:")
        for filepath in missing_both:
            rel_path = filepath.relative_to(phases_dir)
            print(f"  - {rel_path}")

if __name__ == '__main__':
    main()
