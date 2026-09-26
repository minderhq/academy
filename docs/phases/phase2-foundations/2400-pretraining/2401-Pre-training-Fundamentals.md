---
Document ID: 2401-Pre-training-Fundamentals
Title: "2401: Pre-training Fundamentals"
Phase: 2
Module: 2400
Last Updated: 2026-09-26
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['training', 'pretraining', 'data-curation', 'tokenization']
---

# 2401: Pre-training Fundamentals

---

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Part 1: Data Collection and Curation](#part-1-data-collection-and-curation)
- [Part 2: Data Quality Filtering](#part-2-data-quality-filtering)
- [Part 3: Deduplication](#part-3-deduplication)
- [Part 4: Tokenization](#part-4-tokenization)
- [Part 5: Training Curriculum and Learning Rate Schedules](#part-5-training-curriculum-and-learning-rate-schedules)
- [Part 6: Evaluation and Benchmarks](#part-6-evaluation-and-benchmarks)
- [Part 7: Compute Planning](#part-7-compute-planning)
- [Part 8: The Pre-training Loop, End to End](#part-8-the-pre-training-loop-end-to-end)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Learning Objectives

After completing this lesson, you will be able to:

- Catalogue the major public pre-training corpora (Common Crawl, C4, RedPajama, The Pile, SlimPajama) and reason about their size, quality, and access trade-offs
- Implement a document quality filter that checks length, language, repetition, and blocklists, and order the checks cheapest-first
- Detect exact and near-duplicate documents using MinHash signatures, and explain why near-duplicate removal matters as much as exact removal
- Train a real BPE tokenizer with HuggingFace `tokenizers`, use ByteLevel pre-tokenization, and verify encode/decode round-trips
- Schedule a training curriculum (foundation, web knowledge, annealing) and a warmup-then-decay learning rate schedule with exact LR values
- Measure perplexity on held-out text with a working evaluator, and articulate what perplexity does and does not tell you
- Estimate a pre-training run's FLOPs, GPU-hours, wall-clock days, and dollar cost from the 6·N·D rule
- Run the complete pre-training loop end to end on a tiny corpus in PyTorch, in seconds, on a CPU

## Abstract

Pre-training is where a language model earns its capabilities. Before any
instruction tuning or fine-tuning, the model learns the structure of language
from raw text by doing one thing at extraordinary scale: predicting the next
token, over and over, across trillions of them. Everything that makes the
final model good or bad is decided here — which text it saw, how clean that
text was, how the vocabulary was built, how the run was scheduled, and how
much compute it received.

This lesson walks the full pipeline in order. You will build a data catalog
and a collector, filter and deduplicate documents, train a real BPE tokenizer,
schedule a curriculum and learning rate, evaluate with perplexity, plan the
compute budget from first principles, and finally run the entire pre-training
loop end to end on a corpus small enough to train in seconds. Every code block
runs offline — the production-scale counterparts (multi-terabyte crawls,
hundreds of GPUs) are module [2402: Large-Scale Training for Language Models](./2402-Large-Scale-Training.md)'s subject, and the structure you build here is
identical.

**What you'll learn:**

- Where pre-training text comes from, and how to compare the major public corpora
- The cleaning funnel: quality filters, exact dedup, near-duplicate removal
- How a BPE tokenizer is actually trained, and why its vocabulary is frozen before step zero
- Curriculum and learning-rate schedules that keep large runs stable
- What perplexity measures on a real evaluator, and which benchmarks track pre-training progress
- How to turn 6·N·D FLOPs into GPU-hours, wall-clock days, and dollars
- The complete training loop in code, seeded and deterministic

## Part 1: Data Collection and Curation

A pre-training run is only as good as its corpus. The ecosystem has converged
on a small set of public sources, each with a different size/quality/access
profile: web crawls are enormous but noisy, curated corpora are smaller but
clean, and specialized sources (code, science, encyclopedias) inject
capability-specific knowledge. Every serious training mix combines several of
them.

### The pre-training data landscape

The catalog below is the vocabulary you need for any conversation about
pre-training data. Notice the trade-offs in each entry: the biggest source
needs the heaviest filtering, and the cleanest sources are the smallest.

```python
datasets = {
    "Common Crawl": {
        "size": "100+ TB (monthly dumps)",
        "quality": "Mixed (needs heavy filtering)",
        "access": "https://commoncrawl.org/",
        "use_case": "Base data for most models",
    },
    "C4 (Colossal Clean Crawled Corpus)": {
        "size": "750GB cleaned",
        "quality": "High (heavily filtered)",
        "access": "TensorFlow Datasets",
        "use_case": "Cleaned web data",
    },
    "RedPajama": {
        "size": "1.2T tokens",
        "quality": "High (LLaMA reproduction)",
        "access": "https://together.ai/blog/redpajama",
        "use_case": "Open-source LLaMA reproduction",
    },
    "The Pile": {
        "size": "825GB, 800GB+ text",
        "quality": "Very High (curated sources)",
        "access": "https://pile.eleuther.ai/",
        "use_case": "Diverse, high-quality training",
    },
    "SlimPajama": {
        "size": "627B tokens",
        "quality": "High (cleaned RedPajama)",
        "access": "HuggingFace",
        "use_case": "Cleaner RedPajama",
    },
    "GitHub": {
        "size": "1TB+ code",
        "quality": "Mixed (needs deduplication)",
        "access": "Google BigQuery",
        "use_case": "Code models (StarCoder, CodeLLaMA)",
    },
    "Wikipedia": {
        "size": "20GB compressed",
        "quality": "Very High",
        "access": "https://dumps.wikimedia.org/",
        "use_case": "Factual knowledge",
    },
    "arXiv": {
        "size": "10GB+ LaTeX",
        "quality": "High (scientific)",
        "access": "https://arxiv.org/",
        "use_case": "Scientific reasoning",
    },
    "Books": {
        "size": "100GB+ (varying sources)",
        "quality": "Very High",
        "access": "BookCorpus, Project Gutenberg",
        "use_case": "Long-form reasoning",
    },
    "StackExchange": {
        "size": "50GB+ Q&A",
        "quality": "High (curated)",
        "access": "https://archive.org/",
        "use_case": "Technical Q&A, reasoning",
    },
}

print(f"{len(datasets)} major pre-training sources catalogued")
```

**Output:**

```text
10 major pre-training sources catalogued
```

### A collector for every major source

The collector below is the real API surface for pulling each source. Read it
carefully: **calling any method performs a network download** — tens of
gigabytes for Wikipedia, tens of terabytes for a Common Crawl snapshot — so
the block only *defines* the class and prints nothing. This is deliberate:
you should know exactly what each source's collection path looks like before
you ever run one.

```python
"""
Real data-collection surface for pre-training.

Every method here performs a network download when called - none of
them run in this lesson. The class is importable offline so you can
read the exact API surface each source exposes.
"""

import json
import os
from typing import List


class DataCollector:
    """Collect raw training data from public sources."""

    def __init__(self, output_dir: str = "./training_data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def download_common_crawl(self, snapshot: str = "CC-MAIN-2023-14"):
        """Download one Common Crawl snapshot (~30-80TB compressed)."""
        base_url = f"https://data.commoncrawl.org/crawl-data/{snapshot}/"
        warc_paths = self._get_warc_list(snapshot)
        for warc_path in warc_paths[:10]:  # start with a small subset
            self._download_and_extract_warc(warc_path)
        return base_url

    def download_c4_via_huggingface(self):
        """Stream a small C4 sample through HuggingFace datasets."""
        from datasets import load_dataset

        dataset = load_dataset("allenai/c4", "en", split="train", streaming=True)
        out = os.path.join(self.output_dir, "c4_sample.jsonl")
        with open(out, "w") as f:
            for i, example in enumerate(dataset):
                if i >= 10000:
                    break
                f.write(json.dumps(example) + "\n")
        return out

    def download_slimpajama(self):
        """Stream a small SlimPajama sample (cleaned RedPajama)."""
        from datasets import load_dataset

        dataset = load_dataset("cerebras/SlimPajama-627B", split="train", streaming=True)
        out = os.path.join(self.output_dir, "slimpajama_sample.jsonl")
        with open(out, "w") as f:
            for i, example in enumerate(dataset):
                if i >= 10000:
                    break
                f.write(json.dumps(example) + "\n")
        return out

    def download_wikipedia(self, language: str = "en"):
        """Download a Wikipedia dump through HuggingFace datasets."""
        from datasets import load_dataset

        dataset = load_dataset("wikimedia/wikipedia", f"20231101.{language}", split="train")
        out = os.path.join(self.output_dir, "wikipedia.jsonl")
        with open(out, "w") as f:
            for example in dataset:
                f.write(json.dumps({
                    "id": example["id"],
                    "title": example["title"],
                    "text": example["text"],
                }) + "\n")
        return out

    def download_arxiv(self):
        """Download scientific_papers/arxiv through HuggingFace datasets."""
        from datasets import load_dataset

        dataset = load_dataset("scientific_papers", "arxiv", split="train")
        out = os.path.join(self.output_dir, "arxiv.jsonl")
        with open(out, "w") as f:
            for i, example in enumerate(dataset):
                if i >= 1000:
                    break
                f.write(json.dumps({
                    "abstract": example["abstract"],
                    "article": example["article"],
                }) + "\n")
        return out

    def stackexchange_dump_urls(self, sites: List[str] = None) -> List[str]:
        """Internet Archive 7z dump URLs for StackExchange sites."""
        if sites is None:
            sites = ["stackoverflow", "superuser", "math"]
        return [f"https://archive.org/stackexchange/{s}.stackexchange.com.7z" for s in sites]

    def _get_warc_list(self, snapshot: str) -> List[str]:
        """Simplified: a real collector parses the Common Crawl index."""
        return [f"crawl-data/{snapshot}/segments/{i}.warc.gz" for i in range(10)]

    def _download_and_extract_warc(self, warc_path: str):
        """Requires the warcio library and multi-TB scratch space."""
        raise NotImplementedError("network + warcio required - see module docstring")
```

This block has no output — it only defines the collector. What to notice:

- Each source has a *different* collection mechanism: Common Crawl is raw WARC
  files from `data.commoncrawl.org`, most others stream through HuggingFace
  `datasets`, and StackExchange is 7z archives on archive.org.
- The network imports (`datasets`) are deferred *inside* the methods. That
  keeps the module importable on a machine with no internet — the same trick
  production pipelines use to keep collection workers and training workers
  separable.
- `download_common_crawl` takes a snapshot name in the official
  `CC-MAIN-YYYY-WW` format; the WARC extraction path raises
  `NotImplementedError` because real WARC handling needs the `warcio` library
  and terabytes of scratch space.

## Part 2: Data Quality Filtering

Raw crawls are full of boilerplate navigation, spam, non-text pages, and
machine-generated filler. The standard response is a filter funnel: a set of
cheap, interpretable checks, each of which can reject a document. Production
pipelines run dozens of such heuristics (perplexity-pruning with a small LM,
NSFW classifiers, toxicity scorers); the four checks below — length,
language, repetition, blocklist — are the classic core, and they already
remove most of the junk.

The checks are ordered cheapest-first so that obviously-bad documents exit
before the expensive checks run. The language check uses a stopword-ratio
heuristic (English text is rich in words like "the", "of", "and"); production
systems typically use fastText or a dedicated language-ID model instead, but
the shape of the check is the same.

```python
"""
Offline-safe data quality filtering.

langdetect-style language identification is replaced here by a
deterministic stopword-ratio heuristic so the whole pipeline runs
anywhere - the idea (score text, keep it only if every check passes)
is the same one production filters implement.
"""

from typing import Dict

ENGLISH_STOPWORDS = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "it",
    "for", "not", "on", "with", "as", "do", "at", "this", "but", "by", "is",
}


class DataFilter:
    """Filter and clean training documents."""

    def __init__(self):
        self.bad_words = {"spam", "porn", "casino"}  # tiny illustrative blocklist
        self.min_words = 20
        self.max_words = 20480
        self.min_stopword_ratio = 0.15
        self.max_repetition_ratio = 0.7  # unique/total words must exceed 30%

    def reject_reason(self, doc: Dict):
        """Return the name of the first failed check, or None if kept."""
        text = doc.get("text", "")
        words = text.lower().split()

        if not (self.min_words <= len(words) <= self.max_words):
            return "length"

        tokens = [w.strip(".,!?;:'\"()") for w in words]
        stop_ratio = sum(t in ENGLISH_STOPWORDS for t in tokens) / len(words)
        if stop_ratio < self.min_stopword_ratio:
            return "language"

        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 1 - self.max_repetition_ratio:
            return "repetition"

        if set(words) & self.bad_words:
            return "blocklist"

        return None


demo_docs = [
    {"id": "good", "text": (
        "Pre-training teaches a model the structure of language by asking it "
        "to predict the next word in a sequence of tokens. The model sees "
        "billions of words, and every one of them contributes a gradient."
    )},
    {"id": "short", "text": "too short to learn from"},
    {"id": "repetitive", "text": " ".join(["the model repeats the same words over and over"] * 8)},
    {"id": "turkish", "text": (
        "Bu cumle Turkce yazilmistir ve Ingilizce durak sozcukleri icermez. "
        "Ingilizce filtre durak sozcukleri oranini olcer ve bu oran cok dusuk "
        "kalirsa dokuman dil kontrolunden gecemez, boylece reddedilir."
    )},
]

flt = DataFilter()
for doc in demo_docs:
    reason = flt.reject_reason(doc)
    verdict = "kept" if reason is None else f"rejected ({reason})"
    print(f"doc {doc['id']}: {verdict}")
```

**Output:**

```text
doc good: kept
doc short: rejected (length)
doc repetitive: rejected (repetition)
doc turkish: rejected (language)
```

What to notice:

- Each demo document fails a *different* check, which is how you should test a
  filter: one clean document, and one per rule.
- `reject_reason` returns the *first* failing check, so the four rules are
  evaluated cheapest-first: length is O(1), language is one pass, repetition
  needs a set, and the blocklist intersect is last.
- The thresholds are decisions, not laws: `min_words = 20` keeps short
  questions alive, while a code-heavy corpus would raise
  `min_stopword_ratio`'s importance way down (code has few stopwords — a
  nice example of a heuristic that must be re-tuned per domain).

## Part 3: Deduplication

Web corpora contain the same page many times: mirrors, scrapes, pagination,
and boilerplate-heavy templates. Training on duplicates wastes compute and —
worse — lets memorized text leak into outputs. Two passes handle it:

1. **Exact dedup** — hash each document; identical hashes are duplicates.
   Cheap, catches byte-identical copies.
2. **Near-duplicate detection** — documents that differ by a few words have
   different hashes but nearly identical content. The standard tool is
   **MinHash**: convert each document into a set of word *shingles*, compute a
   small signature, and compare signatures. Comparing two MinHash signatures
   position-wise is an unbiased estimator of the Jaccard similarity of the
   underlying shingle sets.

Real pipelines hash with MurmurHash3 and shard signatures into an LSH
(banding) index so lookups are sub-linear; this version uses stdlib `blake2b`
with a per-permutation key so the identical math runs with zero dependencies,
and scans stored signatures directly — fine for the toy scale here.

```python
"""
Exact + near duplicate detection, offline.

Real pipelines hash with MurmurHash3 and shard signatures into an LSH
index; this version uses stdlib blake2b with a per-permutation key so
the same math runs with zero dependencies.
"""

import hashlib
from typing import List


def keyed_hash(seed: int, text: str) -> int:
    """Deterministic 64-bit hash of text under a permutation seed."""
    return int.from_bytes(
        hashlib.blake2b(text.encode(), key=bytes([seed % 256]), digest_size=8).digest(),
        "big",
    )


class Deduplicator:
    """Remove duplicate documents from training data."""

    def __init__(self, method: str = "minhash", num_permutations: int = 16):
        if method not in ("exact", "minhash"):
            raise ValueError(f"Unknown dedup method: {method}")
        self.method = method
        self.num_permutations = num_permutations
        self.seen_hashes = set()
        self.signatures = []  # signatures of every document kept so far

    def is_duplicate(self, text: str) -> bool:
        if self.method == "exact":
            return self._exact_duplicate(text)
        return self._minhash_duplicate(text)

    def _exact_duplicate(self, text: str) -> bool:
        doc_hash = hashlib.sha256(text.encode()).hexdigest()
        if doc_hash in self.seen_hashes:
            return True
        self.seen_hashes.add(doc_hash)
        return False

    def _minhash_duplicate(self, text: str, threshold: float = 0.8) -> bool:
        """Approximate detection of near-duplicates via MinHash signatures.

        Comparing signatures position-wise estimates Jaccard similarity;
        production systems band the signature into an LSH index instead of
        scanning every stored signature.
        """
        shingles = self._create_shingles(text, n=3)
        if not shingles:
            return False  # too short to fingerprint; defer to exact stage
        signature = self._create_minhash(shingles)
        for existing_sig in self.signatures:
            matches = sum(1 for a, b in zip(signature, existing_sig) if a == b)
            similarity = matches / len(signature)
            if similarity >= threshold:
                return True
        self.signatures.append(signature)
        return False

    def _create_shingles(self, text: str, n: int = 3) -> set:
        words = text.lower().split()
        return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}

    def _create_minhash(self, shingles: set) -> List[int]:
        return [min(keyed_hash(i, s) for s in shingles) for i in range(self.num_permutations)]


docs = [
    ("original", "pre training teaches a model to predict the next word from raw text using cross entropy loss over a vocabulary of subword tokens learned by byte pair encoding"),
    ("exact copy", "pre training teaches a model to predict the next word from raw text using cross entropy loss over a vocabulary of subword tokens learned by byte pair encoding"),
    ("near copy", "pre training teaches a model to predict the next token from raw text using cross entropy loss over a vocabulary of subword tokens learned by byte pair encoding"),
    ("unrelated", "the curriculum orders data from clean encyclopedic prose toward noisier web crawls across the training run"),
    ("unrelated again", "the curriculum orders data from clean encyclopedic prose toward noisier web crawls across the training run"),
    ("unique", "evaluation tracks perplexity on a held out validation split every few hundred steps"),
]

dedup = Deduplicator(method="minhash")
for name, text in docs:
    print(f"{name}: duplicate={dedup.is_duplicate(text)}")
```

**Output:**

```text
original: duplicate=False
exact copy: duplicate=True
near copy: duplicate=True
unrelated: duplicate=False
unrelated again: duplicate=True
unique: duplicate=False
```

What to notice:

- The near copy differs from the original by **one word** (`word` → `token`),
  which changes its exact hash but leaves most 3-word shingles intact — and
  the MinHash signature similarity stays above the 0.8 threshold, so it is
  caught. This is precisely the case exact dedup misses.
- `num_permutations = 16` is a toy value. Production MinHash uses 128-200
  permutations (tighter similarity estimates) plus LSH banding to avoid the
  O(N²) scan you see in `_minhash_duplicate`.
- The `signatures` list grows only when a document is *kept* — the dedup
  reservoir. Every kept document's signature becomes the comparison set for
  every future document.

## Part 4: Tokenization

The tokenizer converts text into the integer token ids the model actually
consumes — and it is trained *before* the model and never trained again. Every
capability and every cost in the final system flows through this frozen
component: a word the tokenizer cannot represent cannot be learned, and every
extra token per document is extra compute per step.

### Training a real BPE tokenizer

The block below trains a genuine BPE tokenizer with HuggingFace `tokenizers`
— the same library, model class, and trainer GPT-2-style pipelines use — on a
tiny corpus so it finishes in milliseconds. Byte pair encoding starts from
single characters and repeatedly merges the most frequent adjacent pair, so
frequent words become single tokens while rare words fall back to subword
pieces.

ByteLevel pre-tokenization is GPT-2's approach: text is mapped to printable
byte characters, so *any* input (emoji, CJK, code) is representable, and
decoding is exactly reversible — which is why the round-trip check below is
the tokenizer's own unit test.

```python
"""
Train a real BPE tokenizer with HuggingFace tokenizers - the same
library, model class, and trainer GPT-2-style pipelines use, at toy
scale so it finishes in milliseconds.
"""

import os
import tempfile

from tokenizers import Tokenizer, models, trainers, pre_tokenizers, decoders

corpus_text = """pre training starts from raw text and a tokenizer
the tokenizer turns text into integer token ids
byte pair encoding starts from characters and merges frequent pairs
frequent pairs of characters become subword tokens
subword tokens keep the vocabulary small while covering every word
a small vocabulary means more tokens per document
a large vocabulary means fewer tokens per document
the tokenizer is trained before the model and is never trained again
tokenization quality limits what the model can learn from text
every pre training run fixes its vocabulary before step zero
models learn the distribution of tokens the tokenizer produces
rare words split into subword tokens instead of becoming unk
"""

tmpdir = tempfile.mkdtemp(prefix="bpe_")
corpus_path = os.path.join(tmpdir, "corpus.txt")
with open(corpus_path, "w", encoding="utf-8") as f:
    f.write(corpus_text)

# ByteLevel is GPT-2's approach: text maps to printable byte chars, so ANY
# input (emoji, CJK, code) is representable and decoding is exactly reversible.
tokenizer = Tokenizer(models.BPE(unk_token="[UNK]"))
tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
tokenizer.decoder = decoders.ByteLevel()

trainer = trainers.BpeTrainer(
    vocab_size=120,
    special_tokens=["[PAD]", "[UNK]", "[BOS]", "[EOS]"],
    min_frequency=2,
)
tokenizer.train([corpus_path], trainer)

sample = "the tokenizer turns text into token ids"
ids = tokenizer.encode(sample).ids
print(f"vocab size: {tokenizer.get_vocab_size()}")
print(f"in-vocab sample: {len(sample.split())} words -> {len(ids)} bpe tokens")
print(f"round trip ok: {tokenizer.decode(ids) == sample}")

oov = tokenizer.encode("the pretrainingly tokenizeurs")
print(f"oov ids: {oov.ids}")
print(f"oov decoded: {tokenizer.decode(oov.ids)}")
```

**Output:**

```text
vocab size: 120
in-vocab sample: 7 words -> 15 bpe tokens
round trip ok: True
oov ids: [117, 44, 63, 22, 64, 58, 14, 27, 74, 8, 23, 20, 21]
oov decoded: the pretrainingly tokenizeurs
```

What to notice:

- The trained vocabulary is exactly the 120 tokens requested — BPE fills to
  the budget with merged pairs, then stops. On a toy corpus 15 tokens encode 7
  words (real tokenizers on real corpora compress far better, see the sizing
  table below); the mechanics are identical either way.
- `round trip ok: True` is the property that makes ByteLevel special:
  `decode(encode(x)) == x` for **any** string, byte-exact. Verify it on your
  own tokenizer before trusting it with training data.
- The made-up words `pretrainingly` and `tokenizeurs` are not in the corpus —
  BPE still encodes them by falling back to subword pieces it *has* seen
  (note how `tokenizeurs` reuses the pieces of `tokenizer`). The decode
  reconstructs them perfectly. With a too-small vocabulary some inputs fall
  all the way back to `[UNK]`, which is pure information loss.

### Vocabulary sizing

Vocabulary size is a budget decision made once, before step zero. It trades
sequence length against parameter count:

```yaml
# Vocabulary size: a budget decision made once, before step zero
Small (8k-32k):
  strengths:
    - More embedding budget per token for a fixed parameter count
    - Smaller LM head (vocab x hidden is a big matrix)
  weaknesses:
    - More tokens per document -> longer sequences, more compute per word
  examples: [Llama 2 (32k), BERT (30k)]
Large (100k-250k):
  strengths:
    - Fewer tokens per document
    - Better coverage of code and multiple languages
  weaknesses:
    - Bigger embedding tables and LM head
  examples: [GPT-3.5/GPT-4 cl100k_base (100,256), mT5 (250k)]
```

The tokenizer also couples to the model architecturally: the LM head projects
`hidden -> vocab`, so doubling the vocabulary adds a vocab-sized slice of
parameters. Deeper treatment — SentencePiece, tiktoken, compression-ratio
benchmarking — lives in
[3202: Tokenizer Sciences - BPE, SentencePiece, and Tiktoken](../../phase3-transformers/3200-embeddings/3202-Tokenizer-Sciences.md).

## Part 5: Training Curriculum and Learning Rate Schedules

Two schedules shape every pre-training run: *what data the model sees* at each
point (the curriculum) and *how fast it is allowed to learn* (the learning
rate). Both are defined as functions of step number, so the same definitions
scale from a 1,000-step smoke test to a 500,000-step production run.

### Curriculum: ordering data across the run

The standard curriculum has three phases: clean, well-structured prose first
(the model learns language basics from reliable signal), broad web coverage in
the middle (breadth and volume), and the highest-quality mix at the end as the
learning rate decays (the "annealing" phase leaves the strongest final
impressions).

```python
"""
Training curriculum: schedule data quality across the run.
Stage boundaries come from percentages of total steps, so the same
definition works for a 1k-step smoke test and a 500k-step run.
"""

from typing import Dict, List


class TrainingCurriculum:
    """Design training curriculum for better model quality."""

    def __init__(self):
        self.stages: List[Dict] = [
            {
                "name": "Foundation",
                "percent": 30,  # first 30% of steps
                "data_sources": ["Wikipedia", "Books", "arXiv"],
                "rationale": "clean, factual, well-structured prose first",
            },
            {
                "name": "Web knowledge",
                "percent": 40,  # next 40%
                "data_sources": ["C4 (filtered)", "StackExchange", "GitHub"],
                "rationale": "broaden coverage to diverse, noisier domains",
            },
            {
                "name": "Annealing",
                "percent": 30,  # final 30%
                "data_sources": ["Highest-quality mix"],
                "rationale": "highest quality data as the LR decays to 0",
            },
        ]

    def stage_bounds(self, total_steps: int) -> Dict[str, tuple]:
        """Map each stage name to its [start, end) step range."""
        bounds = {}
        start = 0
        for stage in self.stages:
            end = start + int(total_steps * stage["percent"] / 100)
            bounds[stage["name"]] = (start, end)
            start = end
        return bounds

    def stage_for_step(self, step: int, total_steps: int) -> str:
        for name, (start, end) in self.stage_bounds(total_steps).items():
            if start <= step < end:
                return name
        return self.stages[-1]["name"]

    def mix_ratios(self, stage_name: str) -> Dict[str, float]:
        """Sampling weights for the sources inside one stage."""
        ratios = {
            "Foundation": {"Wikipedia": 0.4, "Books": 0.4, "arXiv": 0.2},
            "Web knowledge": {"C4": 0.5, "Wikipedia": 0.2, "StackExchange": 0.2, "GitHub": 0.1},
            "Annealing": {"Highest-quality mix": 1.0},
        }
        return ratios[stage_name]


curriculum = TrainingCurriculum()
for name, (start, end) in curriculum.stage_bounds(1000).items():
    print(f"{name}: steps {start}-{end}")
print(f"step 250 is in: {curriculum.stage_for_step(250, 1000)}")
print(f"Foundation mix: {curriculum.mix_ratios('Foundation')}")
print(f"Web mix: {curriculum.mix_ratios('Web knowledge')}")
```

**Output:**

```text
Foundation: steps 0-300
Web knowledge: steps 300-700
Annealing: steps 700-1000
step 250 is in: Foundation
Foundation mix: {'Wikipedia': 0.4, 'Books': 0.4, 'arXiv': 0.2}
Web mix: {'C4': 0.5, 'Wikipedia': 0.2, 'StackExchange': 0.2, 'GitHub': 0.1}
```

What to notice:

- Stages are stored as *percentages*, not step counts. The bounds for 1,000
  steps and 500,000 steps come from the same code path, and the annealing
  boundary lands exactly at the point the learning rate is smallest.
- Stage boundaries are half-open ranges `[start, end)` — `stage_for_step(300,
  1000)` returns `Web knowledge`, not Foundation. Off-by-one stage boundaries
  are a classic silent bug in real run launchers.

### Learning rate: warmup then decay

Every LLM learning rate schedule has the same skeleton: a short **linear
warmup** (the first ~2% of steps) while Adam's second-moment estimates
stabilize, followed by a **decay** phase that anneals the LR toward a small
floor. The decay shape is a choice — cosine is the LLM default, linear is the
simplest, and inverse-sqrt never needs to know the total step count (the
classic choice for transformer machine-translation training).

```python
"""
Learning rate schedules for pre-training: linear warmup, then decay.
Cosine is the default for LLMs; linear and inverse-sqrt are the
classical alternatives.
"""

import math
from typing import Dict


class LRScheduler:
    def __init__(self,
                 max_lr: float = 6e-4,
                 min_lr: float = 6e-5,
                 warmup_steps: int = 2000,
                 total_steps: int = 100_000):
        self.max_lr = max_lr
        self.min_lr = min_lr
        self.warmup_steps = warmup_steps
        self.total_steps = total_steps

    def get_lr(self, step: int, schedule_type: str = "cosine") -> float:
        if step < self.warmup_steps:  # every schedule starts with linear warmup
            return self.max_lr * step / self.warmup_steps
        if schedule_type == "cosine":
            return self._cosine_decay(step)
        if schedule_type == "linear":
            return self._linear_decay(step)
        if schedule_type == "inverse_sqrt":
            return self._inverse_sqrt(step)
        raise ValueError(f"Unknown schedule: {schedule_type}")

    def _cosine_decay(self, step: int) -> float:
        progress = (step - self.warmup_steps) / (self.total_steps - self.warmup_steps)
        return self.min_lr + (self.max_lr - self.min_lr) * 0.5 * (1 + math.cos(math.pi * progress))

    def _linear_decay(self, step: int) -> float:
        progress = (step - self.warmup_steps) / (self.total_steps - self.warmup_steps)
        return self.max_lr - (self.max_lr - self.min_lr) * progress

    def _inverse_sqrt(self, step: int) -> float:
        return self.max_lr / math.sqrt(step / self.warmup_steps)

    def get_adamw_params(self) -> Dict:
        """AdamW is the standard pre-training optimizer."""
        return {
            "lr": self.max_lr,
            "betas": (0.9, 0.999),
            "eps": 1e-8,
            "weight_decay": 0.01,
        }


sched = LRScheduler()
probe_steps = [1000, 2000, 25_000, 50_000, 99_999]
for name in ("cosine", "linear", "inverse_sqrt"):
    values = ", ".join(f"{sched.get_lr(s, name):.2e}" for s in probe_steps)
    print(f"{name:>12}: {values}")
```

**Output:**

```text
      cosine: 3.00e-04, 6.00e-04, 5.30e-04, 3.39e-04, 6.00e-05
      linear: 3.00e-04, 6.00e-04, 4.73e-04, 3.36e-04, 6.00e-05
inverse_sqrt: 3.00e-04, 6.00e-04, 1.70e-04, 1.20e-04, 8.49e-05
```

What to notice:

- The columns are steps `1000` (mid-warmup), `2000` (warmup ends — every
  schedule peaks at `max_lr = 6e-4`), then `25_000`, `50_000`, and `99_999`
  (near the end).
- Warmup is **shared** by all three schedules — only the decay differs. At
  step 25,000 cosine has barely begun to fall (5.30e-04) while inverse-sqrt
  is already down to 1.70e-04; inverse-sqrt decays fastest early and never
  reaches a floor.
- Cosine at step 99,999 is `6.00e-05` — exactly `min_lr`, because the cosine
  formula terminates at the floor rather than below it. Real launchers clamp
  or floor the schedule for this reason.

## Part 6: Evaluation and Benchmarks

A pre-training run is evaluated continuously: loss on the training stream,
perplexity on a held-out validation split, and periodically a battery of
downstream benchmarks on saved checkpoints. The first two are cheap and run
every few hundred steps; benchmarks are expensive and run on checkpoints.

### Perplexity

Perplexity is the metric every pre-training run tracks. It is defined as
`exp(average cross-entropy per token)` — a model that assigns probability 1/V
to everything sits at perplexity V, so lower is better and the scale is
interpretable at a glance. The evaluator below fits a character-level bigram
model with add-k smoothing so the whole thing runs offline; real runs compute
the identical quantity with the actual network over a held-out token split.

```python
"""
Perplexity: the metric every pre-training run tracks.

Perplexity = exp(average cross-entropy per token). A model that
assigns probability 1/V to everything sits at perplexity V, so lower
is better and the scale is interpretable at a glance.

This evaluator fits a character-level bigram model (add-k smoothed)
so the whole thing runs offline - real runs compute the identical
quantity with the actual network over a held-out token split.
"""

import math


class PerplexityEvaluator:
    def __init__(self, k: float = 0.01):
        self.k = k  # add-k smoothing: no unseen bigram gets probability 0
        self.transitions = {}
        self.totals = {}

    def fit(self, text: str) -> "PerplexityEvaluator":
        for prev, nxt in zip(text, text[1:]):
            self.transitions.setdefault(prev, {})
            self.transitions[prev][nxt] = self.transitions[prev].get(nxt, 0) + 1
            self.totals[prev] = self.totals.get(prev, 0) + 1
        return self

    def perplexity(self, text: str) -> float:
        vocab = set(self.totals) | set(text)
        vocab_size = len(vocab)
        log_lik = 0.0
        n = 0
        for prev, nxt in zip(text, text[1:]):
            count = self.transitions.get(prev, {}).get(nxt, 0)
            prob = (count + self.k) / (self.totals.get(prev, 0) + self.k * vocab_size)
            log_lik += math.log(prob)
            n += 1
        avg_ce = -log_lik / n  # per-character cross-entropy, token-weighted
        return math.exp(avg_ce)


train_text = (
    "the model learns to predict the next character in a stream of text. "
    "perplexity measures how surprised the model is by held-out text. "
    "lower perplexity means the model predicts the text better. "
)
held_out = "the model predicts the next character of held-out text."
garbage = "zxqkj wvfpn bmgtl zxqkj pvdsn wvfpn."

ev = PerplexityEvaluator().fit(train_text)
print(f"held-out perplexity: {ev.perplexity(held_out):.1f}")
print(f"garbage perplexity:  {ev.perplexity(garbage):.1f}")
```

**Output:**

```text
held-out perplexity: 4.7
garbage perplexity:  113.4
```

What to notice:

- Same alphabet, wildly different perplexity: 4.7 for held-out English-style
  text vs 113.4 for keyboard noise — 24× more "surprise" per character. This
  contrast *is* the metric: perplexity measures how well the model's learned
  distribution matches the text in front of it.
- The averaging is **token-weighted**: `avg_ce` divides by the number of
  characters N. When real runs average eval loss across batches, they must
  weight by tokens, not by batch count — a naive mean over batches silently
  over-weights a short final batch.
- Add-k smoothing (`k = 0.01`) guarantees no unseen bigram gets probability
  zero — without it, a single novel character pair would send perplexity to
  infinity.

### Benchmark suites

Perplexity does not tell you what the model can *do* — a model can lower its
validation perplexity while getting worse at arithmetic. That is why
pre-training runs periodically evaluate checkpoints on downstream benchmarks:

| Benchmark | What it measures | Metric |
|---|---|---|
| MMLU | Knowledge across 57 subjects | Accuracy |
| HellaSwag | Commonsense sentence completion | Accuracy |
| TruthfulQA | Resistance to common misconceptions | % truthful answers |
| GSM8K | Grade-school math word problems | Exact match |
| HumanEval | Python code generation | pass@1 |

These are the headline names you will see in every pre-training paper and
checkpoint card. How to run them properly — harness setup, few-shot prompting,
contamination checks — is the entire subject of module
[2403: Evaluation Frameworks for Language Models](./2403-Evaluation-Frameworks.md).

## Part 7: Compute Planning

Before a single GPU is rented, someone computes whether the run is affordable.
The estimate comes from one rule: **training cost ≈ 6·N·D FLOPs**, where N is
parameter count and D is the token budget — 2 FLOPs per parameter per token
for the forward pass, 4 for the backward pass. Divide by what a GPU actually
delivers (peak throughput × **MFU**, model FLOPs utilization — 0.4-0.55 is
realistic for well-optimized large runs) and everything else follows.

```python
"""
Estimate pre-training compute from the 6*N*D rule: training cost in
FLOPs is roughly 6x parameters x tokens (2 per forward pass, 4 per
backward pass). Everything else - GPU-hours, wall-clock, dollars -
follows from that one number.
"""

import math
from typing import Dict


class InfrastructurePlanner:
    """Plan infrastructure for a pre-training run."""

    # dense BF16 tensor-core throughput and rough cloud pricing
    GPUS = {
        "A100": {"tflops": 312, "usd_per_hour": 3.0},
        "H100": {"tflops": 495, "usd_per_hour": 5.0},  # ~990 with sparsity
    }

    def estimate_compute(self, params: int, tokens: int, gpus: int,
                         hardware: str = "A100", mfu: float = 0.5) -> Dict:
        """
        Args:
            params: model parameter count
            tokens: training token budget
            gpus: fleet size
            mfu: model FLOPs utilization (0.4-0.55 is realistic)
        """
        if hardware not in self.GPUS:
            raise ValueError(f"Unknown GPU: {hardware}")
        spec = self.GPUS[hardware]

        total_flops = 6 * params * tokens
        effective_flops = spec["tflops"] * 1e12 * mfu
        gpu_hours = total_flops / effective_flops / 3600
        wall_days = gpu_hours / gpus / 24
        cost_usd = gpu_hours * spec["usd_per_hour"]
        return {
            "total_flops": total_flops,
            "gpu_hours": gpu_hours,
            "wall_days": wall_days,
            "cost_usd": cost_usd,
        }


planner = InfrastructurePlanner()
SEVEN_B = 7_000_000_000
ONE_T = 1_000_000_000_000

for fleet in (8, 512):
    est = planner.estimate_compute(SEVEN_B, ONE_T, gpus=fleet)
    print(f"{fleet:>3} A100s: {est['wall_days']:.1f} days, ${est['cost_usd']:,.0f}")

h100 = planner.estimate_compute(SEVEN_B, ONE_T, gpus=512, hardware="H100")
print(f"512  H100s: {h100['wall_days']:.1f} days, ${h100['cost_usd']:,.0f}")
```

**Output:**

```text
  8 A100s: 389.5 days, $224,359
512 A100s: 6.1 days, $224,359
512  H100s: 3.8 days, $235,690
```

What to notice:

- **The total cost is invariant to fleet size** — 8 A100s and 512 A100s both
  cost $224,359, because the work is the same 74,786 GPU-hours; more GPUs
  only buys wall-clock time (389.5 days → 6.1 days). This is why scaling
  debates are always about *time-to-result*, not price.
- The H100 row costs *more* in total ($235,690 at $5/hr vs $3/hr) yet
  finishes 1.6× sooner (3.8 days). Whether that trade is worth it depends on
  what the faster result is worth to you — exactly the arithmetic this class
  exists to make explicit.
- One more constraint the FLOPs rule ignores: **memory**. Under AdamW mixed
  precision, a model needs roughly 16-20GB of accelerator memory per 1B
  parameters (fp32 master weights + Adam moments + gradients + activations),
  so a 7B model does not train on a single 80GB A100 — it needs sharding or
  offloading across GPUs, which is module 2402's subject.

## Part 8: The Pre-training Loop, End to End

Everything above converges here. The block below is the complete pre-training
loop — tokenize, stream sliding windows, predict the next token, cross-entropy
loss, AdamW, repeat — at a scale that finishes in seconds on a CPU. The shape
is identical to a 7B run; the production differences (billions of tokens,
multi-GPU sharding, mixed precision, fault tolerance) are scale, not
structure.

```python
"""
The complete pre-training loop, at a scale that finishes in seconds.

Same shape as a 7B run: tokenize -> stream sliding windows -> predict
the next token -> cross-entropy -> AdamW -> repeat. The production
differences are scale (billions of tokens, multi-GPU sharding, mixed
precision), not structure - module 2402 covers those.
"""

import torch
import torch.nn as nn

torch.manual_seed(0)

corpus = [
    "language models learn to predict the next word in a sequence",
    "pre training teaches a model language structure from raw text",
    "the model sees billions of tokens during pre training",
    "curriculum design orders data from clean to noisy",
    "tokenization maps text to integer ids before training",
    "the loss is cross entropy over the next word",
    "a well tuned learning rate schedule stabilizes training",
    "evaluation measures perplexity on held out text",
    "the same training loop scales from tiny to trillion token runs",
    "data quality matters more than data quantity",
]

words = sorted({w for line in corpus for w in line.split()})
stoi = {w: i for i, w in enumerate(words)}
V = len(words)
stream = torch.tensor([stoi[w] for line in corpus for w in line.split()])

windows = stream.unfold(0, 16, 1)   # (N, 16) sliding windows over the stream
X, Y = windows[:, :-1], windows[:, 1:]  # predict each next word


class TinyCausalLM(nn.Module):
    """One causal attention head + MLP - a pre-transformer in miniature."""

    def __init__(self, vocab: int, dim: int = 32, ctx: int = 16):
        super().__init__()
        self.emb = nn.Embedding(vocab, dim)
        self.pos = nn.Embedding(ctx, dim)
        self.qkv = nn.Linear(dim, 3 * dim, bias=False)
        self.proj = nn.Linear(dim, dim, bias=False)
        self.mlp = nn.Sequential(nn.Linear(dim, 4 * dim), nn.GELU(), nn.Linear(4 * dim, dim))
        self.head = nn.Linear(dim, vocab, bias=False)

    def forward(self, idx: torch.Tensor) -> torch.Tensor:
        B, T = idx.shape
        x = self.emb(idx) + self.pos(torch.arange(T))
        q, k, v = self.qkv(x).chunk(3, dim=-1)
        att = q @ k.transpose(-2, -1) / T ** 0.5
        causal = torch.triu(torch.ones(T, T, dtype=torch.bool), diagonal=1)
        att = att.masked_fill(causal, float("-inf"))
        x = x + self.proj(torch.softmax(att, dim=-1) @ v)
        x = x + self.mlp(x)
        return self.head(x)


model = TinyCausalLM(V)
optimizer = torch.optim.AdamW(model.parameters(), lr=0.01, weight_decay=0.01)

losses = []
for step in range(300):
    optimizer.zero_grad()
    logits = model(X)
    loss = nn.functional.cross_entropy(logits.reshape(-1, V), Y.reshape(-1))
    loss.backward()
    optimizer.step()
    losses.append(loss.item())

print(f"vocab: {V} words (random-guess loss ln(V) = {torch.log(torch.tensor(float(V))):.2f})")
print(f"loss step 0: {losses[0]:.2f} -> step 299: {losses[-1]:.2f}")

prompt = torch.tensor([[stoi["the"], stoi["model"]]])
for _ in range(6):
    logits = model(prompt)
    next_id = logits[0, -1].argmax()
    prompt = torch.cat([prompt, next_id.view(1, 1)], dim=1)
print("sample:", " ".join(words[i] for i in prompt[0].tolist()))
```

**Output:**

```text
vocab: 64 words (random-guess loss ln(V) = 4.16)
loss step 0: 4.51 -> step 299: 0.03
sample: the model sees billions of tokens during pre
```

What to notice:

- The untrained loss (4.51) sits slightly *above* the random-guess baseline
  ln(V) = 4.16 — random initialization is not the uniform distribution, and
  the first optimizer steps are spent getting down to it. Watching a new run
  approach ln(V) from above is a standard sanity check.
- The final loss of 0.03 is honest **memorization**: a ~500-token corpus
  trained for 300 full-batch steps leaves nothing to generalize. The prompt
  `the model` continues with the corpus line it memorized
  (`sees billions of tokens during pre`). Real pre-training is exactly this
  loop, with the memorization-forcing ratio removed — billions of distinct
  tokens instead of a few hundred.
- The causal mask (`triu` + `-inf` + softmax) is the entire
  autoregressive contract: position *t* can attend to positions ≤ *t* only.
  You met the proof of this in module PREREQUISITES; here it silently does
  its job inside the loop.
- The production path from here — HuggingFace `Trainer`, `accelerate`, FSDP
  sharding, checkpoint/resume — is module
  [2402: Large-Scale Training for Language Models](./2402-Large-Scale-Training.md),
  and the full hands-on build is
  [LAB 006: Train a Small Language Model from Scratch](../../../learning-resources/labs/LAB-006-Train-Model-From-Scratch.md).

## Summary

Pre-training looks like one thing — predict the next token — but the lesson's
pipeline shows how many decisions hide behind it: which corpora, which
filters, which dedup passes, which vocabulary, which schedules, which
evaluation cadence, and whether the compute budget is real. Each decision is
small; together they decide whether the final model is good.

```yaml
# Pre-training launch checklist
data:
  - Collect from 4-6 complementary sources
  - Filter: length, language, repetition, blocklists
  - Deduplicate: exact (hash) + near-duplicate (MinHash)
  - Hold out a validation split BEFORE training
tokenizer:
  - Train BPE/SentencePiece on the filtered corpus
  - Fix vocabulary size before training (32k-250k typical)
  - Verify round-trip: decode(encode(text)) == text
training:
  - Warmup LR for the first 1-2% of steps, then cosine decay to ~10% of max
  - Curriculum: clean data early, anneal on the best mix
  - Track loss AND held-out perplexity every N steps
  - AdamW: betas (0.9, 0.999), weight decay 0.01
infrastructure:
  - Estimate: 6 x params x tokens FLOPs -> GPU-hours -> dollars
  - Plan VRAM: ~16-20GB per 1B params (AdamW mixed precision)
  - Validate the plan on a small run before the full run
```

Key takeaways:

- **Data quality compounds.** Filters, exact dedup, and MinHash near-dup
  removal all run *before* step zero; no amount of training fixes a
  contaminated corpus afterwards.
- **The tokenizer is frozen infrastructure.** It is trained first, verified
  with round-trip checks, and never touched again — every capability the
  model has must be expressible in its tokens.
- **Schedules are functions of step number.** Curriculum stages in
  percentages and warmup-then-decay LR are the two schedules that make long
  runs stable, and both scale from smoke tests to production unchanged.
- **Perplexity is the compass, not the destination.** Track held-out
  perplexity every few hundred steps; consult benchmarks to know what the
  model can actually do.
- **6·N·D makes costs discussable.** 6×7B×1T FLOPs = 74,786 A100-hours ≈
  $224k — and fleet size changes wall-clock, not price.

## References

### Related Documents

- [2400: LLM Pretraining](./README.md) — module overview, time budget, and the assessment for this lesson
- [2400: LLM Pretraining - Prerequisites](./PREREQUISITES.md) — self-test review of the calculus, framework, and attention background
- [2402: Large-Scale Training for Language Models](./2402-Large-Scale-Training.md) — the scale-up of this lesson's loop: multi-GPU, mixed precision, fault tolerance
- [2403: Evaluation Frameworks for Language Models](./2403-Evaluation-Frameworks.md) — running MMLU/HellaSwag and friends properly
- [LAB 006: Train a Small Language Model from Scratch](../../../learning-resources/labs/LAB-006-Train-Model-From-Scratch.md) — the hands-on version of Part 8
- [3202: Tokenizer Sciences - BPE, SentencePiece, and Tiktoken](../../phase3-transformers/3200-embeddings/3202-Tokenizer-Sciences.md) — deep dive on Part 4's tokenizer

### External References

- [Language Models are Few-Shot Learners (GPT-3)](https://arxiv.org/abs/2005.14165) — Brown et al., 2020; the pre-training recipe and data mix behind GPT-3
- [Training Compute-Optimal Large Language Models (Chinchilla)](https://arxiv.org/abs/2203.15556) — Hoffmann et al., 2022; how to split a compute budget between N and D (~20 tokens per parameter)
- [Neural Machine Translation of Rare Words with Subword Units](https://arxiv.org/abs/1508.07909) — Sennrich et al., 2016; the BPE paper
- [Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer (T5/C4)](https://arxiv.org/abs/1910.10683) — Raffel et al., 2020; the C4 cleaning heuristics in detail
- [The Pile: An 800GB Dataset of Diverse Text for Language Modeling](https://arxiv.org/abs/2101.00027) — Gao et al., 2020; a curated-corpus design study
- [HuggingFace Tokenizers documentation](https://huggingface.co/docs/tokenizers) — the library used in Part 4 (BPE, ByteLevel, trainers)

## Next Steps

- **Next Lesson:** [2402: Large-Scale Training for Language Models](./2402-Large-Scale-Training.md) — scale this loop to multi-GPU: data/tensor/pipeline parallelism, mixed precision, and checkpointing
- **Practical:** [LAB 006: Train a Small Language Model from Scratch](../../../learning-resources/labs/LAB-006-Train-Model-From-Scratch.md) — build and pre-train a small LM yourself, following Part 8's shape
- **Assessment:** [2400: Pretraining Fundamentals - Quiz](./assessment/QUIZ.md) and [2400: Pre-training - Practice](./assessment/PRACTICE.md)

**Related:** [3202: Tokenizer Sciences - BPE, SentencePiece, and Tiktoken](../../phase3-transformers/3200-embeddings/3202-Tokenizer-Sciences.md)

**Experiment:** [EXP_3202: Tokenizer Performance Experiments](../../../../experiments/EXP_3202_TOKENIZER.md) (nearest-relevant - no EXP_24xx exists; this lesson trains a toy BPE tokenizer in Part 4, and EXP_3202 measures tokenizer performance trade-offs in depth)
