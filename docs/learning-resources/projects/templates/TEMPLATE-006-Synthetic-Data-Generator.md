---
Document ID: TEMPLATE-006-Synthetic-Data-Generator
Title: "PROJECT TEMPLATE: Synthetic Data Generator"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Beginner
Tags: ['template', 'synthetic-data', 'distillation']
---

# PROJECT TEMPLATE: Synthetic Data Generator

Generate training data with LLMs.

## Project Structure

```text
synthetic-data-generator/
├── README.md
├── pyproject.toml
├── uv.lock
├── config/
│   ├── generators_config.yaml
│   └── quality_config.yaml
├── src/
│   ├── __init__.py
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── instruction.py    # Instruction generation
│   │   ├── conversation.py   # Conversation generation
│   │   ├── reasoning.py      # CoT data generation
│   │   └── code.py           # Code generation
│   ├── filters/
│   │   ├── __init__.py
│   │   ├── quality.py        # Quality scoring
│   │   ├── diversity.py      # Diversity filtering
│   │   └── deduplication.py  # Duplicate removal
│   ├── augmenters/
│   │   ├── __init__.py
│   │   ├── back_translation.py
│   │   └── paraphrase.py
│   ├── validators/
│   │   ├── __init__.py
│   │   └── schema.py         # Data validation
│   └── pipeline.py           # Generation pipeline
├── data/
│   ├── raw/
│   ├── filtered/
│   └── final/
├── templates/
│   ├── instruction.txt
│   ├── conversation.txt
│   └── reasoning.txt
└── scripts/
    ├── generate.py
    ├── filter.py
    └── export.py
```

## Features

- Multiple data generation types
- Quality filtering
- Data augmentation
- Deduplication
- Export formats (JSON, JSONL)

## Quick Start

### Generate Instruction Data

```python
from src.generators.instruction import InstructionGenerator

generator = InstructionGenerator(
    llm="gpt-4",
    templates=["templates/instruction.txt"]
)

data = generator.generate(
    num_samples=1000,
    domains=["python", "javascript", "sql"]
)
```

### Generate Conversation Data

```python
from src.generators.conversation import ConversationGenerator

generator = ConversationGenerator(
    llm="gpt-4",
    num_turns=4
)

conversations = generator.generate(
    topics=["AI", "programming", "science"],
    num_samples=500
)
```

### Generate CoT Data

```python
from src.generators.reasoning import ReasoningGenerator

generator = ReasoningGenerator(
    llm="gpt-4"
)

cot_data = generator.generate(
    questions=question_list,
    reasoning_style="step_by_step"
)
```

## Quality Filtering

```python
from src.filters.quality import QualityFilter

filter_config = {
    "min_length": 50,
    "max_length": 500,
    "min_unique_ratio": 0.5,
    "forbidden_patterns": ["...", "UNK"]
}

filter = QualityFilter(filter_config)
filtered_data = filter.filter(raw_data)
```

## Pipeline

```bash
# Generate, filter, and export
python scripts/generate.py \
  --type instruction \
  --num_samples 1000 \
  --output data/raw/instructions.jsonl

python scripts/filter.py \
  --input data/raw/instructions.jsonl \
  --output data/filtered/instructions.jsonl

python scripts/export.py \
  --input data/filtered/instructions.jsonl \
  --format jsonl \
  --output data/final/instructions.jsonl
```

## Data Augmentation

```python
from src.augmenters.back_translation import BackTranslationAugmenter

augmenter = BackTranslationAugmenter(
    intermediate_lang="german"
)

augmented = augmenter.augment(original_data)
```

## Templates

Create custom templates in `templates/`:
```text
Generate a {domain} question about {topic}.
The question should be {difficulty} level.

Question:
```

Variables: `{domain}`, `{topic}`, `{difficulty}`, etc.

---

**Difficulty:** Intermediate
**Estimated Time:** 6-10 hours
**Skills:** Data generation, LLM prompting, Quality filtering
