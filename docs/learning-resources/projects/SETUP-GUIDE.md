---
Document ID: SETUP-GUIDE
Title: "PROJECT-001-007: Common Setup Guide"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Intermediate
Tags: ['project', 'setup', 'docker']
---

# PROJECT-001-007: Common Setup Guide

**For:** All PROJECT-XXX capstone projects
**Last Updated:** 2026-09-30

---

## 🚀 Quick Setup (Common to All Projects)

### Step 1: Environment Setup

**Clone Template:**
```bash
git clone https://github.com/your-org/project-template.git
cd project-template
```

**Configure Environment:**
```bash
cp .env.example .env
# Edit .env with your settings
```

### Step 2: Start Infrastructure

```bash
docker compose up -d
```

### Step 3: Verify Services

```bash
# Check all services
docker compose ps

# Check logs
docker compose logs -f
```

---

## 📁 Common Project Structure

```text
project-XXX/
├── docker-compose.yml
├── .env
├── pyproject.toml
├── uv.lock
├── src/
│   ├── main.py
│   ├── config.py
│   └── utils/
├── tests/
├── data/
└── docs/
```

---

## 🔧 Common Configuration

### Docker Compose Pattern

```yaml

services:
  app:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/db

  db:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=password
```

### Python Dependencies Pattern

```toml
# pyproject.toml - dependencies declared via uv add
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
]
```

---

## ✅ Universal Checklist

### Before Starting Any Project

- [ ] Environment set up
- [ ] Docker running
- [ ] Dependencies installed
- [ ] .env configured
- [ ] Prerequisites completed

### After Completing Any Project

- [ ] Tests passing
- [ ] Documentation updated
- [ ] Code committed
- [ ] Services stopped

---

**Need Help?** Check individual project prerequisite guides.
