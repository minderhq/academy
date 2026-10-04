---
Document ID: UC-002
Title: "UC-002: RAG (Retrieval-Augmented Generation) Practical Use Cases"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Intermediate
Tags: ['use-case', 'rag', 'retrieval']
---

# UC-002: RAG (Retrieval-Augmented Generation) Practical Use Cases

## Overview

This document provides comprehensive practical use cases for RAG systems, explaining when to use RAG vs fine-tuning, with real-world implementation examples.

---

## Part 1: RAG vs Fine-Tuning vs Pure LLM

### Decision Matrix

| Scenario | Pure LLM | RAG | Fine-Tuning |
|----------|----------|-----|-------------|
| **General Knowledge** | ✅ Best Choice | ⚠️ Overkill | ❌ Not Needed |
| **Private Data** | ❌ No Access | ✅ Best Choice | ⚠️ Possible |
| **Recent Information** | ❌ Knowledge Cutoff | ✅ Best Choice | ⚠️ Requires Re-training |
| **Specific Format** | ⚠️ Inconsistent | ⚠️ Possible | ✅ Best Choice |
| **Domain Vocabulary** | ⚠️ Generic Terms | ⚠️ Possible | ✅ Best Choice |
| **Fact Accuracy** | ❌ Hallucinates | ✅ Grounded | ⚠️ May Hallucinate |
| **Implementation Speed** | ✅ Immediate | ⚠️ Moderate | ❌ Time-Consuming |
| **Cost** | ✅ Lowest | ⚠️ Moderate | ❌ Highest |

---

## Part 2: Real-World RAG Use Cases

### Use Case 1: Enterprise Knowledge Base Assistant

**Business Problem:**
Employees can't find information across thousands of internal documents (policies, procedures, specs). Traditional search returns irrelevant documents.

**RAG Solution:**

```python
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

class EnterpriseKnowledgeAssistant:
    """
    RAG-based assistant for enterprise knowledge
    """

    def __init__(self):
        # Initialize embedding model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # Initialize vector store
        # langchain_qdrant: QdrantVectorStore takes an explicit client and
        # singular `embedding=` (the old Qdrant class defaulted to localhost).
        qdrant_client = QdrantClient(url="http://localhost:6333")
        self.vectorstore = QdrantVectorStore(
            client=qdrant_client,
            collection_name="enterprise_kb",
            embedding=self.embeddings
        )
        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 4}  # Retrieve top 4 documents
        )

        # Initialize LLM
        model_id = "meta-llama/Meta-Llama-3-8B-Instruct"
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map="auto",
            load_in_4bit=True  # Works on any 11GB+ VRAM GPU
        )

        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=512,
            temperature=0.1  # Low temperature for factual responses
        )

        self.llm = HuggingFacePipeline(pipeline=pipe)

        # Create RAG chain - LangChain 1.x composes LCEL steps
        # instead of the legacy RetrievalQA wrapper.
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Answer the question using only the provided "
                       "context. Cite the documents you used."),
            ("human", "Context:\n{context}\n\nQuestion: {question}"),
        ])

        def format_docs(docs):
            return "\n\n".join(d.page_content for d in docs)

        self.rag_chain = (
            RunnableParallel(
                context=self.retriever | format_docs,
                question=RunnablePassthrough(),
            )
            | prompt
            | self.llm
            | StrOutputParser()
        )

    def query(self, question):
        """Answer question with sources"""
        docs = self.retriever.invoke(question)
        answer = self.rag_chain.invoke({"question": question})

        return {
            "answer": answer,
            "sources": [
                {
                    "document": doc.metadata["title"],
                    "page": doc.metadata["page"],
                    "relevance": doc.metadata["score"]
                }
                for doc in docs
            ]
        }
```

**Real-World Usage:**

