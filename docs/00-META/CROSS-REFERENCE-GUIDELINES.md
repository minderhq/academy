---
Document ID: CROSS-REFERENCE-GUIDELINES
Title: "Minder Academy Cross-Reference Guidelines"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Beginner
Tags: ['maintenance', 'navigation']
---

# Minder Academy Cross-Reference Guidelines

**Version:** 1.0
**Last Updated:** 2026-09-30
**Status:** Active

---

## Overview

This document provides guidelines for creating and maintaining cross-references between Minder Academy documentation files. Proper cross-referencing improves navigation, discoverability, and learning path coherence.

---

## Link Types

### 1. Internal Links (Relative)

Use relative paths for links within Minder Academy:

```markdown
# Same directory
[Document Title](./other-document.md)

# Parent directory
[Document Title](../parent-document.md)

# Child directory
[Document Title](./subdirectory/document.md)

# Cousin directory
[Document Title](../other-directory/document.md)

# Root-relative from docs/
[Document Title](../../phases/phase1-infra/1100-network/1101-Fiber-GPON-Modem.md)
```

### 2. External Links

Use full URLs for external resources:

```markdown
[OpenAI Documentation](https://platform.openai.com/docs)
[Hugging Face Transformers](https://huggingface.co/docs/transformers/)
```

### 3. Anchor Links

Link to sections within the same document:

```markdown
[See Technical Specifications](#2-technical-specifications)
```

**Note:** Anchor IDs are auto-generated from headings:
- Convert to lowercase
- Replace spaces with hyphens
- Remove special characters

---

## Standard Cross-Reference Sections

### References Section (Bottom of Document)

Every technical document should include a References section:

```markdown
## References

### Academic Papers
- [1] Vaswani et al. "Attention Is All You Need". NeurIPS, 2017.

### Documentation
- [PyTorch Documentation](https://pytorch.org/docs) - Official PyTorch docs

### Related Minder Academy Documents
- [3101: Self-Attention](../../phases/phase3-transformers/3100-attention/3101-Self-Attention-DeepDive.md) - Deep dive into attention
- [3301: Activation Functions](../../phases/phase3-transformers/3300-decoding/3301-Activation-Functions.md) - GELU, SwiGLU

### External Resources
- [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/) - Visual guide
```

### Next Steps Section

Guide learners to the next logical document:

```markdown
## Next Steps

- Continue with: **[Next Document ID: Title](./next-document.md)**
- Related: **[Related Document ID: Title](../directory/related.md)**
- Practical: **[LAB-XXX: Lab Title](../../../learning-resources/labs/LAB-XXX.md)**
- Assessment: **[assessment/QUIZ.md](assessment/QUIZ.md)**
```

### See Also Section

Provide additional related resources:

```markdown
## See Also

- **Related Module:** [Module Number: Module Title](../module-directory/)
- **Prerequisite:** [Document ID: Title](./prerequisite.md)
- **Advanced Topic:** [Document ID: Title](./advanced-topic.md)
- **Quick Reference:** [Cheat Sheet](../../../learning-resources/cheat-sheets/CHEAT-SHEET-XXX.md)
```

---

## Link Relationships

### Prerequisite Links

Link to documents that should be completed first:

```markdown
### Prerequisites

- **Required:** [2101: Tensor Algebra](../../phases/phase2-foundations/2100-calculus/2101-Tensor-Algebra.md)
- **Recommended:** [2201: PyTorch Graphs](../../phases/phase2-foundations/2200-frameworks/2201-PyTorch-Computational-Graphs.md)
- **Helpful:** [CHEAT-SHEET-002: Python AI](../../../learning-resources/cheat-sheets/CHEAT-SHEET-002-Python-AI.md)
```

### Related Document Links

Link to documents on similar topics:

```markdown
### Related Documents

| Document | Relationship | Description |
|----------|--------------|-------------|
| [3102: Flash Attention](./3102-Flash-Attention.md) | Alternative | Memory-efficient attention |
| [4101: GGUF Physics](../../phases/phase4-quantization/4100-low-bit/4101-GGUF-Physics.md) | Application | Quantization for attention |
| [7101: ReAct Loop](../../phases/phase7-agentic/7100-architecture/7101-ReAct-Loop-System.md) | Advanced | Attention in agents |
```

### Experiment Links

Link to related experiments:

```markdown
## Related Experiments

| Experiment | Description | Time |
|------------|-------------|------|
| [EXP_3101: Self-Attention](../../../experiments/EXP_3101_SELF_ATTENTION.md) | Implement attention from scratch | 2 hrs |
| [EXP_3102: Flash Attention](../../../experiments/EXP_3102_FLASH_ATTENTION.md) | Benchmark attention mechanisms | 3 hrs |
```

---

## Link Templates

### Document Link Template

```markdown
[Document ID: Title](relative/path/to/document.md)
```

### Module Link Template

```markdown
[Module Number: Module Title](../../phases/phaseX-module/module-directory/)
```

### Lab Link Template

```markdown
[LAB-XXX: Lab Title](../../../learning-resources/labs/LAB-XXX-Lab-Title.md)
```

### Tutorial Link Template

```markdown
[TUTORIAL-XXX: Tutorial Title](../../../learning-resources/tutorials/TUTORIAL-XXX-Tutorial-Title.md)
```

### Volume Link Template

```markdown
[Volume X: Volume Title](../../../volumes/VOLUME-X-Volume-Title.md)
```

