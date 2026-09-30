---
Document ID: STYLE-GUIDE
Title: "PROJECT-OMEGA Style Guide"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Beginner
---

# PROJECT-OMEGA Style Guide

**Official Documentation Standards**

**Last Updated:** 2026-02-04
**Version:** 1.0

---

## 📖 Purpose

This guide ensures consistency across all PROJECT-OMEGA documentation. Consistent documentation makes learning easier and reduces confusion.

---

## 🎯 Core Principles

1. **Clarity First:** Write for learners, not experts
2. **Be Specific:** Avoid vague statements
3. **Show Examples:** Code snippets clarify concepts
4. **Test Everything:** Verify code examples work
5. **Update Regularly:** Keep docs current with code

---

## 📝 Document Structure

### Standard Header

Every document MUST start with a YAML front-matter block, then the
visible H1 header (see the Front Matter Standard in
`ORGANIZATION-GUIDE.md` for the field rules and the QA gates that
enforce them):

```markdown
---
Document ID: [STABLE-SLUG]
Title: "Document Title"
Last Updated: YYYY-MM-DD
Status: Complete
Difficulty: Beginner
Tags: ['tag-one', 'tag-two']
---

# Document Title

**Last Updated:** YYYY-MM-DD
**Reading Time:** X minutes
**Difficulty:** ⭐ Beginner/⭐⭐ Intermediate/⭐⭐⭐ Advanced

---

## Overview

[2-3 sentences explaining what this document covers and why it matters]

---

## Prerequisites

**Required Knowledge:**
- [Concept 1](link) - Brief description
- [Concept 2](link) - Brief description

**Hardware/Software:**
- Requirement 1
- Requirement 2

---

## Table of Contents (if >5 sections)
```

### Standard Footer

Every document SHOULD end with:

```markdown
---

## Summary

[3-5 bullet points summarizing key takeaways]

---

## Next Steps

1. **[Related Topic](link)** - Description
2. **[Next Document](link)** - Description

---

## Resources

- [External Resource 1](url)
- [Internal Resource 2](link)

---

**Last Updated:** YYYY-MM-DD
**Contributors:** [Optional]
**See Also:** [Related Documents](link)
```

---

## 🔤 Typography

### Headings

```markdown
# H1: Document title (one per document)
## H2: Major sections
### H3: Subsections
#### H4: Rare, use sparingly
```

**Rules:**
- H1: Document title only
- H2: First level under H1
- Don't skip levels (H1 → H3)
- Max depth: H4

### Emphasis

```markdown
**Bold** for key terms, commands, UI elements
*Italic* for emphasis, foreign words
`Code` for inline code, file names, commands
```

### Lists

```markdown
**Unordered:**
- Item 1
- Item 2
  - Nested item
  - Another nested

**Ordered:**
1. Step 1
2. Step 2
   1. Sub-step 2.1
   2. Sub-step 2.2

**Task Lists:**
- [ ] Incomplete task
- [x] Completed task
```

---

## 💻 Code Blocks

### Language Specification

```markdown
\```python
def example():
    return "correct"
\```

\```bash
echo "correct"
\```

\```yaml
key: value
\```
```

**Rule:** ALWAYS specify language for syntax highlighting

### Code Block Standards

**Imports Included:**
```python
# ✅ CORRECT
import torch
from transformers import AutoModel

model = AutoModel.from_pretrained("gpt2")
```

```python
# ❌ INCORRECT
model = AutoModel.from_pretrained("gpt2")
# Missing import!
```

**Expected Output:**
```python
result = process_data(input_data)
print(result)
# Expected Output: {'status': 'success', 'count': 42}
```

**Error Handling:**
```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise
```

### File Paths

```markdown
Absolute: C:\AI-Studio\PROJECT-OMEGA\docs\00-META\README.md
Relative: ../00-META/README.md
Code: "docs/00-META/README.md"
```

---

## 📊 Tables

