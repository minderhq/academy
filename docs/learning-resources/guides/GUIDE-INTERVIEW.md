---
Document ID: GUIDE-INTERVIEW
Title: INTERVIEW PREPARATION GUIDE
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
Tags: ['career', 'guide', 'llm']
---

# INTERVIEW PREPARATION GUIDE

**For:** Minder Academy graduates preparing for AI Engineering interviews

**Read Time:** 30 minutes

**Last Updated:** 2026-10-08

---

## REALITY CHECK

**The Truth About Interviews:**

- ✅ Technical skills get you the interview
- ✅ Communication gets you the job
- ⚠️ Most candidates fail on communication, not technical skills
- ⚠️ Practice is MORE important than studying

**This guide focuses on:**

1. Technical interview preparation
2. System design for AI systems
3. Behavioral interviews
4. Take-home assignments
5. Mock interviews

---

## Part 1: Technical Interview Prep

### 1.1 Types of Technical Interviews

| Type | Duration | Focus | Preparation |
|------|----------:|-------|-------------|
| **Screening** | 45-60 min | Basic coding + concepts | LeetCode easy + fundamentals |
| **Deep Dive** | 2-4 hours | System design + coding | Practice architectures |
| **Onsite** | 4-6 hours | Multiple rounds | Full day prep |

---

### 1.2 Common Technical Questions

#### Python Fundamentals (Expect 5-10 questions)
```python
# Example: Explain list comprehension vs generator expression
# List comprehension: Creates full list in memory
squares = [x**2 for x in range(1000000)]  # Uses lots of memory

# Generator: Yields one item at a time
squares_gen = (x**2 for x in range(1000000))  # Memory efficient
```

**Practice questions:**

- What's the difference between `==` and `is`?
- Explain GIL in Python
- How does garbage collection work?
- What are decorators and how do they work?

---

#### NumPy/PyTorch (Expect 5-10 questions)
```python
# Example: Explain broadcasting in NumPy
import numpy as np

a = np.array([[1, 2, 3], [4, 5, 6]])  # (2, 3)
b = np.array([10, 20, 30])            # (3,)

result = a + b  # (2, 3) - b is "broadcast" to match a's shape
```

**Practice questions:**

- What's the difference between NumPy array and Python list?
- Explain gradient computation in PyTorch
- How does `autograd` work?
- What's the difference between `view()` and `reshape()`?

---

#### LLM/Transformer Concepts (Expect 10-15 questions)
```python
# Example: Explain scaled dot-product attention
def attention(query, key, value):
    # Scale by sqrt(d_k) to prevent vanishing gradients
    scores = query @ key.T / np.sqrt(query.shape[-1])
    weights = softmax(scores)
    return weights @ value
```

**Practice questions:**

- Explain the transformer architecture
- What's the difference between encoder-only and decoder-only?
- How does positional encoding work?
- What's the KV cache and why is it important?
- Explain LoRA and how it works

---

#### RAG Systems (Expect 5-10 questions)
**Practice questions:**

- How do you choose chunk size for RAG?
- What's the difference between dense and sparse retrieval?
- Explain re-ranking and when to use it
- How do you evaluate RAG systems?
- What are common failure modes in RAG?

---

### 1.3 Coding Challenges (LeetCode Style)

#### Common Patterns for AI Engineers

**1. Sliding Window**
```python
# Example: Find max sum of k consecutive elements
def max_sum_k_consecutive(arr, k):
    if len(arr) < k:
        return 0

    window_sum = sum(arr[:k])
    max_sum = window_sum

    for i in range(len(arr) - k):
        window_sum = window_sum - arr[i] + arr[i + k]
        max_sum = max(max_sum, window_sum)

    return max_sum
```

**2. Hash Maps**
```python
# Example: Find most frequent elements
def top_k_frequent(nums, k):
    count = {}
    for num in nums:
        count[num] = count.get(num, 0) + 1

    return sorted(count.keys(), key=lambda x: -count[x])[:k]
```

**3. Two Pointers**
```python
# Example: Merge sorted arrays
def merge_sorted(arr1, arr2):
    result = []
    i = j = 0

    while i < len(arr1) and j < len(arr2):
        if arr1[i] < arr2[j]:
            result.append(arr1[i])
            i += 1
        else:
            result.append(arr2[j])
            j += 1

    result.extend(arr1[i:])
    result.extend(arr2[j:])
    return result
```

**Practice:**

