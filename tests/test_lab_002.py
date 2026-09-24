"""
Tests for LAB-002: RAG Implementation with Qdrant
"""

import pytest
import requests
from pathlib import Path


@pytest.mark.rag
class TestLab002RAGBasics:
    """Test Exercise 1: RAG Fundamentals"""

    def test_lab_file_exists(self, labs_root):
        """Test that LAB-002 file exists"""
        lab_files = list(labs_root.glob("LAB-002-*.md"))
        assert len(lab_files) > 0, "LAB-002 file not found"

    def test_solution_file_exists(self, solutions_root):
        """Test that SOLUTION-LAB-002 file exists"""
        solution_files = list(solutions_root.glob("SOLUTION-LAB-002-*.md"))
        assert len(solution_files) > 0, "SOLUTION-LAB-002 file not found"


@pytest.mark.rag
@pytest.mark.qdrant
class TestLab002QdrantSetup:
    """Test Exercise 1: Qdrant Setup"""

    @pytest.fixture
    def qdrant_url(self):
        """Qdrant URL (configurable)"""
        import os
        return os.getenv("QDRANT_URL", "http://localhost:6333")

    def test_qdrant_health_check(self, qdrant_url):
        """Test that Qdrant is accessible"""
        try:
            response = requests.get(f"{qdrant_url}/", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "title" in data
            assert "Qdrant" in data.get("title", "")
        except requests.exceptions.ConnectionError:
            pytest.skip("Qdrant not accessible. Start with: docker run -p 6333:6333 qdrant/qdrant")

    def test_qdrant_collections_list(self, qdrant_url):
        """Test listing collections"""
        try:
            response = requests.get(f"{qdrant_url}/collections", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert "result" in data or "status" in data
        except requests.exceptions.ConnectionError:
            pytest.skip("Qdrant not accessible")

    def test_create_test_collection(self, qdrant_url):
        """Test creating a collection"""
        collection_name = "test_lab_002"

        # First, try to delete if exists
        try:
            requests.delete(f"{qdrant_url}/collections/{collection_name}", timeout=5)
        except Exception:
            pass

        # Create collection
        payload = {
            "vectors": {
                "size": 384,
                "distance": "Cosine"
            }
        }

        try:
            response = requests.put(
                f"{qdrant_url}/collections/{collection_name}",
                json=payload,
                timeout=5
            )

            # Cleanup
            requests.delete(f"{qdrant_url}/collections/{collection_name}", timeout=5)

            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Qdrant not accessible")


@pytest.mark.rag
@pytest.mark.embeddings
class TestLab002Embeddings:
    """Test Exercise 2: Embedding Generation"""

    @pytest.fixture
    def embedding_model(self):
        """Embedding model URL"""
        import os
        return os.getenv(
            "EMBEDDING_URL",
            "http://localhost:11434/api/embeddings"
        )

    def test_embedding_generation(self, embedding_model):
        """Test generating embeddings"""
        try:
            payload = {
                "model": "nomic-embed-text",
                "prompt": "This is a test sentence for embedding."
            }

            response = requests.post(
                embedding_model,
                json=payload,
                timeout=30
            )

            if response.status_code != 200:
                pytest.skip("Embedding model not available")

            data = response.json()
            assert "embedding" in data
            assert isinstance(data["embedding"], list)
            assert len(data["embedding"]) > 0

        except requests.exceptions.ConnectionError:
            pytest.skip("Embedding service not accessible")

    def test_embedding_dimensions(self, embedding_model):
        """Test that embeddings have correct dimensions"""
        try:
            payload = {
                "model": "nomic-embed-text",
                "prompt": "Test"
            }

            response = requests.post(
                embedding_model,
                json=payload,
                timeout=30
            )

            if response.status_code != 200:
                pytest.skip("Embedding model not available")

            data = response.json()
            embedding = data.get("embedding", [])
            # Common embedding dimensions: 384, 768, 1536
            assert len(embedding) in [384, 768, 1536]

        except requests.exceptions.ConnectionError:
            pytest.skip("Embedding service not accessible")


@pytest.mark.rag
@pytest.mark.integration
class TestLab002RAGPipeline:
    """Test Exercise 3: Complete RAG Pipeline"""

    @pytest.fixture
    def rag_components(self):
        """Check if RAG components are available"""
        import os
        return {
            "qdrant": os.getenv("QDRANT_URL", "http://localhost:6333"),
            "llm": os.getenv("OLLAMA_URL", "http://localhost:11434"),
            "embeddings": os.getenv("EMBEDDING_URL", "http://localhost:11434/api/embeddings")
        }

    def test_qdrant_upsert(self, rag_components):
        """Test inserting vectors into Qdrant"""
        collection_name = "test_rag_upsert"

        # Create collection
        try:
            create_payload = {
                "vectors": {"size": 384, "distance": "Cosine"}
            }
            requests.put(
                f"{rag_components['qdrant']}/collections/{collection_name}",
                json=create_payload,
                timeout=5
            )

            # Insert test vector
            upsert_payload = {
                "points": [
                    {
                        "id": 1,
                        "vector": [0.1] * 384,
                        "payload": {"text": "Test document"}
                    }
                ]
            }

            response = requests.put(
                f"{rag_components['qdrant']}/collections/{collection_name}/points",
                json=upsert_payload,
                timeout=5
            )

            # Cleanup
            requests.delete(f"{rag_components['qdrant']}/collections/{collection_name}", timeout=5)

            assert response.status_code == 200

        except requests.exceptions.ConnectionError:
            pytest.skip("Qdrant not accessible")

    def test_qdrant_search(self, rag_components):
        """Test searching in Qdrant"""
        collection_name = "test_rag_search"

        try:
            # Create and populate collection
            create_payload = {
                "vectors": {"size": 384, "distance": "Cosine"}
            }
            requests.put(
                f"{rag_components['qdrant']}/collections/{collection_name}",
                json=create_payload,
                timeout=5
            )

            upsert_payload = {
                "points": [
                    {
                        "id": 1,
                        "vector": [0.1] * 384,
                        "payload": {"text": "AI is transforming technology"}
                    },
                    {
                        "id": 2,
                        "vector": [0.2] * 384,
                        "payload": {"text": "Machine learning is powerful"}
                    }
                ]
            }
            requests.put(
                f"{rag_components['qdrant']}/collections/{collection_name}/points",
                json=upsert_payload,
                timeout=5
            )

            # Search
            search_payload = {
                "vector": [0.1] * 384,
                "limit": 2
            }

            response = requests.post(
                f"{rag_components['qdrant']}/collections/{collection_name}/points/search",
                json=search_payload,
                timeout=5
            )

            # Cleanup
            requests.delete(f"{rag_components['qdrant']}/collections/{collection_name}", timeout=5)

            assert response.status_code == 200
            data = response.json()
            assert len(data.get("result", [])) > 0

        except requests.exceptions.ConnectionError:
            pytest.skip("Qdrant not accessible")


@pytest.mark.concepts
class TestLab002Concepts:
    """Test conceptual understanding from LAB-002"""

    def test_rag_components_understanding(self):
        """Test: What are the components of RAG?"""
        # Quiz: Select all that apply
        # Components: Vector Database, Embeddings, LLM, Documents
        correct_components = ["vector database", "embeddings", "llm", "documents"]
        assert True  # Placeholder

    def test_embedding_purpose(self):
        """Test: Why do we need embeddings?"""
        # Quiz: What do embeddings represent?
        # Answer: Semantic meaning of text as vectors
        assert True  # Placeholder

    def test_similarity_search_concept(self):
        """Test: How does similarity search work?"""
        # Quiz: What metric is commonly used?
        # Answer: Cosine similarity
        assert True  # Placeholder

    def test_qdrant_vs_traditional_db(self):
        """Test: Difference between Qdrant and PostgreSQL"""
        # Quiz: When to use vector database?
        # Answer: For semantic search, not exact matches
        assert True  # Placeholder


@pytest.mark.checklist
class TestLab002Checklist:
    """Completion checklist for LAB-002"""

    def test_exercise_1_complete(self):
        """Exercise 1: Set up Qdrant"""
        # [ ] Qdrant container running
        # [ ] Collections API accessible
        # [ ] Can create and list collections
        assert True  # User confirms

    def test_exercise_2_complete(self):
        """Exercise 2: Generate embeddings"""
        # [ ] Embedding model running
        # [ ] Can generate embeddings for text
        # [ ] Output vectors have correct dimensions
        assert True  # User confirms

    def test_exercise_3_complete(self):
        """Exercise 3: Complete RAG pipeline"""
        # [ ] Documents indexed
        # [ ] Search returns relevant results
        # [ ] LLM generates answers with context
        assert True  # User confirms

    def test_exercise_4_complete(self):
        """Exercise 4: Gradio interface (if applicable)"""
        # [ ] UI loads successfully
        # [ ] Can submit queries
        # [ ] Results display correctly
        assert True  # User confirms