```text
# Employee query
query = "What's our remote work policy for IT department?"

# Response
{
    "answer": "According to the IT Department Remote Work Policy (2024),
    IT staff can work remotely up to 3 days per week with manager approval.
    Core hours are 10 AM - 3 PM EST. On-call rotation requires on-site
    presence. See policy IT-HR-024 for complete details.",

    "sources": [
        {"document": "IT-Remote-Work-Policy-2024.pdf", "page": 2},
        {"document": "HR-Handbook-2024.pdf", "page": 45}
    ]
}
```

**Business Impact:**
- 70% reduction in helpdesk tickets
- 50% faster employee onboarding
- 90% employee satisfaction with information access

**Why RAG and NOT Fine-Tuning:**
- Documents updated frequently (weekly)
- Need source citations
- Must be accurate
- Limited training data for fine-tuning

---

### Use Case 2: Customer Support with Context

**Business Problem:**
Support agents waste time searching for customer information, order history, and product details to answer questions.

**RAG Solution:**

```python
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient

class CustomerSupportRAG:
    """
    RAG system that retrieves customer context + product info
    """

    def __init__(self):
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        # langchain_qdrant: QdrantVectorStore replaced the old Qdrant class
        client = QdrantClient(url="http://localhost:6333")
        self.customer_store = QdrantVectorStore(
            client=client,
            collection_name="customer_history",
            embedding=embeddings,
        )
        self.product_store = QdrantVectorStore(
            client=client,
            collection_name="product_docs",
            embedding=embeddings,
        )
        self.policy_store = QdrantVectorStore(
            client=client,
            collection_name="support_policies",
            embedding=embeddings,
        )

    def answer_customer_query(self, customer_id, query):
        """
        Answer customer query with full context
        """

        # Step 1: Retrieve customer context
        customer_context = self._get_customer_context(customer_id)

        # Step 2: Retrieve relevant product info
        product_info = self.product_store.similarity_search(
            query, k=3
        )

        # Step 3: Retrieve relevant policies
        policy_info = self.policy_store.similarity_search(
            query, k=2
        )

        # Step 4: Build enhanced prompt
        prompt = f"""
        You are a customer support agent.

        CUSTOMER CONTEXT:
        - Name: {customer_context['name']}
        - Tier: {customer_context['tier']}
        - Recent Orders: {customer_context['recent_orders']}
        - Previous Issues: {customer_context['previous_issues']}

        RELEVANT PRODUCT INFORMATION:
        {self._format_docs(product_info)}

        RELEVANT POLICIES:
        {self._format_docs(policy_info)}

        CUSTOMER QUERY: {query}

        Provide a helpful, personalized response. Reference specific
        policies when applicable.
        """

        # Step 5: Generate response
        response = self.llm.generate(prompt)

        return response

    def _get_customer_context(self, customer_id):
        """Retrieve customer-specific context"""

        # This could be a hybrid approach:
        # - Exact lookup from traditional DB (transactions)
        # - Vector search for interaction history summaries

        customer_data = postgres.query(
            "SELECT * FROM customers WHERE id = %s",
            (customer_id,)
        )

        # Get recent interaction summaries (vector search)
        recent_interactions = self.customer_store.similarity_search(
            f"Recent issues for customer {customer_id}",
            k=5,
            filter={"customer_id": customer_id}
        )

        return {
            "name": customer_data['name'],
            "tier": customer_data['tier'],
            "recent_orders": customer_data['recent_orders'],
            "previous_issues": [doc.payload for doc in recent_interactions]
        }
```

**Real-World Scenario:**

```text
# Customer query
query = "My order #12345 is delayed, what can you do?"

# System retrieves:
# - Customer: Gold tier, spends $500/month, never complained before
# - Order: #12345, premium item, shipped 3 days ago, tracking shows delay
# - Policy: "Gold members get 20% refund for delays > 2 days"

# Generated response:
"Hi Sarah! I see your premium order #12345 is experiencing a delay.
As a Gold tier member, I've immediately processed a 20% refund
($47.99) to your original payment method. Your package is expected
to arrive by Friday. I've also flagged this with our shipping partner
for priority handling. Is there anything else I can help with?"
```

