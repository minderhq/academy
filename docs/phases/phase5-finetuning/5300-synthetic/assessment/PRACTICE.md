---
Document ID: 5300-PRACTICE
Title: "5300: Synthetic Data Generation - Practice"
Last Updated: 2026-09-25
Status: Complete
Difficulty: Advanced
Estimated Time: 5 hours
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'practice', 'finetuning', 'synthetic-data']
---

# 5300: Synthetic Data Generation - Practice

## Exercises

### Exercise 1: Generate Instruction Data

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
import random

# Load base model. gpt2 runs anywhere; for production-quality synthetic
# data swap in a strong instruct model, e.g. Qwen/Qwen2.5-7B-Instruct
# (meta-llama/Llama-2-7b-hf is gated - it needs approved HF access).
model = AutoModelForCausalLM.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")

# Define prompts for synthetic data
instruction_templates = [
    "Write a {domain} tutorial about {topic}.",
    "Explain {concept} in simple terms.",
    "Create a {type} exercise for {subject}.",
    "Write code to {task} in {language}.",
]

domains = ["machine learning", "web development", "data science", "mobile apps"]
topics = ["classification", "APIs", "visualization", "user interfaces"]
concepts = ["neural networks", "REST", "SQL", "OAuth"]
types = ["practice", "quiz", "assignment", "lab"]
subjects = ["Python", "JavaScript", "SQL", "TensorFlow"]
tasks = ["sort a list", "fetch data", "train a model", "authenticate users"]
languages = ["Python", "JavaScript", "SQL", "R"]

def generate_synthetic_instructions(num_samples=100):
    """Generate synthetic instruction-response pairs."""

    synthetic_data = []

    for i in range(num_samples):
        # Sample template and fill slots
        template = random.choice(instruction_templates)

        prompt = template.format(
            domain=random.choice(domains),
            topic=random.choice(topics),
            concept=random.choice(concepts),
            type=random.choice(types),
            subject=random.choice(subjects),
            task=random.choice(tasks),
            language=random.choice(languages),
        )

        # Generate response
        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(
            **inputs,
            max_new_tokens=200,
            temperature=0.8,
            do_sample=True,
            top_p=0.95,
        )

        # Decode only the newly generated tokens (generate returns
        # prompt + completion; stripping the prompt with replace()
        # breaks when the detokenizer normalizes whitespace)
        prompt_len = inputs["input_ids"].shape[-1]
        response = tokenizer.decode(outputs[0][prompt_len:], skip_special_tokens=True)

        synthetic_data.append({
            "instruction": prompt,
            "output": response,
        })

        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"Generated {i + 1}/{num_samples} samples")

    return synthetic_data

