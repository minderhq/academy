#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix template compliance: Replace first "## Overview" with "## Abstract".
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
    """Check if file already has Abstract section."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            return bool(re.search(r'^## Abstract$', content, re.MULTILINE))
    except:
        return False

def fix_first_overview(filepath):
    """Replace first '## Overview' with '## Abstract'."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if already has Abstract
        if '## Abstract' in content:
            return False, "Already has Abstract"

        # Find title line (# XXXX: Title)
        lines = content.split('\n')
        title_idx = -1

        for i, line in enumerate(lines):
            if re.match(r'^# \d{4}:', line):
                title_idx = i
                break

        if title_idx < 0:
            return False, "No title found"

        # Look for first "## Overview" after title (within next 20 lines)
        overview_idx = -1
        for i in range(title_idx + 1, min(title_idx + 21, len(lines))):
            if lines[i].strip() == '## Overview':
                overview_idx = i
                break

        if overview_idx < 0:
            return False, "No Overview section found after title"

        # Replace "## Overview" with "## Abstract"
        lines[overview_idx] = lines[overview_idx].replace('## Overview', '## Abstract')

        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        return True, "Fixed Overview → Abstract"

    except Exception as e:
        return False, str(e)

def main():
    phases_dir = Path("C:/AI-Studio/PROJECT-OMEGA/docs/phases")

    results = {
        'fixed': [],
        'skipped': [],
        'error': []
    }

    # Find all main documents
    for filepath in phases_dir.rglob("*.md"):
        if is_main_document(filepath):
            if not has_abstract(filepath):
                success, message = fix_first_overview(filepath)

                if success:
                    results['fixed'].append((filepath, message))
                    rel_path = filepath.relative_to(phases_dir)
                    print(f"✅ Fixed: {rel_path}")
                elif "Already has" in message:
                    results['skipped'].append((filepath, message))
                else:
                    results['error'].append((filepath, message))
                    rel_path = filepath.relative_to(phases_dir)
                    print(f"⏭️  SKIP: {rel_path} - {message}")

    # Summary
    print(f"\n{'='*60}")
    print(f"TEMPLATE FIX SUMMARY")
    print(f"{'='*60}")
    print(f"Fixed: {len(results['fixed'])}")
    print(f"Skipped: {len(results['skipped'])}")
    print(f"Errors: {len(results['error'])}")

if __name__ == '__main__':
    main()
