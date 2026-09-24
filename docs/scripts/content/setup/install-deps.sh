#!/bin/bash
# PROJECT-OMEGA: Install Python Dependencies
# Installs all required Python packages for PROJECT-OMEGA

set -e

echo "Installing PROJECT-OMEGA Python dependencies..."

# Check if virtual environment is active
if [ -z "$VIRTUAL_ENV" ]; then
    echo "ERROR: No virtual environment active"
    echo "Create and activate one first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate  # Mac/Linux"
    echo "  venv\Scripts\activate     # Windows"
    exit 1
fi

echo "Virtual environment: $VIRTUAL_ENV"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Core ML packages
echo ""
echo "Installing core ML packages..."
pip install torch torchvision torchaudio
pip install transformers datasets accelerate
pip install peft bitsandbytes trl

# RAG and vector databases
echo ""
echo "Installing RAG packages..."
pip install chromadb qdrant-client
pip install langchain langchain-community
pip install sentence-transformers

# FastAPI and web framework
echo ""
echo "Installing web framework..."
pip install fastapi uvicorn[standard]
pip install python-multipart pydantic
pip install python-dotenv

# Utilities
echo ""
echo "Installing utilities..."
pip install jupyter pandas numpy matplotlib
pip install requests tqdm python-dotenv
pip install rich typer

# Development tools
echo ""
echo "Installing development tools..."
pip install pytest pytest-cov black ruff mypy
pip install pre-commit

# Ollama Python client
echo ""
echo "Installing Ollama client..."
pip install ollama

echo ""
echo "================================================"
echo "Installation complete!"
echo "================================================"
echo ""
echo "Verify installation:"
echo "  python -c 'import torch; print(torch.__version__)'"
echo "  python -c 'import transformers; print(transformers.__version__)'"
echo ""

# Test imports
echo "Testing imports..."
python -c "import torch; print('✓ PyTorch installed')"
python -c "import transformers; print('✓ Transformers installed')"
python -c "import fastapi; print('✓ FastAPI installed')"
python -c "import qdrant_client; print('✓ Qdrant client installed')"
python -c "import ollama; print('✓ Ollama installed')"

echo ""
echo "All dependencies installed successfully!"
