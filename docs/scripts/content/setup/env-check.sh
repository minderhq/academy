#!/bin/bash
# PROJECT-OMEGA Environment Check Script
# Verifies that all required components are installed and working
# Usage: bash scripts/setup/env-check.sh

set -e

echo "================================================"
echo "PROJECT-OMEGA Environment Check"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASS=0
FAIL=0
WARN=0

# Function to print section header
print_section() {
    echo ""
    echo "================================================"
    echo "$1"
    echo "================================================"
    echo ""
}

# Function to print result
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}✗ $2${NC}"
        FAIL=$((FAIL + 1))
    fi
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
    WARN=$((WARN + 1))
}

# OS Check
print_section "1. Operating System"

OS=$(uname -s)
echo "Detected OS: $OS"

if [[ "$OS" == "Darwin" ]]; then
    print_result 0 "macOS detected"
    ARCH=$(uname -m)
    echo "Architecture: $ARCH"
elif [[ "$OS" == "Linux" ]]; then
    print_result 0 "Linux detected"
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "Distribution: $NAME"
    fi
else
    print_result 1 "Unsupported OS: $OS"
    print_warning "PROJECT-OMEGA supports macOS and Linux"
fi

# Hardware Check
print_section "2. Hardware Verification"

# RAM Check
if [[ "$OS" == "Darwin" ]]; then
    RAM_GB=$(sysctl -n hw.memsize | awk '{print $1/1024/1024/1024}')
else
    RAM_GB=$(free -g | awk '/^Mem:/{print $2}')
fi

echo "Total RAM: ${RAM_GB}GB"
if [ "$RAM_GB" -ge 16 ]; then
    print_result 0 "RAM: ${RAM_GB}GB (meets minimum)"
elif [ "$RAM_GB" -ge 8 ]; then
    print_warning "RAM: ${RAM_GB}GB (below recommended 16GB)"
else
    print_result 1 "RAM: ${RAM_GB}GB (insufficient)"
fi

# Storage Check
echo "Checking storage space..."
if [[ "$OS" == "Darwin" ]]; then
    FREE_GB=$(df -h / | awk 'NR==2{print $4}' | sed 's/G//')
    AVAIL_GB=$(df -h / | awk 'NR==2{print $4}' | sed 's/G//' | sed 's/%.*//')
else
    FREE_GB=$(df -h / | awk 'NR==2{print $4}' | sed 's/G//')
    AVAIL_GB=$(df -h / | awk 'NR==2{print $4}' | sed 's/G//' | sed 's/%.*//')
fi

echo "Available storage: ${AVAIL_GB}GB"
if [ "$AVAIL_GB" -ge 100 ]; then
    print_result 0 "Storage: ${AVAIL_GB}GB available (sufficient)"
else
    print_warning "Storage: ${AVAIL_GB}GB available (100GB+ recommended)"
fi

# GPU Check
print_section "3. GPU Detection"

if command -v nvidia-smi &> /dev/null; then
    print_result 0 "NVIDIA driver installed"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | while read line; do
        echo "  GPU: $line"
    done
    print_result 0 "GPU detected and accessible"
else
    print_warning "NVIDIA GPU not detected"
    echo "  CPU-only mode will be used (slower but functional)"
fi

# Docker Check
print_section "4. Docker Installation"

if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    print_result 0 "Docker installed: $DOCKER_VERSION"

    if docker ps &> /dev/null; then
        print_result 0 "Docker daemon running"
    else
        print_result 1 "Docker daemon not running"
        echo "  Start Docker with: docker desktop (Mac/Win) or systemctl start docker (Linux)"
    fi
else
    print_result 1 "Docker not installed"
    echo "  Install from: https://www.docker.com/products/docker-desktop"
fi

if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version --short 2>/dev/null || docker-compose --version | awk '{print $3}')
    print_result 0 "Docker Compose installed: $COMPOSE_VERSION"
else
    print_result 1 "Docker Compose not installed"
fi

# Python Check
print_section "5. Python Environment"

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    print_result 0 "Python installed: $PYTHON_VERSION"

    # Check if version is 3.10+
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        print_result 0 "Python version compatible (3.10+)"
    else
        print_warning "Python version: $PYTHON_VERSION (3.10+ recommended)"
    fi
else
    print_result 1 "Python 3 not installed"
    echo "  Install from: https://www.python.org/downloads/"
fi

# Check for virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    print_result 0 "Virtual environment active: $VIRTUAL_ENV"
else
    print_warning "No virtual environment active"
    echo "  Create one with: python3 -m venv venv"
fi

# Ollama Check
print_section "6. Ollama Installation"

if command -v ollama &> /dev/null; then
    OLLAMA_VERSION=$(ollama --version | awk '{print $3}')
    print_result 0 "Ollama installed: $OLLAMA_VERSION"

    # Check if Ollama server is running
    if pgrep -x "ollama" &> /dev/null; then
        print_result 0 "Ollama server running"

        # Check installed models
        echo "Installed models:"
        if ollama list &> /dev/null; then
            ollama list | while read line; do
                echo "  $line"
            done
        else
            print_warning "No models installed"
            echo "  Pull one with: ollama pull mistral:7b"
        fi
    else
        print_result 1 "Ollama server not running"
        echo "  Start with: ollama serve"
    fi
else
    print_result 1 "Ollama not installed"
    echo "  Install from: https://ollama.com/download"
fi

# Python Package Check
print_section "7. Python Package Verification"

echo "Checking core packages..."
PACKAGES=(
    "torch:PyTorch"
    "transformers:Transformers"
    "fastapi:FastAPI"
    "qdrant-client:Qdrant Client"
)

for pkg in "${PACKAGES[@]}"; do
    package_name=${pkg%%:*}
    friendly_name=${pkg##*:}

    if python3 -c "import ${package_name}" 2>/dev/null; then
        version=$(python3 -c "import ${package_name}; print(${package_name}.__version__)" 2>/dev/null || echo "installed")
        print_result 0 "$friendly_name: $version"
    else
        print_warning "$friendly_name: not installed"
    fi
done

# Network Check
print_section "8. Network Connectivity"

if ping -c 1 google.com &> /dev/null; then
    print_result 0 "Internet connection available"
else
    print_result 1 "No internet connection"
fi

if curl -s https://ollama.com &> /dev/null; then
    print_result 0 "Ollama.com reachable"
else
    print_warning "Ollama.com not reachable (check firewall/VPN)"
fi

# Summary
print_section "SUMMARY"

echo "Checks Passed: $PASS"
echo "Checks Failed: $FAIL"
echo "Warnings: $WARN"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}Environment check PASSED!${NC}"
    echo -e "${GREEN}You're ready to start PROJECT-OMEGA!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Complete LAB-000: Environment Setup"
    echo "2. Start with TUTORIAL-001: Hello LLM"
    echo "3. Track progress in PROGRESS-TRACKER.md"
    exit 0
else
    echo -e "${RED}================================================${NC}"
    echo -e "${RED}Environment check FAILED${NC}"
    echo -e "${RED}Please resolve the errors above${NC}"
    echo -e "${RED}================================================${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "- Docker issues: Check Docker is running"
    echo "- Python issues: Verify PATH configuration"
    echo "- Ollama issues: Run 'ollama serve'"
    echo ""
    echo "For help, see:"
    echo "- ENVIRONMENT-SETUP.md"
    echo "- TROUBLESHOOTING-QUICKSTART.md"
    exit 1
fi