- LeetCode: Arrays & Hashing (10 problems)
- LeetCode: Two Pointers (5 problems)
- LeetCode: Sliding Window (5 problems)
- Focus: Easy to Medium difficulty

---

## Part 2: System Design Interviews

### 2.1 How System Design Works

**Format:**

1. Clarify requirements (5 min)
2. High-level design (10 min)
3. Deep dive on components (20 min)
4. Trade-offs and discussion (10 min)

**What they're looking for:**

- ✅ Logical thinking
- ✅ Scalability awareness
- ✅ Trade-off analysis
- ✅ Practical experience

---

### 2.2 Common Design Questions

#### Question 1: Design a RAG System

**Requirements:**

- 1M documents, average 5KB each
- 1000 QPS (queries per second)
- Sub-second latency
- 95% accuracy

**High-Level Design:**
```text
┌─────────────┐
 │   Ingest    │
 │   Pipeline  │
 └──────┬──────┘
        │
        ▼
┌─────────────┐
 │  Chunking   │
 │ + Embedding │
 └──────┬──────┘
        │
        ▼
┌─────────────┐
 │ Vector DB   │
 │ (Qdrant)    │
 └──────┬──────┘
        │
        ▼
┌─────────────┐
 │  + Re-rank  │
 └──────┬──────┘
        │
        ▼
┌─────────────┐
 │    LLM      │
 └─────────────┘
```

**Key Components:**

- **Ingest Pipeline:** Async workers for document processing
- **Vector DB:** Qdrant with sharding for scale
- **Cache:** Redis for frequent queries
- **Load Balancer:** nginx or AWS ALB
- **Monitoring:** Prometheus + Grafana

**Trade-offs:**

- Chunk size: Larger = more context, less precise
- Embedding model: Larger = better, slower
- Re-ranking: Better accuracy, more latency

---

#### Question 2: Design an LLM Serving Platform

**Requirements:**

- Support multiple models (Llama, Mistral, etc.)
- 10K concurrent users
- <500ms TTFT (time to first token)
- Auto-scaling

**High-Level Design:**
```text
┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
 │  Client │─▶│ Gateway  │─▶│ Router   │─▶│ Model    │
 └─────────┘  └──────────┘  └──────────┘  │  Server  │
                                           └──────────┘
                                                │
                                                ▼
                                           ┌──────────┐
                                           │  KV      │
                                           │  Cache   │
                                           └──────────┘
```

**Key Components:**

- **API Gateway:** Rate limiting, auth, routing
- **Model Router:** Load balance across instances
- **Model Servers:** vLLM or TGI for inference
- **KV Cache:** Shared cache for efficiency
- **Monitoring:** Track latency, throughput, errors

**Scale Considerations:**

- **Horizontal scaling:** Add more model servers
- **GPU management:** Kubernetes with device plugins
- **Request batching:** Improve throughput
- **Quantization:** Reduce memory, increase speed

---

### 2.3 System Design Checklist

**During the interview:**

- [ ] Ask clarifying questions (scale, latency, consistency)
- [ ] Propose high-level architecture
- [ ] Identify bottlenecks
- [ ] Discuss scaling strategies
- [ ] Mention trade-offs explicitly
- [ ] Talk about monitoring and observability
- [ ] Consider failure modes and recovery

---

## Part 3: Behavioral Interviews

### 3.1 STAR Method

**Structure your answers:**

| Component | What | Time |
|-----------|------|------|
| **S**ituation | Context, background | 30 sec |
| **T**ask | What you needed to do | 30 sec |
| **A**ction | What YOU did (not "we") | 1-2 min |
| **R**esult | Outcome, metrics, impact | 30 sec |

---

### 3.2 Common Behavioral Questions

#### Project Experience
- "Tell me about a challenging AI project you built."
- "Describe a time you had to learn a new technology quickly."
- "Tell me about a time your model didn't perform as expected."

#### Problem Solving
- "Describe a bug you found and how you fixed it."
- "Tell me about a time you had to optimize code for performance."
- "Describe a situation where you had incomplete requirements."

#### Teamwork
- "Tell me about a time you disagreed with a teammate."
- "Describe how you handle code reviews."
- "Tell me about a time you had to explain technical concepts to non-technical stakeholders."

#### Leadership (Mid/Senior roles)
- "Tell me about a time you mentored a junior engineer."
- "Describe a technical decision you led."
- "Tell me about a time you had to say no to a feature request."

---

### 3.3 Answer Templates

