#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix incorrect related document paths.
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

# Path corrections: (incorrect_pattern, correct_replacement)
PATH_CORRECTIONS = [
    # Module directory name corrections (capitalization)
    (r'\.\./1300-Kubernetes/', '../1300-kubernetes/'),
    (r'\.\./1200-Virtualization/', '../1200-virtualization/'),
    (r'\.\./2200-Framework-Engineering/', '../2200-framework-engineering/'),
    (r'\.\./4100-Low-Bit/', '../4100-low-bit/'),
    (r'\.\./5200-SFT-Preference/', '../5200-alignment/'),
    (r'\.\./7100-Reason/', '../7100-architecture/'),
    (r'\.\./7300-Tool-Calling/', '../7200-tools/'),

    # Incorrect module paths
    (r'\.\./7200-Multi-Agent/', '../7300-orchestration/'),
    (r'\.\./7200-Multi-Agent/7202-Collaborative-Tasking\.md', '../7300-orchestration/7301-Orchestration.md'),
    (r'\.\./7300-Tool-Calling/7301-Safe-Python-Interpreter\.md', '../7200-tools/7201-Tool-Calling.md'),

    # Cross-phase path corrections
    (r'\.\./\.\./6000-Data-Nexus/6200-RAG/', '../../phase6-rag/6200-retrieval/'),
    (r'\.\./\.\./6000-Data-Nexus/', '../../phase6-rag/'),
    (r'../../phase7-agentic/7100-Reason/', '../../phase7-agentic/7100-architecture/'),

    # File-specific corrections
    (r'\[5301: Knowledge Distillation\]\(\.\./5300-PEFT/5301-Knowledge-Distillation\.md\)',
     '[5301: Knowledge Distillation](../5300-synthetic/5301-Knowledge-Distillation.md)'),
]

# Specific file corrections (when the document ID is wrong)
DOC_ID_CORRECTIONS = [
    # Fix wrong document references
    (r'\[7201: AutoGen vs LangGraph\]\(\./7201-AutoGen-vs-LangGraph\.md\)',
     '[Related Guides](./guides/7303-Framework-Comparison.md)'),
]

def fix_related_paths_in_file(filepath):
    """Fix incorrect related document paths in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes_made = 0

        # Apply path corrections
        for pattern, replacement in PATH_CORRECTIONS:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                count = len(re.findall(pattern, original_content))
                changes_made += count
                content = new_content

        # Apply document ID corrections
        for pattern, replacement in DOC_ID_CORRECTIONS:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                count = len(re.findall(pattern, original_content))
                changes_made += count
                content = new_content

        if changes_made > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, f"Fixed {changes_made} path(s)"

        return False, "No changes needed"

    except Exception as e:
        return False, str(e)

def main():
    phases_dir = Path("C:/AI-Studio/PROJECT-OMEGA/docs/phases")

    results = {
        'fixed': [],
        'skipped': [],
        'error': []
    }

    # Find all markdown files
    for filepath in phases_dir.rglob("*.md"):
        success, message = fix_related_paths_in_file(filepath)

        if success:
            results['fixed'].append((filepath, message))
            rel_path = filepath.relative_to(phases_dir)
            print(f"✅ Fixed: {rel_path} - {message}")
        elif "No changes" in message:
            results['skipped'].append(filepath)
        else:
            results['error'].append((filepath, message))
            rel_path = filepath.relative_to(phases_dir)
            print(f"❌ ERROR: {rel_path} - {message}")

    # Summary
    print(f"\n{'='*60}")
    print(f"PATH FIX SUMMARY")
    print(f"{'='*60}")
    print(f"Fixed: {len(results['fixed'])} files")
    print(f"Skipped: {len(results['skipped'])} files")
    print(f"Errors: {len(results['error'])} files")

if __name__ == '__main__':
    main()