### Standard Format

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |
```

**Rules:**
- Header row required
- Alignment pipes: `|` on both ends
- Consistent spacing
- Max width: 100 characters

---

## 🔗 Links & References

### Internal Links

```markdown
[Document Name](../path/to/document.md)
[Section Name](#section-id)
[Code Reference](#code-block-above)
```

### External Links

```markdown
[Resource Name](https://example.com)
[Title](https://example.com "Hover text")
```

### Link Text

```markdown
✅ CORRECT:
[Download Ollama](https://ollama.com)
See the [setup guide](ENVIRONMENT-SETUP.md)

❌ INCORRECT:
[click here](https://ollama.com)
[link](ENVIRONMENT-SETUP.md)
```

---

## 🎯 Diagrams

### Mermaid Diagrams

```markdown
\```mermaid
graph TD
    A[Start] --> B[Process]
    B --> C[End]
\```
```

### Architecture Diagrams

```markdown
\```mermaid
graph LR
    User[User] --> API[FastAPI]
    API --> LLM[Ollama]
    API --> DB[(Qdrant)]
\```
```

---

## 📌 Callouts & Alerts

### Info Callout

```markdown
> **💡 Tip:** Helpful information
>
> Use this to provide useful hints or best practices.
```

### Warning Callout

```markdown
> **⚠️ Warning:** Important caution
>
> Use this to warn about potential issues or mistakes.
```

### Error Callout

```markdown
> **❌ Error:** Common mistake
>
> Use this to highlight frequent errors and how to avoid them.
```

### Success Callout

```markdown
> **✅ Success:** Achievement unlocked
>
> Use this to indicate completion or correct approach.
```

---

## 🏷️ Tags & Badges

### Status Badges

```markdown
**Status:** ✅ Complete / 🚧 In Progress / ❌ Deprecated
**Difficulty:** ⭐ Beginner / ⭐⭐ Intermediate / ⭐⭐⭐ Advanced
**Time:** X hours / Y minutes
```

### Version Tags

```markdown
**New in:** v2.0
**Updated:** 2026-02-04
**Deprecated:** Use [new feature](link) instead
```

### Frontmatter Tags

The `Tags:` field in the YAML front matter is the machine-readable
layer the platform's tag filter and related-content navigation read
- it is separate from the visual badges above. Canonical syntax:

```markdown
Tags: ['retrieval', 'vector-search', 'chroma']
```

- bracketed list, comma-space separated, each token single-quoted
- non-empty, unique tokens, kebab-case lowercase
- tokens come from the controlled vocabulary in
  `scripts/qa/tag_vocabulary_census.py` (extending it is a
  deliberate script edit)

Coverage and syntax are hard-gated (`tags_coverage_check.py`,
TG-01..03 + TS-01): a doc without Tags is invisible to the platform
browse graph.

---

## 📐 Layout & Spacing

### Section Breaks

```markdown
Major sections: --- (horizontal rule)
Lists: Blank line before and after
Code blocks: Blank line before and after
```

### Line Length

- Max: 100 characters (where possible)
- Code: 88 characters (PEP 8)
- Tables: Break into multiple lines

### Paragraphs

```markdown
✅ CORRECT:
First paragraph.

Second paragraph.

❌ INCORRECT:
First paragraph.
Second paragraph.
```

---

## 🗣️ Voice & Tone

### Guidelines

1. **Active Voice:** "Click the button" not "The button should be clicked"
2. **Direct Address:** "You should..." not "Users should..."
3. **Present Tense:** "This function returns..." not "This function will return..."
4. **Simple Language:** Explain jargon, use examples

### Examples

```markdown
✅ CORRECT:
"To train the model, run the following command:"
"Download the model using curl"
"Check the logs for errors"

❌ INCORRECT:
"The following command should be run in order to train the model"
"The model is able to be downloaded using the curl utility"
"The logs should be checked for the presence of errors"
```

---

## 🔢 Numbers & Units

### Numbers in Text

```markdown
✅ CORRECT:
- 7B model (not 7b)
- 10 minutes (not ten minutes)
- 3-4 hours (not 3 to 4 hours)
- 20% (not 20 percent)
- 5GB (not 5 gb)
```

### Measurements

```markdown
Time: 2 hours, 30 minutes, 45 seconds
Memory: 16GB RAM, 8GB VRAM
Storage: 100GB SSD
Speed: 1Gbps, 100MB/s
Temperature: 0.7 (dimensionless)
```

### Model Sizes

```markdown
✅ CORRECT:
- 7B model (7 billion parameters)
- 70B model (70 billion parameters)
- mistral:7b (specific variant)

❌ INCORRECT:
- 7b model
- 7B parameters
- Mistral 7B (inconsistent capitalization)
```

---

## 🎨 Formatting Priorities

### Hierarchy of Importance

1. **Readability:** Clear, easy to scan
2. **Accuracy:** Correct information
3. **Consistency:** Follow these standards
4. **Completeness:** Include all necessary info

### When to Break Rules

Break formatting rules IF:
- Significantly improves clarity
- Required by specific tool/constraint
- Documenting legacy code with existing style

Document WHY you broke the rule in comment.

---

## ✅ Quality Checklist

Before publishing/committing:

### Content
- [ ] All code examples tested
- [ ] All links verified
- [ ] All diagrams render correctly
- [ ] Spelling and grammar checked

### Structure
- [ ] Follows template (if applicable)
- [ ] Has proper header/footer
- [ ] TOC accurate (if present)
- [ ] Sections logically ordered

### Consistency
- [ ] Terminology follows [GLOSSARY.md](GLOSSARY.md)
- [ ] Code blocks have language specified
- [ ] Tables properly formatted
- [ ] Links use descriptive text

### Completeness
- [ ] Prerequisites stated
- [ ] Expected outcomes described
- [ ] Troubleshooting included (if complex)
- [ ] Next steps provided

---

## 🔄 Review Process

1. **Self-Review:** Use checklist above
2. **Peer Review:** Another person reviews
3. **Testing:** Try all examples
4. **Approval:** Merge/document

---

## 📚 Templates

### Tutorial Template

```markdown
# TUTORIAL-XXX: [Title]

**Duration:** X hours
**Difficulty:** ⭐⭐
**Prerequisites:** [Links]

## Learning Objectives
After this tutorial, you will:
- [ ] Skill 1
- [ ] Skill 2

## Steps
### Step 1: [Title]
[Content]

### Step 2: [Title]
[Content]

## Summary
[Key takeaways]

## Next Steps
[Related resources]
```

### Lab Template

```markdown
# LAB-XXX: [Title]

**Duration:** X hours
**Difficulty:** ⭐⭐
**Prerequisites:** [Links]

## Objectives
[Goals]

## Steps
[Detailed instructions]

## Verification
[Checklist]

## Troubleshooting
[Common issues]
```

---

## 🆘 Getting Help

### Questions?

1. Check [GLOSSARY.md](GLOSSARY.md)
2. Review examples in this guide
3. Ask in community forums

### Contributions

Improvements welcome! Submit PR with:
- Clear description of change
- Reasoning for improvement
- Examples of before/after