#### Template 1: Challenging Project
```text
**Situation:** "In my previous role, we needed to build a RAG system
for 100K legal documents."

**Task:** "I was responsible for the architecture and implementation.
The challenge was achieving both accuracy and speed."

**Action:** "I chose Qdrant for vector storage, implemented hybrid
search with re-ranking, and optimized chunking strategies. I also
built an evaluation framework to measure accuracy."

**Result:** "We achieved 87% accuracy with sub-second latency. The system
now handles 10K queries per day and reduced legal research time by 60%."
```

#### Template 2: Learning Quickly
```text
**Situation:** "We needed to implement LoRA fine-tuning but I had no
prior experience."

**Task:** "I had to learn the technique and implement it within 2 weeks."

**Action:** "I studied the Hugging Face PEFT library, read the LoRA paper,
and built a prototype. I also consulted with the team and got feedback
on my approach."

**Result:** "I successfully implemented fine-tuning in 10 days and
we achieved a 15% improvement in domain-specific benchmarks."
```

---

## Part 4: Take-Home Assignments

### 4.1 Common Assignment Types

| Type | Duration | Focus |
|------|----------:|-------|
| **RAG Implementation** | 4-8 hours | Vector search, retrieval |
| **Fine-tuning** | 6-10 hours | LoRA, data preparation |
| **API Development** | 3-6 hours | FastAPI, deployment |
| **System Design** | 2-4 hours | Architecture, documentation |
| **Debug Challenge** | 1-2 hours | Problem solving |

---

### 4.2 Assignment Tips

**DO:**

- [ ] Read requirements carefully (twice!)
- [ ] Ask clarifying questions
- [ ] Write clean, documented code
- [ ] Include a README with setup instructions
- [ ] Test your solution before submitting
- [ ] Handle edge cases
- [ ] Include basic error handling

**DON'T:**

- [ ] Over-engineer simple solutions
- [ ] Skip documentation
- [ ] Ignore error handling
- [ ] Submit untested code
- [ ] Copy-paste from tutorials without understanding

---

### 4.3 Example: RAG Assignment

**Requirement:** "Build a simple RAG system that can answer questions from PDF documents."

**Solution Structure:**
```text
project/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app
│   ├── rag.py            # RAG logic
│   └── models.py         # Pydantic models
├── data/                 # Sample PDFs
├── tests/
│   └── test_rag.py
├── README.md             # Setup + usage
├── pyproject.toml        # Project manifest
├── uv.lock               # Locked dependency graph
└── docker-compose.yml    # Easy deployment
```

**Key Components to Demonstrate:**

1. Document ingestion (PDF parsing)
2. Chunking strategy
3. Embedding and vector storage
4. Retrieval and generation
5. API endpoints
6. Basic error handling

---

## Part 5: Mock Interviews

### 5.1 Self-Practice

**Technical (Daily, 30 min):**

- Pick 1 LeetCode problem
- Solve without looking at solution
- Time yourself (20 min max)
- Review solution and optimize

**Concepts (Daily, 15 min):**

- Pick 1 concept (e.g., attention)
- Explain it out loud
- Draw diagrams on whiteboard
- Practice with simple examples

**System Design (Weekly, 1 hour):**

- Pick 1 design question
- Design solution in 30 min
- Review trade-offs
- Get feedback from peers

---

### 5.2 Peer Mock Interviews

**Setup:**

- Find a study partner or use online platforms
- Schedule 2-3 sessions per week
- Rotate roles (interviewer/interviewee)
- Record and review sessions

**Platforms:**