---

## Best Practices

### 1. Use Descriptive Link Text

❌ **Bad:** `[Click here](./document.md)`
✅ **Good:** `[See Self-Attention Deep Dive](./3101-Self-Attention-DeepDive.md)`

### 2. Include Document IDs in Link Text

❌ **Bad:** `[See the attention guide](./3101-Self-Attention-DeepDive.md)`
✅ **Good:** `[3101: Self-Attention Deep Dive](./3101-Self-Attention-DeepDive.md)`

### 3. Group Related Links

```markdown
### Related Documents

**Core Concepts:**
- [3101: Self-Attention](./3101-Self-Attention-DeepDive.md)
- [3102: Flash Attention](./3102-Flash-Attention.md)

**Applications:**
- [4101: GGUF Physics](../../phases/phase4-quantization/4100-low-bit/4101-GGUF-Physics.md)
- [7101: ReAct Loop](../../phases/phase7-agentic/7100-architecture/7101-ReAct-Loop-System.md)
```

### 4. Provide Context for External Links

❌ **Bad:** [More info](https://pytorch.org/docs)
✅ **Good:** [PyTorch Documentation](https://pytorch.org/docs) - Official PyTorch API reference

### 5. Use Tables for Multiple Links

```markdown
| Document | Difficulty | Time | Description |
|----------|------------|------|-------------|
| [3101: Self-Attention](./3101-Self-Attention-DeepDive.md) | ⭐⭐⭐ | 4 hrs | Core attention mechanism |
| [3102: Flash Attention](./3102-Flash-Attention.md) | ⭐⭐⭐⭐ | 3 hrs | Memory-efficient attention |
```

---

## Link Validation

### Validation Checklist

Before marking a document as Complete, verify:

- [ ] All internal links point to existing files
- [ ] All external links are accessible
- [ ] Anchor links point to valid sections
- [ ] Link text is descriptive
- [ ] Document IDs are included in link text
- [ ] Related documents are properly linked
- [ ] Next steps are clearly defined
- [ ] References section is complete

### Validation Commands

```bash
# Find broken internal links (example script)
grep -r '\[.*\](' Minder Academy/docs/ | while read line; do
    # Extract the source file from the grep output and the link path
    file="${line%%:*}"
    link=$(echo "$line" | sed -n 's/.*](\([^)]*\)).*/\1/p')
    # Check if file exists (for relative links)
    if [[ "$link" == ../* ]] || [[ "$link" == ./* ]]; then
        if [ ! -f "$(dirname "$file")/$link" ]; then
            echo "Broken link in $file: $link"
        fi
    fi
done
```

---

## Common Link Patterns

### Phase Navigation

```markdown
**Previous Phase:** [Phase 2: AI/ML Foundations](../../phases/phase2-foundations/)
**Current Phase:** [Phase 3: Transformer Physics](../)
**Next Phase:** [Phase 4: Quantization](../../phases/phase4-quantization/)
```

### Module Navigation

```markdown
**Previous Module:** [3100: Attention](../3100-attention/)
**Current Module:** [3200: Embeddings](../)
**Next Module:** [3300: Decoding](../3300-decoding/)
```

### Learning Path Navigation

```markdown
**Learning Path:**

1. ✅ [1101: Fiber GPON Modem](./1101-Fiber-GPON-Modem.md)
2. ✅ [1102: Star Topology Core](./1102-Star-Topology-Core.md)
3. → [1103: Jumbo Frames and MTU](./1103-Jumbo-Frames-and-MTU.md) ← **You are here**
4. ⏭️ [1201: Proxmox Hypervisor SOP](../1200-virtualization/1201-Proxmox-Hypervisor-SOP.md)
```

---

## Cross-Reference Maintenance

### When to Update Links

Update cross-references when:

1. **Creating a new document** - Add links from related documents
2. **Moving a document** - Update all links pointing to it
3. **Deleting a document** - Remove all links pointing to it
4. **Renaming a document** - Update all links pointing to it
5. **Reorganizing structure** - Batch update affected links

### Link Maintenance Process

1. **Identify affected documents** using grep or find
2. **Update links** in all affected documents
3. **Validate links** using validation script
4. **Test navigation** by clicking through links
5. **Update SITEMAP.md** if structure changed

---

## Automated Link Checking

### GitHub Actions Workflow Example

```yaml
name: Check Links

on: [push, pull_request]

jobs:
  link-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - name: Link Checker
        uses: gaurav-nelson/github-action-markdown-link-check@v1
        with:
          use-verbose-mode: 'yes'
          config-file: '.github/markdown-link-check.json'
```

---

## Quick Reference

### Link Syntax Summary

| Link Type | Syntax | Example |
|-----------|--------|---------|
| Same directory | `[Text](./file.md)` | `[Next](./next.md)` |
| Parent directory | `[Text](../file.md)` | `[Up](../parent.md)` |
| Child directory | `[Text](./dir/file.md)` | `[Guide](./guides/guide.md)` |
| Root-relative | `[Text](../../path/file.md)` | `[Doc](../../phases/...)` |
| External | `[Text](https://example.com)` | `[PyTorch](https://pytorch.org)` |
| Anchor | `[Text](#section)` | `[Top](#overview)` |

## Related Documents

- [DOCUMENT-TEMPLATE.md](DOCUMENT-TEMPLATE.md)
- [SITEMAP.md](SITEMAP.md)
