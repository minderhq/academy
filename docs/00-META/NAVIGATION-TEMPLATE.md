# Navigation Template

**Standard Navigation Structure for All Documents**

---

## 📐 Navigation Section (Add to documents)

### Placement

Add this section AFTER the main content, BEFORE the footer:

```markdown
---

## Navigation

### In This Section

**Previous:** [Previous Document](../path/to/previous.md) - Brief description

**Next:** [Next Document](../path/to/next.md) - Brief description

### Related Topics

- **[Related Topic 1](../path/to/topic1.md)** - When to use this
- **[Related Topic 2](../path/to/topic2.md)** - How it connects

### Prerequisites

**Required Before Starting:**
- [Prerequisite 1](../path/to/prereq1.md) - Description
- [Prerequisite 2](../path/to/prereq2.md) - Description

**Verify You're Ready:**
- [ ] Can explain [concept from prereq 1]
- [ ] Can implement [skill from prereq 2]
- [ ] Have [tool/software] installed

### Deep Dive

**Want to Learn More?**
- **[Advanced Topic](../path/to/advanced.md)** - Deep dive on this subject
- **[Implementation Guide](../path/to/guide.md)** - Hands-on guide
- **[Research Paper](external-link)** - Original source

### Resources

**External Resources:**
- [Resource 1](https://example.com) - Description
- [Resource 2](https://example.com) - Description

**Internal Resources:**
- [Glossary](../00-META/GLOSSARY.md) - Terminology
- [Troubleshooting](../learning-resources/troubleshooting/TROUBLESHOOTING-Common-Issues.md) - Common issues
```

---

## 🍞 Breadcrumb Template

### For Phase Documents

```markdown
**Path:** Home > [Volume X](../volumes/VOLUME-X.md) > Phase XXXX > [Module Name](.)

**Example:**
Home > Volume 3 > Phase 3 > [3100] Attention > 3101 Self-Attention
```

### For Learning Resources

```markdown
**Path:** Home > [Learning Resources](../learning-resources/) > [Type](../learning-resources/[type]/) > [Document Name](.)

**Example:**
Home > Learning Resources > Tutorials > TUTORIAL-001
```

---

## 🔗 Cross-Reference Standards

### Linking Between Documents

```markdown
✅ CORRECT:
See [3101-Self-Attention](../../3100-attention/3101-Self-Attention-DeepDive.md) for details.

❌ INCORRECT:
See 3101 for details.
See the attention document.
Click here.
```

### Referencing Code

```markdown
✅ CORRECT:
The `process_data()` function in [processing.py](../code/processing.py) handles this.

❌ INCORRECT:
The processing file handles this.
```

### Referencing Experiments

```markdown
✅ CORRECT:
Try [EXP_3101: Self-Attention](../../experiments/EXP_3101_SELF_ATTENTION.md) to test this.

❌ INCORRECT:
Try the experiment.
```

---

## 📊 Navigation by Document Type

### Tutorial Navigation

```markdown
## Continue Your Journey

**Next Tutorial:** [TUTORIAL-002](./TUTORIAL-002-[Title].md)
**Related Lab:** [LAB-001](../learning-resources/labs/LAB-001-[Title].md)
**Build Project:** [PROJECT-001](../projects/PROJECT-001-[Title].md)
```

### Lab Navigation

```markdown
## Progress Checklist

- [ ] Lab completed
- [ ] Code working
- [ ] Concepts understood

**Next Lab:** [LAB-002](./LAB-002-[Title].md)
**Related Tutorial:** [TUTORIAL-003](../tutorials/TUTORIAL-003-[Title].md)
**Build On This:** [PROJECT-001](../projects/PROJECT-001-[Title].md)
```

### Module Navigation

```markdown
## In This Module

**Completed:**
- [3101: Previous Topic](../3100-attention/3101-[Previous].md) ✅

**Current:**
- [3102: This Topic](../3100-attention/3102-[Current].md) 📍

**Next:**
- [3201: Next Module](../3200-embeddings/3201-[Next].md) ➡️
```

---

## 🎯 Phase Navigation

### Phase Overview

```markdown
## Phase Overview

**Phase [XXXX]: [Phase Name]**

**Modules:**
- **[Module 1](../[module1]/)** - Description
- **[Module 2](../[module2]/)** - Description
- **[Module 3](../[module3]/)** - Description

**Progress:**
- Module 1: ⭐⭐⭐⭐⭐ (100%)
- Module 2: ⭐⭐⭐☆☆ (60%)
- Module 3: ⭐☆☆☆☆ (20%)

**Phase Completion:** ⭐⭐⭐☆☆ (60%)

**Next Phase:** [Phase YYYY](../[phase-yyyy]/)
```

---

## 📚 Volume Navigation

### Volume Structure

```markdown
## Volume [X]: [Volume Name]

**Contents:**
1. [Module 1](../module1/) - Description
2. [Module 2](../module2/) - Description
3. [Module 3](../module3/) - Description

**Estimated Time:** X-Y weeks

**Prerequisites:**
- [Volume X-1](../volumes/VOLUME-[X-1].md) completed
- [Skill list]

**Volume Capstone:** [PROJECT-XXX](../projects/PROJECT-XXX.md)
```

---

## 🔄 Progress Tracking

### Learning Checkpoints

```markdown
## Checkpoint: After This Document

**You Should Be Able To:**
- [ ] Explain [concept] in your own words
- [ ] Implement [technique] from scratch
- [ ] Troubleshoot [common issue]

**Verify Your Knowledge:**
- Complete: [LAB-XXX](../learning-resources/labs/LAB-XXX.md)
- Quiz yourself: [Assessment Guide](../00-META/ASSESSMENT-GUIDE.md)
- Build: [Mini-project](../learning-resources/projects/)

**Ready for Next?**
- If yes → [Next Document](../next/)
- If no → Review [Prerequisite](../prerequisite/)
```

---

## 📱 Quick Navigation Cards

### Topic Cards

```markdown
<details>
<summary><b>📖 Quick Navigation</b></summary>

**Beginner:** Start with [TUTORIAL-001](../tutorials/TUTORIAL-001.md)

**Intermediate:** Try [LAB-002](../learning-resources/labs/LAB-002.md)

**Advanced:** Build [PROJECT-001](../projects/PROJECT-001.md)

**Reference:** [GLOSSARY.md](../00-META/GLOSSARY.md)
</details>
```

---

## 🎯 Call-to-Action Placement

### End of Document

```markdown
---

## 🚀 What's Next?

**Choose Your Path:**

1. **Continue Learning:** [Next Document](../next/)
2. **Practice Skills:** [Related Lab](../labs/)
3. **Build Project:** [Capstone Project](../learning-resources/projects/)
4. **Deep Dive:** [Advanced Topic](../advanced/)

**Need Help?**
- [Troubleshooting](../troubleshooting/)
- [Glossary](../00-META/GLOSSARY.md)
- [Community](https://community.example.com)
```

---

## 📋 Navigation Checklist

Use this checklist for every document:

### Essential Navigation
- [ ] "Previous" link included
- [ ] "Next" link included
- [ ] Related topics listed
- [ ] Prerequisites stated

### Helpful Navigation
- [ ] Deep dive links
- [ ] External resources
- [ ] Progress checkpoint
- [ ] Call-to-action

### Quality Checks
- [ ] All links tested
- [ ] Link text descriptive
- [ ] No broken links
- [ ] Consistent formatting

---

**Last Updated:** 2026-02-04
**Version:** 1.0