- [Pramp](https://www.pramp.com/) - Free peer interviews
- [Interviewing.io](https://interviewing.io/) - Mock coding interviews
- [Discord/Slack communities] - AI/ML study groups

---

### 5.3 Professional Mock Interviews

**When to use:**

- Before onsite interviews
- For senior roles
- If you lack confidence

**Services:**

- [AlgoExpert](https://www.algoexpert.io/) - Paid mock interviews
- [Interview Kickstart](https://www.interviewkickstart.com/) - Professional coaching
- [Exponent](https://www.tryexponent.com/) - System design practice

---

## Part 6: Interview Day Tips

### 6.1 Before the Interview

**1 Day Before:**

- [ ] Review your portfolio projects
- [ ] Practice explaining your resume
- [ ] Prepare questions to ask them
- [ ] Test your internet connection
- [ ] Set up quiet environment

**Questions to Ask Them:**

- "What does the day-to-day work look like?"
- "How does the team handle technical disagreements?"
- "What's the biggest challenge the team is facing?"
- "How do you measure success for this role?"
- "What's the onboarding process like?"

---

### 6.2 During the Interview

**Technical:**

- Think out loud
- Ask clarifying questions
- Start with brute force, then optimize
- Test your code with examples
- Admit when you don't know something

**Behavioral:**

- Use STAR method
- Be specific (use numbers)
- Focus on YOUR contributions
- Show enthusiasm
- Ask follow-up questions

**System Design:**

- Clarify requirements first
- Draw diagrams
- Discuss trade-offs
- Mention scalability
- Talk about monitoring

---

### 6.3 After the Interview

**Same Day:**

- [ ] Send thank you note (within 24 hours)
- [ ] Write down questions you were asked
- [ ] Note areas to improve

**Thank You Template:**
```text
Subject: Thank you - [Role] interview - [Your Name]

Hi [Interviewer Name],

Thank you for taking the time to interview me for the
[Role] position. I enjoyed discussing [specific topic] and
learning more about the team's work on [project].

I'm particularly excited about [aspect of role] and believe
my experience with [your relevant skill] would be valuable.

Looking forward to hearing from you.

Best,
[Your Name]
[LinkedIn]
[GitHub]
```

---

## Part 7: Salary Negotiation

### 7.1 When to Negotiate

**Best Times:**

- ✅ After offer but before accepting
- ✅ After they mention salary first
- ❌ Never during initial screening
- ❌ Never before they say "we want you"

---

### 7.2 Research First

**Know your market value:**

- [Levels.fyi](https://www.levels.fyi/) - Salary data
- [Glassdoor](https://www.glassdoor.com/) - Company salaries
- [Reddit r/cscareerquestions](https://www.reddit.com/r/cscareerquestions/) - Industry insights

**Total Compensation = Base + Bonus + Equity**

---

### 7.3 Negotiation Script

```text
"Thank you so much for the offer! I'm really excited about
joining the team and working on [specific project].

Based on my research and the value I can bring, I was hoping
for a base salary of [10-20% above offer]. Given my experience
with [your specific skill] and [relevant achievement], I believe
this is fair.

Is there flexibility here?"
```

**If they say no:**
```text
"I understand. Could we discuss other aspects of compensation?
Perhaps equity, signing bonus, or additional PTO?"
```

---

### 7.4 Red Flags

**Walk away if:**

- Salary is below market by 20%+
- No equity for startup role
- No clear growth path
- Poor culture during interviews
- They won't discuss compensation

---

## Part 8: Quick Reference

### Technical Concepts to Review

**NumPy:**

- Array creation and manipulation
- Broadcasting rules
- Matrix multiplication
- Statistical operations

**PyTorch:**

- Tensor operations
- Autograd and gradients
- Model building
- Training loops

**LLMs:**

- Transformer architecture
- Attention mechanisms
- Tokenization
- Generation strategies

**RAG:**

- Vector databases
- Chunking strategies
- Retrieval methods
- Evaluation metrics

---

### Common LeetCode Patterns

1. **Sliding Window** - Subarray problems
2. **Two Pointers** - Array manipulation
3. **Hash Maps** - Counting, caching
4. **Stack/Queue** - Parsing, ordering
5. **Binary Search** - Sorted data
6. **DFS/BFS** - Graphs, trees
7. **Recursion** - Divide and conquer

---

### System Design Checklist

**Requirements:**

- [ ] Scale (users, data, QPS)
- [ ] Latency requirements
- [ ] Consistency needs
- [ ] Budget constraints

**Components:**

- [ ] Load balancer
- [ ] API gateway
- [ ] Application servers
- [ ] Database (vector + relational)
- [ ] Caching layer
- [ ] Monitoring

**Trade-offs:**

- [ ] CAP theorem implications
- [ ] SQL vs NoSQL
- [ ] Strong vs eventual consistency
- [ ] Cost vs performance

---

## Conclusion

**Remember:**

- ✅ Preparation beats talent
- ✅ Practice makes confident
- ✅ Authenticity wins over perfection
- ✅ Every interview is learning experience

**Final Checklist:**

- [ ] Complete technical preparation
- [ ] Practice system design
- [ ] Prepare behavioral stories
- [ ] Do 3+ mock interviews
- [ ] Research target companies
- [ ] Prepare questions to ask
- [ ] Practice salary negotiation

**Good luck! You've got this!**

---

**Related Resources:**

- [GUIDE-CAREER.md](./GUIDE-CAREER.md) - Career planning
- [GUIDE-RESUME.md](./GUIDE-RESUME.md) - Resume templates

**© 2026 Minder Academy. All rights reserved.**