**Business Impact:**
- 60% reduction in average handle time
- 40% increase in first-contact resolution
- 35% improvement in customer satisfaction

---

### Use Case 3: Technical Documentation Assistant

**Business Problem:**
Developers struggle to find relevant code examples, API usage patterns, and troubleshooting guides across extensive documentation.

**RAG Solution with Code-Aware Retrieval:**

```python
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# LangChain 1.x: CodeLoader is gone - load code with
# GenericLoader + LanguageParser (langchain_community).
class DocumentationRAG:
    """
    RAG specialized for technical documentation
    """

    def __init__(self):
        # Use code-aware embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="microsoft/codebert-base"
        )

        # Different collections for different doc types
        self.collections = {
            "api_docs": self._init_collection("api_docs"),
            "code_examples": self._init_collection("code_examples"),
            "troubleshooting": self._init_collection("troubleshooting"),
            "changelog": self._init_collection("changelog")
        }

    def index_repository_docs(self, repo_path):
        """Index documentation from code repository"""

        # Load different document types
        docs = []

        # API documentation (Markdown)
        docs.extend(self._load_markdown_docs(f"{repo_path}/docs/api"))

        # Code examples (Python files)
        docs.extend(self._load_code_examples(f"{repo_path}/examples"))

        # Troubleshooting guides
        docs.extend(self._load_markdown_docs(f"{repo_path}/docs/troubleshooting"))

        # Split intelligently
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n## ", "\n## ", "\n### ", "\n```\n", "\n"]
        )

        splits = splitter.split_documents(docs)

        # Index with metadata
        for split in splits:
            # Detect doc type
            doc_type = self._detect_doc_type(split)

            # Create embedding
            embedding = self.embeddings.embed_query(split.page_content)

            # Store
            self.collections[doc_type].add_documents([split])

    def answer_technical_question(self, question):
        """
        Answer technical question with code examples
        """

        # Determine query type
        query_type = self._classify_query(question)

        # Retrieve from relevant collection
        docs = self.collections[query_type].similarity_search(
            question, k=5
        )

        # Build prompt with code formatting
        prompt = f"""
        You are a technical documentation assistant.

        RELEVANT DOCUMENTATION:
        {self._format_technical_docs(docs)}

        QUESTION: {question}

        Provide a clear answer with:
        1. Direct answer to the question
        2. Code examples if applicable
        3. Links to relevant documentation
        4. Common pitfalls to avoid

        Format code blocks with ```language
        """

        # LangChain 1.x: .invoke replaces the removed .generate
        response = self.llm.invoke(prompt)
        return response.content

    def _classify_query(self, question):
        """Determine which collection to search"""

        # Simple classification using keyword matching
        # In production, use a classifier model
        if any(word in question.lower() for word in ["example", "how to", "code"]):
            return "code_examples"
        elif any(word in question.lower() for word in ["error", "fix", "troubleshoot"]):
            return "troubleshooting"
        elif any(word in question.lower() for word in ["new", "release", "version"]):
            return "changelog"
        else:
            return "api_docs"
```

**Real-World Usage:**

````python
# Developer query
question = "How do I authenticate with the API using OAuth2?"

# Retrieved docs include:
# - API reference for /auth/oauth
# - Complete code example in Python
# - Common authentication errors and fixes

# Response:
"""
To authenticate with the API using OAuth2:

1. Register your application to get client credentials
2. Request authorization code
3. Exchange for access token

```python
import requests

# Step 1: Get authorization URL
auth_url = "[https://api.example.com/oauth/authorize](https://api.example.com/oauth/authorize)"
params = {
    "client_id": YOUR_CLIENT_ID,
    "redirect_uri": "[https://yourapp.com/callback](https://yourapp.com/callback)",
    "response_type": "code"
}

# Step 2: Exchange code for token
token_response = requests.post(
    "[https://api.example.com/oauth/token](https://api.example.com/oauth/token)",
    data={
        "grant_type": "authorization_code",
        "code": auth_code,
        "client_id": YOUR_CLIENT_ID,
        "client_secret": YOUR_CLIENT_SECRET
    }, timeout=30
)

