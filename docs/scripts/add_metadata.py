#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated metadata migration tool for PROJECT-OMEGA documents.
Adds frontmatter metadata to all technical documents.

Usage:
    python add_metadata.py --dry-run    # Preview changes
    python add_metadata.py --execute     # Apply changes
    python add_metadata.py --limit 10    # Process first 10 documents
"""

import os
import re
import sys
import argparse

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
from pathlib import Path
from datetime import datetime

# Metadata mapping based on document ID patterns
METADATA_PATTERNS = {
    # Phase 1 - Infrastructure
    r"11\d{2}": {
        "phase": "1",
        "difficulty": "Beginner",
        "estimated_time": "2 hours",
        "tags": ["infrastructure", "networking", "hardware"]
    },
    r"12\d{2}": {
        "phase": "1",
        "difficulty": "Intermediate",
        "estimated_time": "3 hours",
        "tags": ["infrastructure", "virtualization", "proxmox", "gpu"]
    },
    r"13\d{2}": {
        "phase": "1",
        "difficulty": "Intermediate",
        "estimated_time": "3 hours",
        "tags": ["infrastructure", "kubernetes", "k3s", "gpu"]
    },
    r"14\d{2}": {
        "phase": "1",
        "difficulty": "Advanced",
        "estimated_time": "4 hours",
        "tags": ["infrastructure", "llmops", "ollama", "vllm", "tgi"]
    },
    r"15\d{2}": {
        "phase": "1",
        "difficulty": "Advanced",
        "estimated_time": "3 hours",
        "tags": ["infrastructure", "monitoring", "observability", "prometheus"]
    },
    # Phase 2 - Foundations
    r"21\d{2}": {
        "phase": "2",
        "difficulty": "Intermediate",
        "estimated_time": "4 hours",
        "tags": ["math", "calculus", "tensors", "backpropagation"]
    },
    r"22\d{2}": {
        "phase": "2",
        "difficulty": "Intermediate",
        "estimated_time": "4 hours",
        "tags": ["frameworks", "pytorch", "tensorflow", "cuda"]
    },
    r"23\d{2}": {
        "phase": "2",
        "difficulty": "Advanced",
        "estimated_time": "5 hours",
        "tags": ["frameworks", "architecture", "api-design", "production"]
    },
    r"24\d{2}": {
        "phase": "2",
        "difficulty": "Advanced",
        "estimated_time": "6 hours",
        "tags": ["training", "pretraining", "evaluation", "fsdp"]
    },
    # Phase 3 - Transformers
    r"31\d{2}": {
        "phase": "3",
        "difficulty": "Advanced",
        "estimated_time": "4 hours",
        "tags": ["transformers", "attention", "self-attention", "flash-attention"]
    },
    r"32\d{2}": {
        "phase": "3",
        "difficulty": "Intermediate",
        "estimated_time": "3 hours",
        "tags": ["transformers", "embeddings", "rope", "tokenization", "bpe"]
    },
    r"33\d{2}": {
        "phase": "3",
        "difficulty": "Beginner",
        "estimated_time": "2 hours",
        "tags": ["transformers", "activation", "gelu", "swiglu", "normalization"]
    },
    r"34\d{2}": {
        "phase": "3",
        "difficulty": "Intermediate",
        "estimated_time": "4 hours",
        "tags": ["transformers", "architecture", "encoder-decoder", "gpt", "llama"]
    },
    r"35\d{2}": {
        "phase": "3",
        "difficulty": "Advanced",
        "estimated_time": "5 hours",
        "tags": ["transformers", "multimodal", "vision-language", "clip", "audio"]
    },
    # Phase 4 - Quantization
    r"41\d{2}": {
        "phase": "4",
        "difficulty": "Advanced",
        "estimated_time": "4 hours",
        "tags": ["quantization", "gguf", "exl2", "awq", "compression"]
    },
    r"42\d{2}": {
        "phase": "4",
        "difficulty": "Advanced",
        "estimated_time": "4 hours",
        "tags": ["quantization", "kv-cache", "context-window", "speculative-decoding"]
    },
    r"43\d{2}": {
        "phase": "4",
        "difficulty": "Advanced",
        "estimated_time": "4 hours",
        "tags": ["quantization", "qat", "quantization-aware-training"]
    },
    r"44\d{2}": {
        "phase": "4",
        "difficulty": "Expert",
        "estimated_time": "5 hours",
        "tags": ["quantization", "advanced", "optimization"]
    },
    # Phase 5 - Fine-tuning
    r"51\d{2}": {
        "phase": "5",
        "difficulty": "Advanced",
        "estimated_time": "5 hours",
        "tags": ["finetuning", "peft", "lora", "qlora", "adaptation"]
    },
    r"52\d{2}": {
        "phase": "5",
        "difficulty": "Advanced",
        "estimated_time": "4 hours",
        "tags": ["finetuning", "alignment", "dpo", "rlhf", "preference"]
    },
    r"53\d{2}": {
        "phase": "5",
        "difficulty": "Advanced",
        "estimated_time": "4 hours",
        "tags": ["finetuning", "synthetic-data", "distillation", "federated"]
    },
    # Phase 6 - RAG
    r"61\d{2}": {
        "phase": "6",
        "difficulty": "Intermediate",
        "estimated_time": "3 hours",
        "tags": ["rag", "vectors", "hnsw", "embeddings", "similarity"]
    },
    r"62\d{2}": {
        "phase": "6",
        "difficulty": "Intermediate",
        "estimated_time": "3 hours",
        "tags": ["rag", "retrieval", "hybrid-search", "reranking"]
    },
    r"63\d{2}": {
        "phase": "6",
        "difficulty": "Advanced",
        "estimated_time": "5 hours",
        "tags": ["rag", "context", "graphrag", "neo4j", "knowledge-graphs"]
    },
    r"64\d{2}": {
        "phase": "6",
        "difficulty": "Intermediate",
        "estimated_time": "3 hours",
        "tags": ["rag", "vector-db", "qdrant", "pinecone", "weaviate"]
    },
    r"65\d{2}": {
        "phase": "6",
        "difficulty": "Advanced",
        "estimated_time": "4 hours",
        "tags": ["mlops", "pipeline", "ci-cd", "model-registry", "lifecycle"]
    },
    # Phase 7 - Agents
    r"71\d{2}": {
        "phase": "7",
        "difficulty": "Advanced",
        "estimated_time": "4 hours",
        "tags": ["agents", "react", "planning", "autonomy", "cognition"]
    },
    r"72\d{2}": {
        "phase": "7",
        "difficulty": "Intermediate",
        "estimated_time": "3 hours",
        "tags": ["agents", "tool-calling", "function-calling", "code-interpreter"]
    },
    r"73\d{2}": {
        "phase": "7",
        "difficulty": "Advanced",
        "estimated_time": "4 hours",
        "tags": ["agents", "orchestration", "multi-agent", "autogen", "langgraph"]
    },
    r"74\d{2}": {
        "phase": "7",
        "difficulty": "Advanced",
        "estimated_time": "4 hours",
        "tags": ["agents", "memory", "vector-store", "long-term-memory"]
    },
    r"75\d{2}": {
        "phase": "7",
        "difficulty": "Advanced",
        "estimated_time": "3 hours",
        "tags": ["agents", "security", "prompt-injection", "pii", "adversarial"]
    },
}


def extract_document_id(filename):
    """Extract document ID from filename."""
    match = re.match(r'(\d{4})', filename)
    return match.group(1) if match else None


def extract_title(content, filename):
    """Extract title from content or generate from filename."""
    # Try to find first H1 heading
    h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if h1_match:
        title = h1_match.group(1).strip()
        # Remove document ID prefix if present
        title = re.sub(r'^\d{4}:\s*', '', title)
        return title
    # Generate from filename
    return filename.replace('.md', '').replace('-', ' ')


def extract_module(doc_id):
    """Extract module number from document ID."""
    return doc_id[0:2] + '00'


def get_metadata_for_document(doc_id, title):
    """Generate metadata for a document based on its ID."""
    for pattern, metadata in METADATA_PATTERNS.items():
        if re.match(pattern, doc_id):
            base_metadata = metadata.copy()
            base_metadata['document_id'] = doc_id
            base_metadata['title'] = title
            base_metadata['module'] = extract_module(doc_id)
            base_metadata['last_updated'] = datetime.now().strftime('%Y-%m-%d')
            base_metadata['status'] = 'Complete'
            return base_metadata

    # Default metadata if no pattern match
    return {
        'document_id': doc_id,
        'title': title,
        'phase': 'Unknown',
        'module': extract_module(doc_id),
        'last_updated': datetime.now().strftime('%Y-%m-%d'),
        'status': 'Review',
        'difficulty': 'Intermediate',
        'estimated_time': '3 hours',
        'tags': ['documentation'],
    }


def generate_frontmatter(metadata):
    """Generate YAML frontmatter from metadata dictionary."""
    frontmatter = "---\n"
    frontmatter += f"Document ID: {metadata['document_id']}\n"
    frontmatter += f"Title: {metadata['title']}\n"
    frontmatter += f"Phase: {metadata['phase']}\n"
    frontmatter += f"Module: {metadata['module']}\n"
    frontmatter += f"Last Updated: {metadata['last_updated']}\n"
    frontmatter += f"Status: {metadata['status']}\n"
    frontmatter += f"Difficulty: {metadata['difficulty']}\n"
    frontmatter += f"Estimated Time: {metadata['estimated_time']}\n"
    frontmatter += f"Prerequisites: See module README\n"
    frontmatter += f"Related: See module README\n"
    frontmatter += f"Tags: {metadata['tags']}\n"
    frontmatter += "---\n\n"
    return frontmatter


def document_needs_migration(filepath):
    """Check if a document needs metadata migration."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            return not first_line.strip() == '---'
    except:
        return False