# Generate and save
print("Generating synthetic instruction data...")
data = generate_synthetic_instructions(100)
with open("synthetic_instructions.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"\nGenerated {len(data)} instruction-response pairs")
print(f"Sample entry:")
print(json.dumps(data[0], indent=2))

# Expected Output:
# Generating synthetic instruction data...
# Generated 10/100 samples
# ...
# Generated 100/100 samples
#
# Generated 100 instruction-response pairs
# Sample entry:
# {
#   "instruction": "...",
#   "output": "..."
# }
# (completion text varies with the loaded model and sampling)
```

### Exercise 2: Data Augmentation with Back Translation

```python
from transformers import pipeline

# Load translation models
print("Loading translation models...")
translator_en_de = pipeline("translation", model="Helsinki-NLP/opus-mt-en-de")
translator_de_en = pipeline("translation", model="Helsinki-NLP/opus-mt-de-en")

def back_translate(text, n_variations=3):
    """Generate paraphrases via back-translation."""

    variations = []

    for i in range(n_variations):
        print(f"Generating variation {i+1}/{n_variations}...")

        # do_sample=True: greedy (the pipeline default) is deterministic,
        # so every round-trip returns the identical sentence and the
        # n_variations loop yields copies of one paraphrase
        german = translator_en_de(
            text, max_length=512, do_sample=True, temperature=0.8
        )[0]["translation_text"]

        # Translate back to English
        paraphrase = translator_de_en(
            german, max_length=512, do_sample=True, temperature=0.8
        )[0]["translation_text"]

        variations.append(paraphrase)

    return variations

# Augment dataset
original_text = "Machine learning is a subset of artificial intelligence."
print(f"Original: {original_text}\n")

paraphrases = back_translate(original_text, n_variations=3)

print(f"\nGenerated {len(paraphrases)} paraphrases:")
for i, paraphrase in enumerate(paraphrases, 1):
    print(f"Paraphrase {i}: {paraphrase}")

# Expected Output:
# Loading translation models...
# Original: Machine learning is a subset of artificial intelligence.
#
# Generating variation 1/3...
# Generating variation 2/3...
# Generating variation 3/3...
#
# Generated 3 paraphrases:
# Paraphrase 1: ...
# Paraphrase 2: ...
# Paraphrase 3: ...
# (round-trip wording varies per run - sampling drives the variation)
```

### Exercise 3: Generate Conversation Data

```python
import json
import random

def generate_conversations(model, tokenizer, num_conversations=50):
    """Generate synthetic multi-turn conversations."""

    conversations = []

    # Conversation starters
    starters = [
        "Can you help me with",
        "I'm trying to understand",
        "What's the difference between",
        "How do I",
        "Explain to me",
    ]

    topics = [
        "Python programming",
        "machine learning",
        "web development",
        "data structures",
    ]

    for conv_num in range(num_conversations):
        print(f"Generating conversation {conv_num + 1}/{num_conversations}")
        conversation = []

        # Start conversation
        user_msg = random.choice(starters) + " " + random.choice(topics)

        for turn in range(5):  # 5-turn conversations
            # User message
            conversation.append({"role": "user", "content": user_msg})

            # Format conversation for model
            prompt = ""
            for msg in conversation:
                if msg["role"] == "user":
                    prompt += f"User: {msg['content']}\n"
                else:
                    prompt += f"Assistant: {msg['content']}\n"
            prompt += "Assistant:"

            # Generate assistant response
            inputs = tokenizer(prompt, return_tensors="pt")
            outputs = model.generate(
                **inputs,
                max_new_tokens=150,
                temperature=0.8,
                do_sample=True,  # temperature is ignored in greedy mode
            )
            prompt_len = inputs["input_ids"].shape[-1]
            assistant_msg = tokenizer.decode(
                outputs[0][prompt_len:], skip_special_tokens=True
            )

            conversation.append({"role": "assistant", "content": assistant_msg})

            # Generate follow-up (simulate user)
            follow_up_prompts = [
                "Can you elaborate?",
                "What about X?",
                "Show me an example.",
                "That's helpful, thanks.",
            ]
            user_msg = random.choice(follow_up_prompts)

            if "thanks" in user_msg.lower():
                conversation.append({"role": "user", "content": user_msg})
                break

        conversations.append({"messages": conversation})

    return conversations

# Generate conversations
print("Generating synthetic conversations...")
convs = generate_conversations(model, tokenizer, num_conversations=20)

# Save conversations
with open("synthetic_conversations.json", "w") as f:
    json.dump(convs, f, indent=2)

print(f"\nGenerated {len(convs)} conversations")
print(f"Sample conversation:")
for msg in convs[0]["messages"][:4]:
    print(f"{msg['role']}: {msg['content'][:100]}...")

# Expected Output:
# Generating synthetic conversations...
# Generating conversation 1/20
# ...
# Generating conversation 20/20
#
# Generated 20 conversations
# Sample conversation:
# user: Can you help me with Python programming...
# assistant: ...
# (message text varies with the loaded model and sampling)
```

### Exercise 4: Synthetic Data for Reasoning

```python
import json
import random

def generate_reasoning_data(model, tokenizer, num_samples=100):
    """Generate chain-of-thought reasoning data."""

    # Every template uses the {question} slot: the call below does
    # .format(question=...), so {problem}/{query} would raise KeyError
    reasoning_prompts = [
        "Let's think step by step: {question}",
        "Break this down: {question}",
        "Solve this logically: {question}",
    ]

    questions = [
        "If I have 3 apples and eat 1, how many do I have?",
        "What comes next: 2, 4, 6, 8, ...?",
        "A bat and ball cost $1.10. The bat costs $1 more. How much is the ball?",
        "If it takes 5 machines 5 minutes to make 5 widgets, how long for 100 machines to make 100 widgets?",
        "A farmer has 17 sheep. All but 9 die. How many sheep does the farmer have left?",
    ]

    reasoning_data = []

    for i in range(num_samples):
        # Create reasoning prompt
        question = random.choice(questions)
        prompt = random.choice(reasoning_prompts).format(question=question)

        # Generate with reasoning
        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(
            **inputs,
            max_new_tokens=300,
            temperature=0.7,
            do_sample=True,
        )

        # Decode only the newly generated tokens - the full sequence
        # would carry the prompt verbatim inside the reasoning field
        prompt_len = inputs["input_ids"].shape[-1]
        response = tokenizer.decode(outputs[0][prompt_len:], skip_special_tokens=True)

        # Extract reasoning and answer
        reasoning_data.append({
            "question": question,
            "reasoning": response,
            "answer": extract_final_answer(response),
        })

        if (i + 1) % 20 == 0:
            print(f"Generated {i + 1}/{num_samples} reasoning samples")

    return reasoning_data

def extract_final_answer(response):
    """Extract final answer from reasoning."""
    # Look for answer patterns
    import re

    # Pattern 1: "Answer: X"
    match = re.search(r"Answer:\s*(.+?)(?:\.|$)", response, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Pattern 2: "Therefore, X" or "So, X"
    match = re.search(r"(?:Therefore|So),?\s*(.+?)(?:\.|$)", response, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Fallback: last sentence
    sentences = response.split(". ")
    return sentences[-1].strip() if sentences else ""

# Generate reasoning data
print("Generating reasoning data...")
reasoning_data = generate_reasoning_data(model, tokenizer, num_samples=50)

with open("synthetic_reasoning.json", "w") as f:
    json.dump(reasoning_data, f, indent=2)

print(f"\nGenerated {len(reasoning_data)} reasoning samples")
print(f"Sample:")
print(json.dumps(reasoning_data[0], indent=2)[:300] + "...")

# Expected Output:
# Generating reasoning data...
# Generated 20/50 reasoning samples
# Generated 40/50 reasoning samples
#
# Generated 50 reasoning samples
# Sample:
# {
#   "question": "...",
#   "reasoning": "...",
#   "answer": "..."
# }
#
# Note: base models frequently answer trick questions (bat-and-ball,
# widgets) incorrectly - pair this generation with the Exercise 6
# quality filtering before training on it.
```

### Exercise 5: Generate Code-Text Pairs

````python
import json

def generate_code_explanations(model, tokenizer, code_snippets):
    """Generate natural language explanations for code."""

    code_text_pairs = []

    for i, code in enumerate(code_snippets):
        print(f"Explaining code snippet {i+1}/{len(code_snippets)}")

        # Create prompt
        prompt = f"""Explain what this code does:

```python
{code}
```

Explanation:"""

        # Generate explanation
        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(
            **inputs,
            max_new_tokens=200,
            temperature=0.7,
            do_sample=True,  # temperature is ignored in greedy mode
        )
        prompt_len = inputs["input_ids"].shape[-1]
        explanation = tokenizer.decode(
            outputs[0][prompt_len:], skip_special_tokens=True
        )

        code_text_pairs.append({
            "code": code,
            "explanation": explanation,
        })

    return code_text_pairs

# Sample code snippets
code_snippets = [
    "def add(a, b): return a + b",
    "[x**2 for x in range(10)]",
    "df.groupby('column').mean()",
    "model.fit(X_train, y_train)",
    "import pandas as pd\ndf = pd.read_csv('data.csv')\ndf.head()",
    "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
    "numbers = [1, 2, 3, 4, 5]\nsum(numbers)\nlen(numbers)",
]

print("Generating code explanations...")
pairs = generate_code_explanations(model, tokenizer, code_snippets)

with open("code_text_pairs.json", "w") as f:
    json.dump(pairs, f, indent=2)

print(f"\nGenerated {len(pairs)} code-text pairs")
print(f"Sample:")
print(json.dumps(pairs[0], indent=2))

# Expected Output:
# Generating code explanations...
# Explaining code snippet 1/7
# ...
# Explaining code snippet 7/7
#
# Generated 7 code-text pairs
# Sample:
# {
#   "code": "def add(a, b): return a + b",
#   "explanation": "..."
# }
# (explanation text varies with the loaded model and sampling)
````

### Exercise 6: Quality Filtering

```python
import json

def filter_synthetic_data(data, quality_threshold=0.7):
    """Filter low-quality synthetic data."""

    filtered_data = []

    for item in data:
        score = 0

        # Check length (prefer 50-500 characters)
        output_length = len(item.get("output", ""))
        if 50 <= output_length <= 500:
            score += 0.3
        elif output_length > 0:
            score += 0.15  # Partial credit for non-empty

        # Check for repetition
        output = item.get("output", "")
        words = output.split()
        if words:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio > 0.5:
                score += 0.3
            elif unique_ratio > 0.3:
                score += 0.15  # Partial credit

        # Check for special tokens/artifacts
        special_tokens = ["<|", "UNK", "PAD", "<sent", "<para>"]
        if not any(token in output for token in special_tokens):
            score += 0.2

        # Check coherence (simple heuristic)
        if "..." not in output and output.count(".") > 0:
            score += 0.2

        # Keep high-quality samples
        if score >= quality_threshold:
            filtered_data.append({**item, "quality_score": score})

    return filtered_data

# Apply filtering
print("Filtering synthetic data...")
original_count = len(data)
filtered = filter_synthetic_data(data, quality_threshold=0.6)
filtered_count = len(filtered)

print(f"Original samples: {original_count}")
print(f"Filtered samples: {filtered_count}")
print(f"Kept: {filtered_count/original_count*100:.1f}%")

# Save filtered data
with open("filtered_synthetic_data.json", "w") as f:
    json.dump(filtered, f, indent=2)

# Show quality distribution
quality_scores = [item["quality_score"] for item in filtered]
print(f"\nQuality score statistics:")
print(f"  Min: {min(quality_scores):.2f}")
print(f"  Max: {max(quality_scores):.2f}")
print(f"  Average: {sum(quality_scores)/len(quality_scores):.2f}")

# Expected Output:
# Filtering synthetic data...
# Original samples: 100
# Filtered samples: <N>
# Kept: <N>.N%
#
# Quality score statistics:
#   Min: <N>.NN
#   Max: <N>.NN
#   Average: <N>.NN
# (counts depend entirely on the generated outputs being filtered)
```

### Exercise 7: Mix Real and Synthetic Data

```python
import json
import random

def create_training_mix(real_data, synthetic_data, synthetic_ratio=0.3):
    """Create a training set mixing real and synthetic data.

    synthetic_ratio (0 < ratio < 1) is the synthetic share of the
    FINAL mix, not of the source pool.
    """

    # n_syn / (n_real + n_syn) = ratio  =>  n_syn = n_real * ratio / (1 - ratio)
    # Sizing the sample from the pool total instead lets a large
    # synthetic pool dominate: with 100 synthetic vs 2 real and
    # ratio=0.2, the "0.2" mix would actually be ~91% synthetic.
    target_synthetic = min(
        len(synthetic_data),
        int(len(real_data) * synthetic_ratio / (1 - synthetic_ratio)),
    )
    sampled_synthetic = random.sample(synthetic_data, target_synthetic)

    # Combine
    mixed_dataset = real_data + sampled_synthetic

    # Shuffle
    random.shuffle(mixed_dataset)

    # Add source tag
    for item in mixed_dataset:
        if item in sampled_synthetic:
            item["_source"] = "synthetic"
        else:
            item["_source"] = "real"

    return mixed_dataset

# Example usage - a small real dataset for demonstration
real_data = [
    {"instruction": "Explain machine learning", "output": "Machine learning is a field where algorithms learn patterns from data."},
    {"instruction": "What is Python?", "output": "Python is a high-level programming language known for readability."},
    {"instruction": "Define overfitting", "output": "Overfitting is when a model memorizes training data instead of generalizing."},
    {"instruction": "What is a REST API?", "output": "A REST API exposes resources over HTTP using standard methods."},
    {"instruction": "Explain gradient descent", "output": "Gradient descent updates parameters in the direction that reduces the loss."},
    {"instruction": "What is a dataframe?", "output": "A dataframe is a two-dimensional labeled data structure with columns."},
    {"instruction": "Define regularization", "output": "Regularization adds constraints to a model to reduce overfitting."},
    {"instruction": "What is tokenization?", "output": "Tokenization splits text into units a model can process."},
    {"instruction": "Explain cross-validation", "output": "Cross-validation estimates generalization by rotating held-out folds."},
    {"instruction": "What is an embedding?", "output": "An embedding maps discrete items into dense continuous vectors."},
]

# Create mix
print("Creating mixed training dataset...")
mixed = create_training_mix(
    real_data,
    filtered,  # quality-filtered synthetic data from Exercise 6
    synthetic_ratio=0.3,
)

print(f"Total samples: {len(mixed)}")
print(f"Synthetic: {sum(1 for x in mixed if x['_source'] == 'synthetic')}")
print(f"Real: {sum(1 for x in mixed if x['_source'] == 'real')}")
print(f"Synthetic ratio: {sum(1 for x in mixed if x['_source'] == 'synthetic')/len(mixed):.1%}")

# Save mixed dataset
with open("mixed_training_data.json", "w") as f:
    json.dump(mixed, f, indent=2)

print("\nMixed dataset saved to mixed_training_data.json")

# Expected Output:
# Creating mixed training dataset...
# Total samples: 14
# Synthetic: 4
# Real: 10
# Synthetic ratio: 28.6%
#
# Mixed dataset saved to mixed_training_data.json
# (assumes Exercise 6 kept at least 4 samples - the min() cap in
# create_training_mix reduces the synthetic share otherwise)
```