access_token = token_response.json()["access_token"]
```

**Common Pitfalls:**
- Using client credentials in frontend code (security risk)
- Not handling token expiration (tokens last 1 hour)
- Forgetting to include redirect URI in registration

**Documentation:** [API Authentication Guide](https://docs.example.com/auth)
"""
````

---

## Use Case 4: Legal Contract Analysis

**Business Problem:**
Lawyers need to analyze contracts for specific clauses, risks, and compliance issues across thousands of documents.

**RAG Solution with Clause-Level Retrieval:**

```python
from qdrant_client import QdrantClient

class LegalContractRAG:
    """
    RAG system for contract analysis
    """

    def __init__(self):
        # Use legal-domain embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="nlpaueb/legal-bert-base-uncased"
        )

        # langchain_qdrant: QdrantVectorStore replaced the old Qdrant class
        self.contract_store = QdrantVectorStore(
            client=QdrantClient(url="http://localhost:6333"),
            collection_name="contract_clauses",
            embedding=self.embeddings
        )

    def index_contract(self, contract_path):
        """
        Index contract at clause level for granular retrieval
        """

        # Parse contract
        contract = self._parse_contract(contract_path)

        # Split into clauses
        clauses = self._split_into_clauses(contract)

        # Index each clause
        for clause in clauses:
            # Create embedding
            embedding = self.embeddings.embed_query(clause["text"])

            # Store with metadata
            self.contract_store.add_texts(
                texts=[clause["text"]],
                metadatas=[{
                    "contract_id": contract["id"],
                    "clause_type": clause["type"],
                    "clause_number": clause["number"],
                    "party": contract["party"],
                    "date": contract["date"],
                    "jurisdiction": contract["jurisdiction"]
                }]
            )

    def analyze_contract(self, contract_text, analysis_type):
        """
        Analyze contract for specific risks or provisions
        """

        # Build analysis prompt
        if analysis_type == "force_majeure":
            prompt_template = "Review these Force Majeure clauses and identify risks"
        elif analysis_type == "termination":
            prompt_template = "Compare these termination clauses"
        elif analysis_type == "compliance":
            prompt_template = "Check these clauses for GDPR compliance"

        # Retrieve similar clauses from other contracts
        similar_clauses = self.contract_store.similarity_search(
            contract_text,
            k=10,
            filter={"clause_type": analysis_type}
        )

        # Build prompt
        prompt = f"""
        {prompt_template}

        CURRENT CONTRACT CLAUSE:
        {contract_text}

        SIMILAR CLAUSES FROM OTHER CONTRACTS:
        {self._format_clauses(similar_clauses)}

        Provide:
        1. Analysis of current clause
        2. Comparison with industry standards
        3. Identified risks
        4. Suggested improvements
        """

        analysis = self.llm.generate(prompt)
        return analysis
```

**Real-World Usage:**

```python
# Lawyer request
clause_text = """
Force Majeure: Neither party shall be liable for delays due to
circumstances beyond reasonable control.
"""

# Analysis
{
    "analysis": "This clause is vague and provides minimal protection.",
    "comparison": "Industry standard clauses enumerate specific events",
    "risks": [
        "No explicit pandemic coverage",
        "No government action coverage",
        "No notice period requirements"
    ],
    "suggestions": """
    Consider expanding to:
    'Force Majeure includes but is not limited to: pandemics,
    epidemics, government actions, natural disasters, wars,
    and strikes. Affected party must notify within 5 days.'
    """
}
```

---

### Use Case 5: Educational Content Generator

**Business Problem:**
Educators need to create customized learning materials, quizzes, and explanations based on curriculum standards.

**RAG Solution:**

```python
from qdrant_client import QdrantClient

