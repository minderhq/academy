#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add Next Steps sections to PROJECT-OMEGA documents.
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

def get_next_steps_mapping():
    """Define next document for each document based on learning path."""
    return {
        # Phase 4 - QAT
        "4301": ("4302", "4302-Fake-Quantization.md", "same"),
        "4302": ("4303", "4303-QAT-for-Transformers.md", "same"),
        "4303": ("4304", "4304-Low-bit-QAT.md", "same"),
        "4304": ("4305", "4305-Quantization-Configuration.md", "same"),
        "4305": ("4401", "../4400-advanced-techniques/4401-GPTQ.md", "up"),

        # Phase 4 - Advanced
        "4401": ("4402", "4402-AWQ.md", "same"),
        "4402": ("4403", "4403-GGUF-Format.md", "same"),
        "4403": ("4404", "4404-EXL2-Format.md", "same"),
        "4404": ("5101", "../../phase5-finetuning/5100-peft/5101-LoRA-Logic.md", "phase5"),

        # Phase 5 - PEFT
        "5101": ("5102", "5102-QLoRA-Pipelines.md", "same"),
        "5102": ("5201", "../5200-alignment/5201-RLHF-Fundamentals.md", "up"),

        # Phase 5 - Alignment
        "5201": ("5202", "5202-DPO-Fundamentals.md", "same"),
        "5202": ("5301", "../5300-synthetic/5301-Synthetic-Data.md", "up"),

        # Phase 5 - Synthetic
        "5301": ("5401", "../5400-distributed-training/5401-Data-Parallelism.md", "up"),

        # Phase 5 - Distributed
        "5401": ("5501", "../5500-advanced-optimization/5501-Optimizer-Variants.md", "up"),
        "5501": ("6101", "../../phase6-rag/6100-vector/6101-HNSW-Indexing.md", "phase6"),

        # Phase 6 - Vector
        "6101": ("6102", "6102-Vector-Embeddings.md", "same"),
        "6102": ("6201", "../6200-retrieval/6201-Hybrid-Search.md", "up"),

        # Phase 6 - Retrieval
        "6201": ("6202", "6202-Re-ranking.md", "same"),
        "6202": ("6301", "../6300-context/6301-Context-Window-Optimization.md", "up"),

        # Phase 6 - Context
        "6301": ("6401", "../6400-vector-databases/6401-Qdrant.md", "up"),

        # Phase 6 - Vector DBs
        "6401": ("6402", "6402-Pinecone.md", "same"),
        "6402": ("6501", "../6500-mlops-pipelines/6501-ML-Lifecycle-Management.md", "up"),

        # Phase 6 - MLOps
        "6501": ("6502", "6502-CI-CD-Pipelines.md", "same"),
        "6502": ("7101", "../../phase7-agentic/7100-architecture/7101-ReAct-Loop-System.md", "phase7"),

        # Phase 7 - Architecture
        "7101": ("7102", "7102-Planning-Decomposition.md", "same"),
        "7102": ("7201", "../7200-tools/7201-Tool-Calling.md", "up"),

        # Phase 7 - Tools
        "7201": ("7301", "../7300-orchestration/7301-Orchestration.md", "up"),

        # Phase 7 - Orchestration
        "7301": ("7401", "../7400-memory/7401-Long-term-Memory.md", "up"),

        # Phase 7 - Memory
        "7401": ("7501", "../7500-security/7501-Prompt-Injection-Defense.md", "up"),

        # Phase 7 - Security
        "7501": ("7502", "7502-PII-Redaction.md", "same"),
        "7502": ("7503", "7503-Adversarial-Attacks.md", "same"),
    }

def add_next_steps_to_file(filepath, next_info):
    """Add Next Steps section to a file."""
    doc_id, next_file, relation = next_info

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip if already has Next Steps
        if '## Next Steps' in content:
            return False, "Already has Next Steps"

        # Find the end of the file (before closing metadata if exists)
        lines = content.split('\n')

        # Find position to insert (before last "---" if it exists)
        insert_pos = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == '---' and i > len(lines) // 2:
                insert_pos = i
                break

        # Determine next text based on relation
        if relation == "same":
            next_text = f"Continue with: **[{doc_id}: Next Document](./{next_file})**"
        elif relation == "up":
            next_text = f"Continue with: **[{next_file.split('/')[-1]}](./{next_file})**"
        elif relation == "phase5":
            next_text = f"Phase 4 Complete! Next: **[Phase 5: Fine-Tuning](../../phase5-finetuning/)**"
        elif relation == "phase6":
            next_text = f"Phase 5 Complete! Next: **[Phase 6: RAG](../../phase6-rag/)**"
        elif relation == "phase7":
            next_text = f"Phase 6 Complete! Next: **[Phase 7: Agents](../../phase7-agentic/)**"

        # Build Next Steps section
        next_steps = [
            "",
            "---",
            "",
            "## Next Steps",
            "",
            f"- {next_text}",
            "- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**",
            "",
            "---"
        ]

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
    mapping = get_next_steps_mapping()

    results = {
        'success': [],
        'skip': [],
        'error': []
    }

    for doc_id, next_info in mapping.items():
        # Find file
        for filepath in phases_dir.rglob(f"{doc_id}-*.md"):
            if filepath.name.startswith(doc_id + '-'):
                success, message = add_next_steps_to_file(filepath, next_info)

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
