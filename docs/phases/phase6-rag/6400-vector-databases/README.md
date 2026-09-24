# 6400: Vector Databases

## Module Overview

This module covers production vector database systems for RAG applications. You'll learn to deploy, scale, and optimize vector databases like Qdrant, Pinecone, and Weaviate.

**Why This Matters:**
- Vector databases power scalable RAG systems
- Production deployment requires performance, reliability, and security
- Different databases excel at different use cases
- Proper indexing and scaling are critical for performance

## Learning Objectives

After completing this module, you will be able to:

- **Vector Database Architecture**: Understand how vector databases work
- **Qdrant Setup**: Deploy and configure Qdrant for production
- **Pinecone vs Weaviate**: Compare managed vs self-hosted solutions
- **Performance Optimization**: Tune indexes, shards, and replication
- **Production Deployment**: Build scalable, reliable vector systems

## Module Contents

### 6401: Qdrant Setup
**Self-Hosted Vector Database**

- Qdrant architecture and features
- Installation and configuration
- Index creation and tuning
- Filtered search and payload indexing
- Backup and recovery

**Experiments:**
- Deploy Qdrant locally
- Create and populate collections
- Implement filtered search
- Benchmark query performance

### 6402: Pinecone vs Weaviate
**Managed vs Self-Hosted Solutions**

- Pinecone: Managed vector database
- Weaviate: Self-hosted with ecosystem
- Performance comparison
- Cost analysis
- Feature comparison

**Experiments:**
- Deploy both databases
- Compare query performance
- Test scalability
- Analyze cost vs performance

### 6403: Qdrant Production Deployment
**Production Vector Database Self-Hosted** (Guide)

- Docker deployment on any Linux host
- Docker Compose configuration
- Persistent storage and backups
- Remote access and security
- Performance optimization

**Guide:** [guides/6403-Qdrant-Production-Deployment.md](./guides/6403-Qdrant-Production-Deployment.md)

## Prerequisites

Before starting this module, ensure you have:

- [ ] Module 6100: Vector Embeddings (vector fundamentals)
- [ ] Module 6200: Retrieval (retrieval strategies)
- [ ] Docker and container basics
- [ ] Linux system administration
- [ ] Database fundamentals

**Review:** [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

## Assessment

### Quiz
- **Format:** 20 multiple-choice questions
- **Passing Score:** 80% (16/20)
- **Topics:** Vector databases, Qdrant, Pinecone, Weaviate
- **Location:** [assessment/QUIZ.md](./assessment/QUIZ.md)

### Practice Exercises
- **Format:** Vector database deployment projects
- **Duration:** 6-8 hours
- **Topics:**
  - Deploy Qdrant in production
  - Compare Pinecone vs Weaviate
  - Optimize database performance
  - Set up backups and monitoring
- **Location:** [assessment/PRACTICE.md](./assessment/PRACTICE.md)

## Related Modules

This module connects to:
- **6100: Vector Embeddings** (embedding generation)
- **6200: Retrieval** (retrieval strategies)
- **6300: Context** (context management)
- **6500: MLOps Pipelines** (production ML)

## Time Commitment

| Activity | Time |
|----------|------|
| Reading (6401) | 3 hours |
| Experiments (6401) | 3 hours |
| Reading (6402) | 2 hours |
| Experiments (6402) | 2 hours |
| Guide (6403) | 2 hours |
| Quiz | 30 minutes |
| Practice | 6-8 hours |
| **Total** | **18-20 hours** |

## Resources

**Vector Databases:**
- Qdrant (self-hosted)
- Pinecone (managed)
- Weaviate (self-hosted)
- Milvus (self-hosted)
- pgvector (PostgreSQL extension)

**Essential Tools:**
- Docker / Docker Compose
- Python client libraries
- Monitoring tools (Prometheus, Grafana)

## Vector Database Comparison

| Feature | Qdrant | Pinecone | Weaviate | pgvector |
|---------|--------|----------|----------|---------|
| Deployment | Self-hosted | Managed | Self-hosted | Self-hosted |
| Performance | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Ease of Use | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Features | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Cost | Low (self) | High (managed) | Low (self) | Very low |
| Best For | Production | Rapid start | Rich features | Simple needs |

## Qdrant Configuration

```yaml
storage:
  # Performance tuning
  optimizers_cpu_threshold: 0.5
  optimizer_indexing_threshold: 20000

  # Memory management
  max_optimization_threads: 2

service:
  # API configuration
  max_workers: 0  # Auto

# HNSW parameters
hnsw_index:
  m: 16
  ef_construct: 100
  full_scan_threshold: 10000
```

## Performance Tuning Parameters

| Parameter | Qdrant | Pinecone | Weaviate |
|-----------|--------|----------|----------|
| Index Type | HNSW | HNSW | HNSW |
| M (connectivity) | 16 | N/A | 16 |
| ef_construction | 100 | N/A | 100 |
| ef_search | Tunable | Auto | Tunable |
| Sharding | Yes | Yes | Yes |

## Deployment Options

| Option | Complexity | Cost | Control |
|--------|------------|------|---------|
| Local Docker | Low | Minimal | Full |
| Cloud VM | Medium | Low | Full |
| Kubernetes | High | Medium | Full |
| Pinecone Managed | Low | High | Limited |
| Serverless | Low | Variable | Limited |

## Backup Strategies

| Strategy | RTO | RPO | Complexity |
|----------|-----|-----|------------|
| Snapshot backups | Minutes | Hours | Medium |
| Replication | Seconds | Minutes | High |
| S3/Cloud storage | Hours | Hours | Low |

## Tips for Success

1. **Start with Qdrant**: Best open-source option
2. **Use managed for MVP**: Pinecone is fastest to start
3. **Optimize HNSW parameters**: Small changes, big impact
4. **Monitor memory**: Vector databases are memory-hungry
5. **Test with real data**: Synthetic benchmarks lie

## Common Pitfalls

- **Wrong index parameters**: HNSW tuning is critical
- **Ignoring filters**: Payload filtering needs optimization
- **Under-provisioning**: Vector databases need RAM
- **No backups**: Data loss is catastrophic
- **Skipping monitoring**: Performance degrades silently

## When to Choose Each Database

| Scenario | Recommended |
|----------|-------------|
| Production, control | Qdrant |
| Quick start, low effort | Pinecone |
| Rich ecosystem, self-hosted | Weaviate |
| Existing PostgreSQL | pgvector |
| Enterprise, on-prem | Milvus |

## Cost Comparison (Monthly)

| Database | 1M vectors | 10M vectors | 100M vectors |
|----------|-----------|-------------|--------------|
| Qdrant (self) | $20 | $100 | $500 |
| Pinecone ( Starter) | $70 | $200+ | Custom |
| Weaviate (self) | $20 | $100 | $500 |
| pgvector (self) | $10 | $50 | $200 |

## Production Checklist

Before deploying to production:
- [ ] HNSW parameters tuned
- [ ] Backup strategy configured
- [ ] Monitoring set up
- [ ] Replication configured
- [ ] Security (auth, TLS) enabled
- [ ] Load testing completed
- [ ] Disaster recovery tested
- [ ] Documentation complete

---

**Next Module:** [6500: MLOps Pipelines](../6500-mlops-pipelines/README.md)

**Previous Module:** [6300: Context Management](../6300-context/README.md)

**Questions?** Review the [PREREQUISITES.md](./PREREQUISITES.md) or check Phase 6 documentation.

---

**Last Updated:** 2026-02-04
