#!/bin/bash
# PROJECT-OMEGA: Docker Environment Setup
# Sets up Docker for PROJECT-OMEGA development

set -e

echo "Setting up Docker for PROJECT-OMEGA..."

# Check Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker not installed"
    echo "Install from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo "Docker version: $(docker --version)"
echo ""

# Create Docker network if it doesn't exist
echo "Creating Docker network..."
docker network create project-omega 2>/dev/null || echo "Network already exists"
echo ""

# Pull required images
echo "Pulling required Docker images..."

echo "Pulling Qdrant..."
docker pull qdrant/qdrant:latest

echo ""
echo "Pulling PostgreSQL..."
docker pull postgres:15

echo ""
echo "Pulling Ollama..."
docker pull ollama/ollama:latest

echo ""
echo "================================================"
echo "Docker setup complete!"
echo "================================================"
echo ""
echo "Network created: project-omega"
echo "Images pulled: Qdrant, PostgreSQL, Ollama"
echo ""
echo "Start services with:"
echo "  docker compose up -d"