class EducationalRAG:
    """
    RAG system for educational content generation
    """

    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )

        # Specialized collections
        # langchain_qdrant: QdrantVectorStore replaced the old Qdrant class
        client = QdrantClient(url="http://localhost:6333")
        self.curriculum = QdrantVectorStore(
            client=client,
            collection_name="curriculum_standards",
            embedding=self.embeddings,
        )
        self.textbooks = QdrantVectorStore(
            client=client,
            collection_name="textbooks",
            embedding=self.embeddings,
        )
        self.assessments = QdrantVectorStore(
            client=client,
            collection_name="assessments",
            embedding=self.embeddings,
        )

    def generate_lesson_content(self, topic, grade_level, standards):
        """
        Generate lesson content aligned with standards
        """

        # Retrieve relevant curriculum standards
        relevant_standards = self.curriculum.similarity_search(
            f"{topic} {grade_level}",
            k=5,
            filter={"standard": standards}
        )

        # Retrieve textbook content
        textbook_content = self.textbooks.similarity_search(
            topic,
            k=3,
            filter={"grade_level": grade_level}
        )

        # Retrieve example assessments
        example_assessments = self.assessments.similarity_search(
            f"{topic} quiz questions",
            k=2
        )

        # Generate lesson
        prompt = f"""
        Create a lesson plan for: {topic}
        Grade Level: {grade_level}

        ALIGNMENT STANDARDS:
        {self._format_standards(relevant_standards)}

        REFERENCE MATERIAL:
        {self._format_textbook_content(textbook_content)}

        EXAMPLE ASSESSMENTS:
        {self._format_assessments(example_assessments)}

        Generate:
        1. Learning objectives (aligned to standards)
        2. Lesson outline with timing
        3. Key concepts to cover
        4. Class activity ideas
        5. Assessment questions (multiple choice + open-ended)
        6. Differentiation strategies
        """

        lesson = self.llm.generate(prompt)
        return lesson
```

**Real-World Output:**

```python
# Input
topic = "Photosynthesis"
grade_level = "7th Grade"
standards = ["NGSS-MS-LS1-6"]

# Output (abbreviated)
"""
## Lesson Plan: Photosynthesis
**Grade:** 7th Grade | **Duration:** 90 minutes

### Learning Objectives (Aligned to NGSS-MS-LS1-6)
1. Students will explain how plants use energy from sunlight
   to convert water and carbon dioxide into sugar and oxygen
2. Students will diagram the photosynthesis equation
3. Students will identify factors affecting photosynthesis rate

### Lesson Outline

**Warm-up (10 min): What do plants need to grow?**
- KWL chart on board
- Discussion on plant needs

**Direct Instruction (25 min): Photosynthesis Process**
- Show diagram of chloroplast
- Explain light-dependent reactions
- Explain Calvin cycle
- Write equation: 6CO₂ + 6H₂O + light → C₆H₁₂O₆ + 6O₂

**Guided Practice (20 min): Interactive Diagram**
- Students label photosynthesis diagram
- Color-code reactants and products

**Independent Practice (20 min): Virtual Lab**
- PhET simulation: Plant growth variables
- Record data on light intensity vs. oxygen production

**Assessment (15 min): Exit Ticket**

**Multiple Choice:**
1. What are the reactants in photosynthesis?
   A) Sugar and oxygen
   B) Carbon dioxide and water ✓
   C) Nitrogen and phosphorus
   D) Glucose and carbon dioxide

2. Where does photosynthesis occur?
   A) Mitochondria
   B) Nucleus
   C) Chloroplast ✓
   D) Ribosome

**Open-Ended:**
3. Explain what would happen to a plant if it was kept in
   complete darkness for one week. Use photosynthesis
   vocabulary in your answer.

**Differentiation:**
- Advanced: Research C3, C4, CAM plant variations
- Support: Word bank for diagram labeling
- ELL: Bilingual glossary, visual vocabulary cards
"""
```

---

## Part 3: Hybrid RAG Approaches

### RAG + Fine-Tuning (Best of Both)

```python
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient

class HybridRAG:
    """
    Combine RAG with fine-tuned model for domain-specific language
    """

    def __init__(self):
        # Fine-tuned model for domain vocabulary
        self.llm = self._load_finetuned_model()

        # RAG for factual grounding
        # langchain_qdrant: QdrantVectorStore replaced the old Qdrant class
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.retriever = QdrantVectorStore(
            client=QdrantClient(url="http://localhost:6333"),
            collection_name="domain_docs",
            embedding=self.embeddings,
        )

    def query(self, question):
        # Retrieve context
        context = self.retriever.similarity_search(question, k=3)

        # Generate with fine-tuned model
        response = self.llm.generate(
            question,
            context=context,
            temperature=0.2
        )

        return response
```

### GraphRAG (Knowledge Graph + RAG)

```python
from qdrant_client import QdrantClient
class GraphRAG:
    """
    Combine knowledge graph relationships with vector search
    """

    def __init__(self):
        self.neo4j = Neo4jClient()
        self.qdrant = QdrantClient()

    def query_with_context(self, question):
        # Step 1: Vector search for relevant documents
        docs = self.qdrant.search(question)

        # Step 2: Extract entities
        entities = self._extract_entities(question)

        # Step 3: Traverse knowledge graph
        related_entities = self.neo4j.get_related(entities)

        # Step 4: Generate response with both
        response = self.llm.generate(
            question,
            vector_context=docs,
            graph_context=related_entities
        )

        return response
```

---

## Part 4: RAG Implementation Patterns

### Pattern 1: Stuffing (Simple)

```python
# Stuff all retrieved documents into one prompt
context = "\n\n".join([doc.page_content for doc in retrieved_docs])
prompt = f"Context: {context}\n\nQuestion: {query}"
```

### Pattern 2: Map-Reduce (Large Documents)

```python
# Process each document separately, then combine
summaries = []
for doc in retrieved_docs:
    summary = llm.summarize(doc)
    summaries.append(summary)

final_answer = llm.synthesize(query, summaries)
```

### Pattern 3: Refine (Iterative)

```python
# Iteratively refine answer
answer = "Initial answer"
for doc in retrieved_docs:
    answer = llm.refine(answer, doc.page_content, query)
```

---

## Part 5: RAG vs Alternatives Decision Guide

### Use RAG When:

✅ You have documents that need to be referenced
✅ Information changes frequently
✅ You need source citations
✅ Accuracy is critical
✅ You have limited training data
✅ Quick implementation is needed

### Use Fine-Tuning When:

✅ You need specific response format/style
✅ Domain has unique vocabulary
✅ You have lots of domain-specific training data
✅ Knowledge is relatively stable
✅ You want domain-specialized model

### Use Pure LLM When:

✅ Questions are general knowledge
✅ Creativity is more important than accuracy
✅ No specific documents need to be referenced
✅ Cost must be minimized

---

## Part 6: Performance Optimization

### Retrieval Optimization

```python
class OptimizedRetrieval:
    """
    Improve RAG retrieval performance
    """

    def __init__(self):
        self.embedder = SentenceTransformer('multi-qa-mpnet-base-dot-v1')
        self.reranker = CrossEncoder('ms-marco-MiniLM-L-6-v2')

    def retrieve(self, query, top_k=100):
        # Step 1: Initial retrieval (fast, broad)
        candidates = self.vector_store.search(query, k=top_k)

        # Step 2: Rerank (accurate, narrow)
        reranked = self.reranker.rank(query, candidates)

        # Step 3: Return top N
        return reranked[:10]
```

### Context Window Optimization

```python
# Calculate context usage
def estimate_tokens(text):
    return len(text.split()) * 1.3  # Rough estimate

# Ensure you don't exceed context limit
max_context = 4096  # For Llama 2 7B
query_tokens = estimate_tokens(query)
available_for_docs = max_context - query_tokens - 512  # Reserve for response

# Adjust k based on available tokens
if available_for_docs < 1000:
    k = 2  # Fewer documents
else:
    k = 5  # More documents
```

---

## Next Steps

- **[UC-003: Agent Applications](./UC-003-Agent-Applications.md)**
