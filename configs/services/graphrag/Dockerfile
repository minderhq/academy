# PROJECT-OMEGA GraphRAG Service Dockerfile
# Multi-stage build for production deployment

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim

# Set metadata
LABEL maintainer="PROJECT-OMEGA"
LABEL description="GraphRAG Service - Knowledge Graph + Vector Search"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 graphrag && \
    mkdir -p /app /data /documents && \
    chown -R graphrag:graphrag /app /data /documents

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=graphrag:graphrag . .

# Switch to non-root user
USER graphrag

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV QDRANT_URL=http://qdrant:6334
ENV NEO4J_URI=bolt://neo4j:7687
ENV CHUNK_SIZE=512
ENV CHUNK_OVERLAP=50
ENV TOP_K=5
ENV GRAPH_DEPTH=2
ENV ALPHA=0.5
ENV LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "-m", "graphrag.server"]