def migrate_document(filepath, dry_run=False):
    """Add frontmatter metadata to a document."""
    if not document_needs_migration(filepath):
        return {'status': 'skip', 'reason': 'Already has frontmatter'}

    filename = Path(filepath).name
    doc_id = extract_document_id(filename)

    if not doc_id:
        return {'status': 'skip', 'reason': 'No document ID found'}

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except Exception as e:
        return {'status': 'error', 'reason': str(e)}

    title = extract_title(original_content, filename)
    metadata = get_metadata_for_document(doc_id, title)
    frontmatter = generate_frontmatter(metadata)

    new_content = frontmatter + original_content

    if dry_run:
        return {
            'status': 'preview',
            'file': filepath,
            'doc_id': doc_id,
            'frontmatter': frontmatter.strip()
        }

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return {
            'status': 'success',
            'file': str(filepath),
            'doc_id': doc_id
        }
    except Exception as e:
        return {'status': 'error', 'reason': str(e)}


def find_documents_to_migrate(root_dir):
    """Find all markdown documents that need migration."""
    docs = []
    root_path = Path(root_dir)

    # Search in phases directory
    for md_file in root_path.rglob('*.md'):
        # Skip README, assessment, and guide files
        if any(x in md_file.name for x in ['README', 'QUIZ', 'PRACTICE']):
            continue
        if md_file.name.startswith('TUTORIAL'):
            continue
        if md_file.name.startswith('LAB-'):
            continue
        if md_file.name.startswith('CHEAT'):
            continue
        if md_file.name.startswith('PROJECT'):
            continue
        if 'guides' in str(md_file):
            continue
        if 'assessment' in str(md_file):
            continue
        if '00-META' in str(md_file):
            continue
        if 'learning-resources' in str(md_file):
            continue
        if 'volumes' in str(md_file):
            continue
        if 'comparisons' in str(md_file):
            continue
        if 'industry' in str(md_file):
            continue
        if 'configs' in str(md_file):
            continue
        if 'experiments' in str(md_file):
            continue

        if document_needs_migration(md_file):
            docs.append(md_file)

    return sorted(docs)


