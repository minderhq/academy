#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add Next Steps sections to remaining PROJECT-OMEGA documents.
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

def get_extended_mapping():
    """Extended mapping including documents missing Next Steps."""
    return {
        # Phase 1 - LLMOps Guides
        "1404": ("1405", "1405-TGI-Deployment-Guide.md", "same", "guides"),
        "1405": (None, None, "module_complete", "guides"),

        # Phase 2 - Framework Engineering Guides
        "2305": ("2306", "2306-Building-Production-Framework.md", "same", "guides"),
        "2306": (None, None, "module_complete", "guides"),

        # Phase 3 - Attention & Architecture
        "3101": ("3201", "../3200-embeddings/3201-Rotary-Positional-Embeddings-RoPE.md", "up", None),
        "3303": (None, None, "module_complete", "guides"),
        "3403": (None, None, "module_complete", "guides"),

        # Phase 4 - KV Cache & QAT
        "4203": (None, None, "module_complete", "guides"),
        "4308": (None, None, "module_complete", "guides"),
        "4408": (None, None, "module_complete", "guides"),

        # Phase 5 - PEFT & Synthetic
        "5104": (None, None, "module_complete", "guides"),
        "5302": ("5303", "5303-Federated-Learning.md", "same", None),
        "5303": ("5401", "../5400-distributed-training/5401-Data-Parallelism.md", "up", None),

        # Phase 6 - RAG
        "6103": (None, None, "module_complete", "guides"),
        "6302": ("6401", "../6400-vector-databases/6401-Qdrant-Setup.md", "up", None),
        "6303": (None, None, "module_complete", "guides"),
        "6304": (None, None, "module_complete", "guides"),
        "6403": (None, None, "module_complete", "guides"),
        "6503": (None, None, "phase_complete", None),

        # Phase 7 - Agents
        "7103": (None, None, "module_complete", "guides"),
        "7202": (None, None, "module_complete", "guides"),
        "7303": (None, None, "module_complete", "guides"),
        "7402": (None, None, "module_complete", "guides"),
        "7503": (None, None, "phase_complete", None),
    }

def get_phase_completion_text(doc_id, filepath):
    """Get appropriate phase completion text."""
    # Determine which phase this is in
    if "phase1" in str(filepath):
        return "Phase 1 Complete! Next: **[Phase 2: Foundations](../../phase2-foundations/)**"
    elif "phase2" in str(filepath):
        return "Phase 2 Complete! Next: **[Phase 3: Transformers](../../phase3-transformers/)**"
    elif "phase3" in str(filepath):
        return "Phase 3 Complete! Next: **[Phase 4: Quantization](../../phase4-quantization/)**"
    elif "phase4" in str(filepath):
        return "Phase 4 Complete! Next: **[Phase 5: Fine-Tuning](../../phase5-finetuning/)**"
    elif "phase5" in str(filepath):
        return "Phase 5 Complete! Next: **[Phase 6: RAG](../../phase6-rag/)**"
    elif "phase6" in str(filepath):
        return "Phase 6 Complete! Next: **[Phase 7: Agents](../../phase7-agentic/)**"
    elif "phase7" in str(filepath):
        return "🎉 **Phase 7 Complete!** You've mastered the entire PROJECT-OMEGA curriculum!"
    return "Module Complete!"

def get_module_readme_link(filepath):
    """Find link to module README."""
    # Navigate to the module directory
    path_parts = filepath.parts
    # Find the module directory (XXXX-*)
    for i, part in enumerate(path_parts):
        if re.match(r'\d{4}-', part):
            # Found module directory
            readme_path = Path(*path_parts[:i+1]) / "README.md"
            if readme_path.exists():
                return f"**[Module README](./{readme_path.name})**"
    return None

def add_next_steps_to_file(filepath, doc_id, next_info):
    """Add Next Steps section to a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip if already has Next Steps
        if '## Next Steps' in content:
            return False, "Already has Next Steps"

        # Find the end of the file
        lines = content.split('\n')
        insert_pos = len(lines)

        # Find position to insert (before last "---" if it exists near end)
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == '---' and i > len(lines) // 2:
                insert_pos = i
                break

        # Build next steps content
        next_doc_id, next_file, relation, is_guide = next_info

        if relation == "phase_complete":
            next_text = get_phase_completion_text(doc_id, filepath)
        elif relation == "module_complete":
            # Link to module README
            readme_link = get_module_readme_link(filepath)
            if readme_link:
                next_text = f"Return to: {readme_link}"
            else:
                next_text = "Module Complete!"
        elif next_file is None:
            next_text = "Module Complete!"
        elif is_guide == "guides":
            next_text = f"Continue with: **[{next_file}](./{next_file})**"
        elif relation == "same":
            next_text = f"Continue with: **[{next_doc_id}: {next_file}](./{next_file})**"
        elif relation == "up":
            next_text = f"Continue with: **[{next_file}](./{next_file})**"
        else:
            next_text = "Continue learning!"

        # Build Next Steps section
        next_steps = [
            "",
            "---",
            "",
            "## Next Steps",
            "",
            f"- {next_text}",
        ]

        # Add assessment link if exists
        assessment_path = filepath.parent / "assessment" / "QUIZ.md"
        if assessment_path.exists():
            next_steps.append(f"- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**")

        next_steps.extend(["", "---"])

        # Insert Next Steps
        lines.insert(insert_pos, '\n'.join(next_steps))

        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        return True, "Added Next Steps"

    except Exception as e:
        return False, str(e)

def main():
    phases_dir = Path("C:/AI-Studio/PROJECT-OMEGA/docs/phases")
    mapping = get_extended_mapping()

    results = {
        'success': [],
        'skip': [],
        'error': []
    }

    for doc_id, next_info in mapping.items():
        # Find file
        for filepath in phases_dir.rglob(f"{doc_id}-*.md"):
            if filepath.name.startswith(doc_id + '-'):
                success, message = add_next_steps_to_file(filepath, doc_id, next_info)

                if success:
                    results['success'].append((doc_id, filepath))
                    print(f"✅ {doc_id}: {filepath.name}")
                elif "Already has" in message:
                    results['skip'].append((doc_id, message))
                    print(f"⏭️  SKIP: {doc_id} - {message}")
                else:
                    results['error'].append((doc_id, message))
                    print(f"❌ ERROR: {doc_id} - {message}")
                break

    # Summary
    print(f"\n{'='*60}")
    print(f"NEXT STEPS ADDITION SUMMARY")
    print(f"{'='*60}")
    print(f"Success: {len(results['success'])}")
    print(f"Skipped: {len(results['skip'])}")
    print(f"Errors: {len(results['error'])}")

if __name__ == '__main__':
    main()
