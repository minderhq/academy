#!/bin/bash

# PROJECT-OMEGA Book Analysis Script
# Analyzes word counts by category for print estimation

cd "C:\AI-Studio\PROJECT-OMEGA"

echo "=== PROJECT-OMEGA BOOK ANALYSIS ==="
echo ""

# Count files by category
echo "FILE COUNTS BY CATEGORY:"
echo "========================"

echo "Volumes: $(find docs/volumes -type f -name "*.md" | wc -l)"
echo "Phases: $(find docs/phases -type f -name "*.md" | wc -l)"
echo "Experiments: $(find experiments -type f -name "*.md" | wc -l)"
echo "Labs: $(find docs/labs -type f -name "*.md" 2>/dev/null | wc -l)"
echo "Notebooks: $(find docs/notebooks -type f -name "*.ipynb" 2>/dev/null | wc -l)"
echo "Meta files: $(find docs/00-META -type f -name "*.md" 2>/dev/null | wc -l)"
echo "Tutorials: $(find docs/learning-resources/tutorials -type f -name "*.md" 2>/dev/null | wc -l)"
echo "Cheat Sheets: $(find docs/learning-resources/cheat-sheets -type f -name "*.md" 2>/dev/null | wc -l)"
echo "Projects: $(find docs/learning-resources/projects -type f -name "*.md" 2>/dev/null | wc -l)"
echo "Use Cases: $(find docs/use-cases -type f -name "*.md" 2>/dev/null | wc -l)"
echo "Comparisons: $(find docs/comparisons -type f -name "*.md" 2>/dev/null | wc -l)"
echo "Industry: $(find docs/industry -type f -name "*.md" 2>/dev/null | wc -l)"
echo "Solutions: $(find docs/solutions -type f -name "*.md" 2>/dev/null | wc -l)"
echo "Diagrams: $(find docs/diagrams -type f -name "*.md" 2>/dev/null | wc -l)"
echo ""

echo "WORD COUNTS BY CATEGORY:"
echo "========================"

# Function to count words in a directory
count_words() {
    local dir="$1"
    local pattern="${2:-*.md}"
    find "$dir" -type f -name "$pattern" -exec wc -w {} + 2>/dev/null | tail -1 | awk '{print $1}'
}

echo "Volumes: $(count_words 'docs/volumes') words"
echo "Phases: $(count_words 'docs/phases') words"
echo "Experiments: $(count_words 'experiments') words"
echo "Labs: $(count_words 'docs/labs') words"
echo "Notebooks: $(find docs/notebooks -type f -name "*.ipynb" 2>/dev/null | wc -l) notebooks"
echo "Meta files: $(count_words 'docs/00-META') words"
echo "Tutorials: $(count_words 'docs/learning-resources/tutorials') words"
echo "Cheat Sheets: $(count_words 'docs/learning-resources/cheat-sheets') words"
echo "Projects: $(count_words 'docs/learning-resources/projects') words"
echo "Use Cases: $(count_words 'docs/use-cases') words"
echo "Comparisons: $(count_words 'docs/comparisons') words"
echo "Industry: $(count_words 'docs/industry') words"
echo "Solutions: $(count_words 'docs/solutions') words"
echo "Diagrams: $(find docs/diagrams -type f -name "*.md" 2>/dev/null | wc -l) diagram files"
echo ""

echo "TOTAL STATISTICS:"
echo "================="
echo "Total Markdown files: $(find . -type f -name "*.md" | wc -l)"
echo "Total Notebook files: $(find . -type f -name "*.ipynb" | wc -l)"
echo "Total words (md): $(find . -type f -name "*.md" -exec wc -w {} + 2>/dev/null | tail -1 | awk '{print $1}')"
echo "Total lines (md): $(find . -type f -name "*.md" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')"
echo "Total characters (md): $(find . -type f -name "*.md" -exec wc -c {} + 2>/dev/null | tail -1 | awk '{print $1}')"
echo ""

echo "VOLUME-SPECIFIC WORD COUNTS:"
echo "============================="
for vol in docs/volumes/VOLUME-*.md; do
    if [ -f "$vol" ]; then
        words=$(wc -w < "$vol")
        basename=$(basename "$vol" .md)
        echo "$basename: $words words"
    fi
done
echo ""

echo "CODE BLOCK AND DIAGRAM ANALYSIS:"
echo "================================"
echo "Total code blocks (estimated): $(grep -r '```' docs --include="*.md" | wc -l)"
echo "Total Mermaid diagrams: $(grep -r 'mermaid' docs --include="*.md" | wc -l)"
echo ""

echo "PAGE CALCULATIONS:"
echo "=================="
total_words=$(find . -type f -name "*.md" -exec wc -w {} + 2>/dev/null | tail -1 | awk '{print $1}')
code_blocks=$(grep -r '```' docs --include="*.md" | wc -l)
mermaid_diagrams=$(grep -r 'mermaid' docs --include="*.md" | wc -l)

# Calculate pages for different formats
echo "A5 Format (14x21cm) - ~350 words/page:"
echo "  Text only: $((total_words / 350)) pages"
echo "  With code blocks (1.5x multiplier): $((total_words / 350 * 3 / 2)) pages"
echo ""

echo "B5 Format (17x25cm) - ~450 words/page:"
echo "  Text only: $((total_words / 450)) pages"
echo "  With code blocks (1.5x multiplier): $((total_words / 450 * 3 / 2)) pages"
echo ""

echo "A4 Format (21x30cm) - ~500 words/page:"
echo "  Text only: $((total_words / 500)) pages"
echo "  With code blocks (1.5x multiplier): $((total_words / 500 * 3 / 2)) pages"