def main():
    parser = argparse.ArgumentParser(
        description='Migrate PROJECT-OMEGA documents with frontmatter metadata'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying them'
    )
    parser.add_argument(
        '--docs-dir',
        default='.',
        help='Path to docs directory (default: current directory)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of documents to process'
    )

    args = parser.parse_args()

    docs = find_documents_to_migrate(args.docs_dir)

    print(f"Found {len(docs)} documents to migrate\n")

    if args.dry_run:
        print("DRY RUN MODE - No changes will be applied\n")

    results = {
        'success': [],
        'skip': [],
        'preview': [],
        'error': []
    }

    for i, doc in enumerate(docs[:args.limit] if args.limit else docs):
        result = migrate_document(doc, dry_run=args.dry_run)

        if result['status'] == 'success':
            results['success'].append(result)
            print(f"✅ {result['doc_id']}: {doc}")
        elif result['status'] == 'preview':
            results['preview'].append(result)
            print(f"\n📋 PREVIEW: {result['doc_id']} - {doc}")
            print(result['frontmatter'][:150] + "...")
            print()
        elif result['status'] == 'skip':
            results['skip'].append(result)
            print(f"⏭️  SKIP: {doc} - {result['reason']}")
        elif result['status'] == 'error':
            results['error'].append(result)
            print(f"❌ ERROR: {doc} - {result['reason']}")

        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"\nProgress: {i + 1}/{len(docs)}\n")

    # Summary
    print(f"\n{'='*60}")
    print(f"MIGRATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total documents found: {len(docs)}")
    print(f"Would migrate: {len(results['success']) if not args.dry_run else len(results['preview'])}")
    print(f"Skipped: {len(results['skip'])}")
    print(f"Errors: {len(results['error'])}")

    if args.dry_run:
        print(f"\n🔍 DRY RUN COMPLETE - Run without --dry-run to apply changes")


if __name__ == '__main__':
    main()
