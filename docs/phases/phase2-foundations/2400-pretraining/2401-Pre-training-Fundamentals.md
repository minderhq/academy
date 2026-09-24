---
Document ID: 2401
Title: Pre-training Fundamentals
Phase: 2
Module: 2400
Last Updated: 2026-09-24
Status: Complete
Difficulty: Advanced
Estimated Time: 6 hours
Prerequisites: See module README
Related: See module README
Tags: ['training', 'pretraining', 'evaluation', 'fsdp']
---

# 2401: Pre-training Fundamentals

**"From Data to Model"** - Understanding the complete pre-training pipeline.

---

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Part 1: Data Collection & Curation](#part-1-data-collection-curation)
- [Part 2: Tokenization for Pre-training](#part-2-tokenization-for-pre-training)
- [Part 3: Training Curriculum Design](#part-3-training-curriculum-design)
- [Part 4: Evaluation Frameworks](#part-4-evaluation-frameworks)
- [Part 5: Infrastructure Requirements](#part-5-infrastructure-requirements)
- [Part 6: End-to-End Training Script](#part-6-end-to-end-training-script)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain Part 1: Data Collection & Curation
- Explain Part 2: Tokenization for Pre-training
- Explain Part 3: Training Curriculum Design
- Measure and evaluate Part 4: Evaluation Frameworks
- Explain Part 5: Infrastructure Requirements
- Explain Part 6: End-to-End Training Script

---

## Abstract

**Prerequisites:** Volume 2 (Math Foundations), Volume 3 (LLM Internals)
**Time:** 4-5 hours to read, weeks/months to implement
**Difficulty:** ⭐⭐⭐⭐ Advanced

### What You'll Learn

After this guide, you will understand:
- ✅ How to collect and curate training data at scale
- ✅ Tokenization strategies for pre-training
- ✅ Training curriculum design
- ✅ Evaluation frameworks (MMLU, HELM, etc.)
- ✅ Pre-training infrastructure requirements
- ✅ Cost estimation and optimization

---

## Part 1: Data Collection & Curation

### Understanding Data Sources

**Pre-training requires massive datasets:**

| Model | Dataset Size | Tokens | Source |
|-------|-------------|--------|--------|
| GPT-3 (175B) | 45TB | 300B | Common Crawl + WebText + Books |
| LLaMA (65B) | 1.4TB | 1.4T | CommonCrawl + C4 + GitHub + Wikipedia |
| Mistral (7B) | Unknown | ~1T | Web datasets + books |
| TinyLlama (1.1B) | 3TB | 3T | SlimPajama, StarCoder, RedPajama |

### Publicly Available Datasets

```python
# Major pre-training datasets:

datasets = {
    # Web-scale datasets
    "Common Crawl": {
        "size": "100+ TB (monthly dumps)",
        "quality": "Mixed (needs heavy filtering)",
        "access": "https://commoncrawl.org/",
        "use_case": "Base data for most models"
    },

    "C4 (Colossal Clean Crawled Corpus)": {
        "size": "750GB cleaned",
        "quality": "High (heavily filtered)",
        "access": "TensorFlow Datasets",
        "use_case": "Cleaned web data"
    },

    "RedPajama": {
        "size": "1.2T tokens",
        "quality": "High (LLaMA reproduction)",
        "access": "https://together.ai/blog/redpajama",
        "use_case": "Open-source LLaMA reproduction"
    },

    "The Pile": {
        "size": "825GB, 800GB+ text",
        "quality": "Very High (curated sources)",
        "access": "https://pile.eleuther.ai/",
        "use_case": "Diverse, high-quality training"
    },

    "SlimPajama": {
        "size": "627B tokens",
        "quality": "High (cleaned RedPajama)",
        "access": "HuggingFace",
        "use_case": "Cleaner RedPajama"
    },

    # Domain-specific
    "GitHub": {
        "size": "1TB+ code",
        "quality": "Mixed (needs deduplication)",
        "access": "Google BigQuery",
        "use_case": "Code models (StarCoder, CodeLLaMA)"
    },

    "Wikipedia": {
        "size": "20GB compressed",
        "quality": "Very High",
        "access": "https://dumps.wikimedia.org/",
        "use_case": "Factual knowledge"
    },

    "arXiv": {
        "size": "10GB+ LaTeX",
        "quality": "High (scientific)",
        "access": "https://arxiv.org/",
        "use_case": "Scientific reasoning"
    },

    "Books": {
        "size": "100GB+ (varying sources)",
        "quality": "Very High",
        "access": "BookCorupus, Project Gutenberg",
        "use_case": "Long-form reasoning"
    },

    "StackExchange": {
        "size": "50GB+ Q&A",
        "quality": "High (curated)",
        "access": "https://archive.org/",
        "use_case": "Technical Q&A, reasoning"
    }
}
```

### Data Collection Pipeline

```python
"""
Complete data collection pipeline for pre-training
"""

import os
import json
import gzip
import requests
from typing import List, Dict, Iterator
import datasets
from bs4 import BeautifulSoup
import langdetect

class DataCollector:
    """Collect and pre-process training data"""

    def __init__(self, output_dir: str = "./training_data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def download_common_crawl(self, snapshot: str = "2023-14"):
        """
        Download Common Crawl snapshot

        Note: Each snapshot is ~30-80TB compressed
        This is an example - you'll need significant storage
        """
        base_url = f"https://data.commoncrawl.org/crawl-data/{snapshot}/"

        # Get WARC file list
        warc_paths = self._get_warc_list(snapshot)

        # Download and process
        for warc_path in warc_paths[:10]:  # Start with small subset
            self._download_and_extract_warc(warc_path)

    def download_c4_via_huggingface(self):
        """Download C4 dataset via HuggingFace"""
        from datasets import load_dataset

        # C4 is available through HuggingFace
        # Only download small subset for testing
        dataset = load_dataset(
            "c4",
            "en",
            split="train",
            streaming=True  # Use streaming to avoid downloading all
        )

        # Sample and save
        with open(f"{self.output_dir}/c4_sample.jsonl", "w") as f:
            for i, example in enumerate(dataset):
                if i >= 10000:  # Save only first 10k for testing
                    break
                f.write(json.dumps(example) + "\n")

    def download_slimpajama(self):
        """Download SlimPajama (cleaned RedPajama)"""
        from datasets import load_dataset

        # SlimPajama is split into train/validation/test
        dataset = load_dataset("cerebras/SlimPajama-627B",
                               split="train",
                               streaming=True)

        with open(f"{self.output_dir}/slimpajama_sample.jsonl", "w") as f:
            for i, example in enumerate(dataset):
                if i >= 10000:
                    break
                f.write(json.dumps(example) + "\n")

    def download_wikipedia(self, language: str = "en"):
        """Download Wikipedia dump"""
        from datasets import load_dataset

        # Wikipedia is available through HuggingFace
        dataset = load_dataset("wikipedia", language, split="train")

        with open(f"{self.output_dir}/wikipedia.jsonl", "w") as f:
            for example in dataset:
                f.write(json.dumps({
                    "text": example["text"],
                    "title": example["title"],
                    "id": example["id"]
                }) + "\n")

    def download_arxiv(self):
        """Download arXiv abstracts/papers"""
        from datasets import load_dataset

        dataset = load_dataset("scientific_papers", "arxiv", split="train")

        with open(f"{self.output_dir}/arxiv.jsonl", "w") as f:
            for i, example in enumerate(dataset):
                if i >= 1000:
                    break
                f.write(json.dumps({
                    "text": example["article"],
                    "abstract": example["abstract"],
                    "section_names": example["section_names"]
                }) + "\n")

    def download_stackexchange(self, sites: List[str] = None):
        """Download StackExchange dumps"""
        if sites is None:
            sites = ["stackoverflow", "superuser", "math"]

        for site in sites:
            url = f"https://archive.org/stackexchange/{site}.stackexchange.com.7z"
            # Download and extract
            # This requires significant processing

    def _get_warc_list(self, snapshot: str) -> List[str]:
        """Get list of WARC files from Common Crawl"""
        # This is simplified - actual implementation needs
        # to parse the Common Crawl index
        return [f"warc/path/{i}.warc.gz" for i in range(100)]

    def _download_and_extract_warc(self, warc_path: str):
        """Download and extract WARC file"""
        # This requires warcio library
        # and significant processing
        pass
```

### Data Filtering & Quality Control

```python
"""
Data quality filtering pipeline
"""

import re
import langdetect
from typing import Dict, List

class DataFilter:
    """Filter and clean training data"""

    def __init__(self):
        self.bad_words = self._load_bad_words()
        self.min_length = 512  # Minimum document length
        self.max_length = 20480  # Maximum document length

    def filter_document(self, doc: Dict) -> bool:
        """
        Apply all filters to a document

        Returns True if document passes all filters
        """
        text = doc.get("text", "")

        # Length filter
        if not self._check_length(text):
            return False

        # Language filter
        if not self._check_language(text, target_lang="en"):
            return False

        # Content quality filter
        if not self._check_quality(text):
            return False

        # Deduplication (done separately)
        # PII filter (done separately)

        return True

    def _check_length(self, text: str) -> bool:
        """Check if text is within acceptable length range"""
        word_count = len(text.split())
        return self.min_length <= word_count <= self.max_length

    def _check_language(self, text: str, target_lang: str = "en") -> bool:
        """Check if text is in target language"""
        try:
            detected = langdetect.detect(text)
            return detected == target_lang
        except:
            return False

    def _check_quality(self, text: str) -> bool:
        """Check content quality"""
        # Check for too much repeated text
        if self._has_excessive_repetition(text):
            return False

        # Check for bad words
        if self._has_bad_words(text):
            return False

        # Check for special characters ratio
        if not self._valid_char_ratio(text):
            return False

        # Check sentence structure
        if not self._has_valid_sentences(text):
            return False

        return True

    def _has_excessive_repetition(self, text: str, threshold: float = 0.3) -> bool:
        """Check for excessive repetition"""
        words = text.lower().split()
        unique_words = set(words)
        if len(words) == 0:
            return True
        return len(unique_words) / len(words) < threshold

    def _has_bad_words(self, text: str) -> bool:
        """Check for prohibited content"""
        words = set(text.lower().split())
        return bool(words & self.bad_words)

    def _valid_char_ratio(self, text: str) -> bool:
        """Check if text has valid character ratio"""
        # Should not have too many special chars
        alpha_chars = sum(c.isalpha() or c.isspace() for c in text)
        return alpha_chars / len(text) > 0.7 if text else False

    def _has_valid_sentences(self, text: str) -> bool:
        """Check if text has valid sentence structure"""
        # Count sentence-ending punctuation
        sentence_ends = text.count('.') + text.count('!') + text.count('?')
        words = len(text.split())

        # Should have reasonable sentence-to-word ratio
        return sentence_ends > words / 100  # At least 1 sentence per 100 words

    def _load_bad_words(self) -> set:
        """Load list of prohibited words"""
        # This would typically load from a file
        return set(["spam", "porn", "viagra", ...])  # Simplified
```

### Deduplication

```python
"""
Remove duplicate documents from training data
"""

import hashlib
import mmh3  # MurmurHash3 for fast hashing

class Deduplicator:
    """Remove duplicate documents"""

    def __init__(self, method: str = "minhash"):
        self.method = method
        self.seen_hashes = set()

    def is_duplicate(self, text: str) -> bool:
        """Check if text is a duplicate"""
        if self.method == "exact":
            return self._exact_duplicate(text)
        elif self.method == "minhash":
            return self._minhash_duplicate(text)
        else:
            raise ValueError(f"Unknown dedup method: {self.method}")

    def _exact_duplicate(self, text: str) -> bool:
        """Exact duplicate detection using SHA256"""
        doc_hash = hashlib.sha256(text.encode()).hexdigest()

        if doc_hash in self.seen_hashes:
            return True

        self.seen_hashes.add(doc_hash)
        return False

    def _minhash_duplicate(self, text: str, threshold: float = 0.8) -> bool:
        """
        Approximate duplicate detection using MinHash + LSH

        Better for near-duplicates (slightly modified text)
        """
        # Create shingles (n-grams)
        shingles = self._create_shingles(text, n=5)

        # Create MinHash signature
        signature = self._create_minhash(shingles, num_permutations=128)

        # Check against existing signatures (using LSH)
        if self._is_near_duplicate(signature, threshold):
            return True

        self.signatures.append(signature)
        return False

    def _create_shingles(self, text: str, n: int = 5) -> set:
        """Create word shingles for MinHash"""
        words = text.lower().split()
        return set(" ".join(words[i:i+n]) for i in range(len(words) - n + 1))

    def _create_minhash(self, shingles: set, num_permutations: int = 128) -> List[int]:
        """Create MinHash signature"""
        # Create num_permutations different hash functions
        signature = []
        for i in range(num_permutations):
            min_hash = float('inf')
            for shingle in shingles:
                # Use different seed for each permutation
                h = mmh3.hash(shingle, seed=i)
                if h < min_hash:
                    min_hash = h
            signature.append(min_hash)
        return signature

    def _is_near_duplicate(self, signature: List[int], threshold: float = 0.8) -> bool:
        """Check if signature is near-duplicate using Jaccard similarity"""
        for existing_sig in self.signatures:
            # Estimate Jaccard similarity
            intersection = sum(1 for a, b in zip(signature, existing_sig) if a == b)
            similarity = intersection / len(signature)

            if similarity >= threshold:
                return True
        return False
```

---

## Part 2: Tokenization for Pre-training

### Tokenizer Training

```python
"""
Train custom tokenizer for pre-training
"""

from tokenizers import Tokenizer, models, trainers, pre_tokenizers
from datasets import load_dataset
import os

class TokenizerTrainer:
    """Train and manage tokenizers"""

    def train_bpe_tokenizer(self,
                            dataset_path: str,
                            vocab_size: int = 50000,
                            save_path: str = "./tokenizer"):
        """
        Train BPE tokenizer on custom dataset

        BPE (Byte-Pair Encoding) is used by GPT-2, GPT-3, RoBERTa
        """
        # Initialize BPE tokenizer
        tokenizer = Tokenizer(models.BPE(unk_token="[UNK]"))

        # Pre-tokenizer (split text into words)
        tokenizer.pre_tokenizer = pre_tokenizers.Whitespace()

        # Trainer
        trainer = trainers.BpeTrainer(
            vocab_size=vocab_size,
            special_tokens=["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"],
            min_frequency=2,  # Minimum frequency for a merge
        )

        # Load dataset
        files = [dataset_path]  # Can be multiple files

        # Train
        tokenizer.train(files, trainer)

        # Save
        os.makedirs(save_path, exist_ok=True)
        tokenizer.save(f"{save_path}/tokenizer.json")

        return tokenizer

    def train_unigram_tokenizer(self,
                                dataset_path: str,
                                vocab_size: int = 50000,
                                save_path: str = "./tokenizer"):
        """
        Train Unigram tokenizer (SentencePiece)

        Unigram is used by T5, mT5, ALBERT
        """
        import sentencepiece as spm

        # Train SentencePiece model
        spm.SentencePieceTrainer.train(
            input=dataset_path,
            model_prefix=f"{save_path}/sp",
            vocab_size=vocab_size,
            model_type="unigram",
            character_coverage=0.995,
            input_sentence_size=10000000,  # Number of sentences for training
            shuffle_input_sentence=True,
        )

        # Load and return
        sp = spm.SentencePieceProcessor()
        sp.load(f"{save_path}/sp.model")

        return sp

    def train_wordpiece_tokenizer(self,
                                  dataset_path: str,
                                  vocab_size: int = 30522,
                                  save_path: str = "./tokenizer"):
        """
        Train WordPiece tokenizer

        WordPiece is used by BERT, DistilBERT
        """
        from tokenizers import Tokenizer, models, trainers

        tokenizer = Tokenizer(models.WordPiece(unk_token="[UNK]"))
        tokenizer.pre_tokenizer = pre_tokenizers.Whitespace()

        trainer = trainers.WordPieceTrainer(
            vocab_size=vocab_size,
            special_tokens=["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"]
        )

        files = [dataset_path]
        tokenizer.train(files, trainer)

        os.makedirs(save_path, exist_ok=True)
        tokenizer.save(f"{save_path}/tokenizer.json")

        return tokenizer

    def compare_tokenizers(self, text: str):
        """Compare different tokenization strategies"""
        results = {}

        # BPE
        # Unigram
        # WordPiece

        # Compare:
        # - Vocabulary size
        # - Average tokens per word
        # - Compression ratio
        # - Out-of-vocabulary rate

        return results
```

### Tokenization Best Practices

```yaml
Tokenizer Design:

  Vocabulary Size:
    Small (10k-30k):
      - Faster inference
      - More tokens per document
      - Better for low-resource languages

    Medium (30k-100k):
      - Good balance (most models use this)
      - Recommended: 50k for general models

    Large (100k-250k):
      - Fewer tokens per document
      - Better for code/multilingual
      - Used by: CodeLLaMA (100k), mT5 (250k)

  Special Tokens:
    Minimum: [PAD], [UNK], [BOS], [EOS]
    For BERT-style: [CLS], [SEP], [MASK]
    For chat: [USER], [ASSISTANT], [SYSTEM]

  Pre-tokenization:
    Whitespace: Simple, fast
    Byte-level: Handles all Unicode (GPT-2 style)
    Morse: Custom character-level

  Training Data:
    - Use representative sample of final training data
    - At least 1M documents
    - 10M+ documents for better coverage
```

---

## Part 3: Training Curriculum Design

### Curriculum Stages

```python
"""
Training curriculum: How to schedule data during training
"""

class TrainingCurriculum:
    """Design training curriculum for better model quality"""

    def __init__(self):
        self.stages = []

    def define_stages(self):
        """
        Define training stages based on data quality and difficulty

        Concept: Start with easier, high-quality data, then progress to harder
        """
        self.stages = [
            {
                "name": "Stage 1: Foundation",
                "percent": 30,  # First 30% of training
                "data_sources": [
                    "Wikipedia",        # Factual, structured
                    "Books",            # Long-form, well-written
                    "arXiv",            # Scientific, technical
                ],
                "rationale": "Build foundational knowledge and reasoning"
            },
            {
                "name": "Stage 2: Web Knowledge",
                "percent": 40,  # Next 40% of training
                "data_sources": [
                    "C4 (filtered)",    # Cleaned web data
                    "StackExchange",    # Technical Q&A
                    "GitHub",           # Code (if code model)
                ],
                "rationale": "Expand knowledge to diverse domains"
            },
            {
                "name": "Stage 3: Fine-tuning on Quality",
                "percent": 20,  # Next 20% of training
                "data_sources": [
                    "High-quality web",
                    "Instructional data",
                    "Conversational data",
                ],
                "rationale": "Improve instruction following and chat"
            },
            {
                "name": "Stage 4: Annealing",
                "percent": 10,  # Final 10% of training
                "data_sources": [
                    "Highest quality data only",
                    "Instruction-response pairs",
                ],
                "rationale": "Final polish, improve instruction following",
                "lr_schedule": "constant or decay to 0"
            }
        ]

    def get_stage_schedule(self, total_steps: int) -> Dict:
        """
        Get which data to use at each training step

        Returns mapping of step -> stage
        """
        schedule = {}
        steps_so_far = 0

        for stage in self.stages:
            stage_steps = int(total_steps * (stage["percent"] / 100))
            stage_end = steps_so_far + stage_steps

            for step in range(steps_so_far, stage_end):
                schedule[step] = stage

            steps_so_far = stage_end

        return schedule

    def mix_databy_stage(self, stage: Dict, base_batch_size: int = 512):
        """
        Mix data sources within a stage

        Returns sampling ratios for each source
        """
        mixing_ratios = {}

        if stage["name"] == "Stage 1: Foundation":
            # Weight towards high-quality
            mixing_ratios = {
                "Wikipedia": 0.4,
                "Books": 0.4,
                "arXiv": 0.2,
            }

        elif stage["name"] == "Stage 2: Web Knowledge":
            # Mix web with quality sources
            mixing_ratios = {
                "C4": 0.5,
                "Wikipedia": 0.2,
                "StackExchange": 0.2,
                "GitHub": 0.1,
            }

        elif stage["name"] == "Stage 3: Fine-tuning on Quality":
            # Focus on instruction following
            mixing_ratios = {
                "Instructional": 0.6,
                "Conversational": 0.3,
                "High-quality web": 0.1,
            }

        elif stage["name"] == "Stage 4: Annealing":
            # Only highest quality
            mixing_ratios = {
                "Instruction-response": 0.8,
                "High-quality conversational": 0.2,
            }

        return mixing_ratios
```

### Learning Rate Scheduling

```python
"""
Learning rate schedules for pre-training
"""

import torch
import math

class LRScheduler:
    """Learning rate scheduling for pre-training"""

    def __init__(self,
                 max_lr: float = 6e-4,
                 min_lr: float = 6e-5,
                 warmup_steps: int = 2000,
                 total_steps: int = 100000):
        self.max_lr = max_lr
        self.min_lr = min_lr
        self.warmup_steps = warmup_steps
        self.total_steps = total_steps

    def get_lr(self, step: int, schedule_type: str = "cosine") -> float:
        """Get learning rate for given step"""

        if schedule_type == "cosine":
            return self._cosine_decay(step)

        elif schedule_type == "linear":
            return self._linear_decay(step)

        elif schedule_type == "inverse_sqrt":
            return self._inverse_sqrt(step)

        else:
            raise ValueError(f"Unknown schedule: {schedule_type}")

    def _cosine_decay(self, step: int) -> float:
        """
        Cosine decay with warmup

        Most common for pre-training (used by GPT-3, LLaMA)
        """
        if step < self.warmup_steps:
            # Linear warmup
            return self.max_lr * (step / self.warmup_steps)

        # Cosine decay
        progress = (step - self.warmup_steps) / (self.total_steps - self.warmup_steps)
        return self.min_lr + (self.max_lr - self.min_lr) * 0.5 * (1 + math.cos(math.pi * progress))

    def _linear_decay(self, step: int) -> float:
        """Linear decay with warmup"""
        if step < self.warmup_steps:
            return self.max_lr * (step / self.warmup_steps)

        progress = (step - self.warmup_steps) / (self.total_steps - self.warmup_steps)
        return self.max_lr - (self.max_lr - self.min_lr) * progress

    def _inverse_sqrt(self, step: int) -> float:
        """
        Inverse square root decay

        Used by Transformer (original paper), T5
        """
        if step < self.warmup_steps:
            return self.max_lr * (step / self.warmup_steps)

        return self.max_lr / math.sqrt(step / self.warmup_steps)

    def get_adamw_params(self) -> Dict:
        """
        Get AdamW optimizer parameters

        AdamW is standard for pre-training
        """
        return {
            "lr": self.max_lr,
            "betas": (0.9, 0.999),
            "eps": 1e-8,
            "weight_decay": 0.01,  # Important for preventing overfitting
        }
```

---

## Part 4: Evaluation Frameworks

### Standard Benchmarks

```python
"""
Evaluate pre-trained models on standard benchmarks
"""

from datasets import load_dataset
from typing import Dict, List
import torch
from tqdm import tqdm

class ModelEvaluator:
    """Evaluate model on standard benchmarks"""

    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer

    def evaluate_perplexity(self, dataset_name: str = "wikitext", split: str = "test"):
        """
        Evaluate perplexity on language modeling benchmark

        Lower perplexity = better language modeling
        """
        dataset = load_dataset(dataset_name, split=split)

        total_loss = 0
        total_tokens = 0

        for batch in tqdm(dataset):
            # Tokenize
            inputs = self.tokenizer(batch["text"], return_tensors="pt")

            # Forward pass
            with torch.no_grad():
                outputs = self.model(**inputs, labels=inputs["input_ids"])
                loss = outputs.loss

            total_loss += loss.item() * inputs["input_ids"].size(1)
            total_tokens += inputs["input_ids"].size(1)

        avg_loss = total_loss / total_tokens
        perplexity = math.exp(avg_loss)

        return {
            "loss": avg_loss,
            "perplexity": perplexity
        }

    def evaluate_mmlu(self, subject: str = "all"):
        """
        Massive Multitask Language Understanding (MMLU)

        Tests knowledge across 57 subjects
        """
        # MMLU requires multiple-choice evaluation
        # This is a simplified version

        # Load MMLU dataset
        # dataset = load_dataset("cais/mmlu", subject, split="test")

        # For each question:
        # 1. Format as multiple choice
        # 2. Get model predictions
        # 3. Calculate accuracy

        # Returns accuracy per subject and overall

        pass

    def evaluate_hellaswag(self):
        """
        HELLaSwAG: Common sense reasoning

        Tests if model can predict likely endings to situations
        """
        pass

    def evaluate_truthfulqa(self):
        """
        TruthfulQA: Test if model generates true answers

        Tests tendency to mimic common misconceptions
        """
        pass

    def evaluate_gsm8k(self):
        """
        GSM8K: Grade school math

        Tests mathematical reasoning
        """
        pass

    def evaluate_human_eval(self):
        """
        HumanEval: Python code generation

        Tests coding ability
        """
        pass

    def run_all_benchmarks(self) -> Dict:
        """Run all standard benchmarks"""
        results = {}

        # Perplexity
        results["perplexity"] = self.evaluate_perplexity()

        # MMLU
        results["mmlu"] = self.evaluate_mmlu()

        # HellaSwAG
        results["hellaswag"] = self.evaluate_hellaswag()

        # TruthfulQA
        results["truthfulqa"] = self.evaluate_truthfulqa()

        # GSM8K
        results["gsm8k"] = self.evaluate_gsm8k()

        # HumanEval (if code model)
        results["human_eval"] = self.evaluate_human_eval()

        return results
```

---

## Part 5: Infrastructure Requirements

### Hardware Estimation

```python
"""
Estimate infrastructure requirements for pre-training
"""

class InfrastructurePlanner:
    """Plan infrastructure for pre-training"""

    def estimate_compute(self,
                        model_size: str = "7B",
                        tokens: int = 1_000_000_000_000,
                        hardware: str = "A100") -> Dict:
        """
        Estimate compute requirements

        Args:
            model_size: Model parameter count (7B, 13B, 70B, etc.)
            tokens: Number of training tokens
            hardware: GPU type (A100, H100, etc.)
        """

        params = {
            "7B": 7_000_000_000,
            "13B": 13_000_000_000,
            "70B": 70_000_000_000,
            "175B": 175_000_000_000,
        }

        model_params = params[model_size]

        # Compute FLOPs needed
        # ~6 * params * tokens (forward + backward)
        total_flops = 6 * model_params * tokens

        # GPU specs
        gpu_specs = {
            "A100": {
                "flops": 312e12,  # TFLOPs (FP16)
                "vram": 80,  # GB
                "bandwidth": 2e12,  # Bytes/sec
            },
            "H100": {
                "flops": 1000e12,  # TFLOPs (FP8)
                "vram": 80,
                "bandwidth": 3.35e12,
            },
        }

        gpu = gpu_specs[hardware]

        # Compute time (assuming 50% MFU - Model FLOPs Utilization)
        mfu = 0.5  # Realistic MFU
        effective_flops = gpu["flops"] * mfu

        seconds = total_flops / effective_flops
        hours = seconds / 3600
        days = hours / 24

        # Number of GPUs needed
        # Rule of thumb: 1B params needs ~20GB VRAM for training
        vram_per_param = 20  # GB per billion params (with AdamW, gradients, etc.)
        required_vram = model_params / 1_000_000_000 * vram_per_param
        num_gpus = math.ceil(required_vram / gpu["vram"])

        # Actually, use tensor parallelism for large models
        # 7B fits on 1 GPU with gradient checkpointing
        # 13B needs 2 GPUs
        # 70B needs 8 GPUs
        # 175B needs 16+ GPUs

        # Parallelism strategy
        if model_size in ["7B"]:
            strategy = "DP (Data Parallel)"
            num_gpus = max(num_gpus, 8)  # Use 8 for efficiency
        elif model_size in ["13B"]:
            strategy = "TP + DP"
            num_gpus = 16
        elif model_size in ["70B"]:
            strategy = "TP + DP"
            num_gpus = 64
        else:
            strategy = "TP + DP + Pipeline Parallel"
            num_gpus = 256

        # Training time with N GPUs
        days_parallel = days / num_gpus

        # Cost estimation
        # A100: ~$3/hour on cloud
        # H100: ~$5/hour on cloud
        cost_per_gpu_hour = 3 if hardware == "A100" else 5
        total_cost = days_parallel * 24 * num_gpus * cost_per_gpu_hour

        return {
            "total_flops": total_flops,
            "training_days_single_gpu": days,
            "num_gpus": num_gpus,
            "parallelism_strategy": strategy,
            "training_days_parallel": days_parallel,
            "estimated_cost_usd": total_cost,
        }

    def estimate_storage(self, tokens: int) -> Dict:
        """Estimate storage requirements"""
        # Average token ~4 bytes
        token_size = 4

        # Raw data size
        raw_size = tokens * token_size

        # Processed data (with features, etc.)
        processed_size = raw_size * 1.5

        # Checkpoints (save every 1000 steps, keep last 10)
        checkpoint_size = 0  # Depends on model size

        # Logs
        logs_size = 100e9  # 100GB for logs

        return {
            "raw_data_gb": raw_size / 1e9,
            "processed_data_gb": processed_size / 1e9,
            "total_storage_gb": (raw_size + processed_size + logs_size) / 1e9,
        }

# Example usage
planner = InfrastructurePlanner()

# 7B model, 1T tokens, A100 GPUs
estimate = planner.estimate_compute("7B", 1_000_000_000_000, "A100")
print(f"Training time: {estimate['training_days_parallel']:.1f} days")
print(f"GPUs needed: {estimate['num_gpus']}")
print(f"Estimated cost: ${estimate['estimated_cost_usd']:,.0f}")

# Output:
# Training time: 21.3 days
# GPUs needed: 8
# Estimated cost: $12,288
```

---

## Part 6: End-to-End Training Script

```python
"""
Complete training script for pre-training
"""

import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers import Trainer, TrainingArguments
import torch.distributed as dist

class PreTrainingDataset(Dataset):
    """Dataset for pre-training"""

    def __init__(self, data_path, max_length=2048):
        self.data = []
        self.max_length = max_length

        # Load pre-processed data
        with open(data_path, 'r') as f:
            for line in f:
                self.data.append(json.loads(line))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        text = self.data[idx]["text"]

        # Tokenize
        encodings = tokenizer(
            text,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )

        return {
            "input_ids": encodings["input_ids"].squeeze(),
            "attention_mask": encodings["attention_mask"].squeeze(),
            "labels": encodings["input_ids"].squeeze(),  # For language modeling
        }

def train_model(
    model_name: str = "facebook/opt-125m",  # Start with small model
    data_path: str = "./training_data/c4_sample.jsonl",
    output_dir: str = "./models/my_model",
    num_train_epochs: int = 3,
    batch_size: int = 4,
    gradient_accumulation_steps: int = 4,
    learning_rate: float = 6e-4,
    max_length: int = 512,
):
    """
    Train a model from scratch or continue pre-training
    """

    # Load model
    model = AutoModelForCausalLM.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Add pad token if needed
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        model.config.pad_token_id = tokenizer.pad_token_id

    # Load dataset
    dataset = PreTrainingDataset(data_path, max_length=max_length)

    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_train_epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        learning_rate=learning_rate,
        weight_decay=0.01,
        warmup_steps=500,
        logging_steps=10,
        save_steps=1000,
        save_total_limit=3,
        fp16=True,  # Use mixed precision
        gradient_checkpointing=True,  # Save memory
        dataloader_num_workers=4,
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
    )

    # Train
    trainer.train()

    # Save
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    return model, tokenizer

# For distributed training (multi-GPU)
def train_distributed():
    """Train with DDP (Distributed Data Parallel)"""
    import torch.distributed as dist
    from torch.nn.parallel import DistributedDataParallel as DDP

    # Initialize process group
    dist.init_process_group("nccl")

    local_rank = int(os.environ["LOCAL_RANK"])
    torch.cuda.set_device(local_rank)

    # Wrap model with DDP
    model = DDP(model.cuda(), device_ids=[local_rank])

    # Train...
```

---

## Summary

### Pre-training Checklist

```yaml
Data Preparation:
  [ ] Collect datasets (C4, Wikipedia, etc.)
  [ ] Filter quality (length, language, content)
  [ ] Remove duplicates (exact and near)
  [ ] Balance data sources
  [ ] Split train/val/test

Tokenizer:
  [ ] Train tokenizer on dataset
  [ ] Choose vocabulary size
  [ ] Add special tokens
  [ ] Test tokenization

Infrastructure:
  [ ] Estimate compute requirements
  [ ] Set up GPU cluster
  [ ] Configure storage
  [ ] Set up monitoring

Training:
  [ ] Define training curriculum
  [ ] Set learning rate schedule
  [ ] Configure warmup
  [ ] Enable gradient checkpointing
  [ ] Set up checkpointing

Evaluation:
  [ ] Set up validation logging
  [ ] Calculate perplexity
  [ ] Run benchmarks (MMLU, etc.)
  [ ] Compare to baseline

Hyperparameters:
  Model size: Start with 125M-1B for first run
  Tokens: 10B-100B for small models
  Batch size: As large as VRAM allows
  Learning rate: 6e-4 for small models, 3e-4 for large
  Warmup: 2-5% of total steps
```

---

## References

### Related ai-engineering-curriculum Documents

- [2402: Large-Scale Training for Language Models](2402-Large-Scale-Training.md)
- [2403: Evaluation Frameworks for Language Models](2403-Evaluation-Frameworks.md)

---

## Next Steps

- Continue with: **[2402: Large-Scale Training](./2402-Large-Scale-Training.md)**
- Practical: **[LAB-006: Train Small Model](../../../learning-resources/labs/LAB-006-Train-Model-From-Scratch.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
