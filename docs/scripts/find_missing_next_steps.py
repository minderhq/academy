#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Find main documents missing Next Steps sections.
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
    # Main documents have pattern XXXX-Title.md where XXXX is 4 digits
    filename = os.path.basename(filepath)
    return bool(re.match(r'^\d{4}-.*\.md$', filename))

def has_next_steps(filepath):
    """Check if file has Next Steps section."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            return '## Next Steps' in content
    except:
        return False

def main():
    phases_dir = Path("C:/AI-Studio/PROJECT-OMEGA/docs/phases")

    # Find all main documents
    all_main_docs = []
    missing_next_steps = []

    for filepath in phases_dir.rglob("*.md"):
        if is_main_document(filepath):
            all_main_docs.append(filepath)
            if not has_next_steps(filepath):
                missing_next_steps.append(filepath)

    print(f"Total main documents: {len(all_main_docs)}")
    print(f"Documents with Next Steps: {len(all_main_docs) - len(missing_next_steps)}")
    print(f"Documents missing Next Steps: {len(missing_next_steps)}")
    print()

    if missing_next_steps:
        print("Documents missing Next Steps:")
        for filepath in missing_next_steps:
            rel_path = filepath.relative_to(phases_dir)
            print(f"  - {rel_path}")
    else:
        print("All main documents have Next Steps!")

if __name__ == '__main__':
    main()
