#!/bin/bash

cd "C:\AI-Studio\PROJECT-OMEGA"

echo "==================================================="
echo "   PROJECT-OMEGA COMPREHENSIVE BOOK ANALYSIS"
echo "==================================================="
echo ""

# Total statistics
TOTAL_MD=$(find . -type f -name "*.md" | wc -l)
TOTAL_NB=$(find . -type f -name "*.ipynb" | wc -l)
TOTAL_WORDS=$(find . -type f -name "*.md" -exec wc -w {} + 2>/dev/null | awk '{sum+=$1} END {print sum}')
TOTAL_LINES=$(find . -type f -name "*.md" -exec wc -l {} + 2>/dev/null | awk '{sum+=$1} END {print sum}')
TOTAL_CHARS=$(find . -type f -name "*.md" -exec wc -c {} + 2>/dev/null | awk '{sum+=$1} END {print sum}')

echo "TOTAL STATISTICS"
echo "================"
echo "Total Markdown files: $TOTAL_MD"
echo "Total Notebook files: $TOTAL_NB"
echo "Total files: $((TOTAL_MD + TOTAL_NB))"
echo "Total words: $TOTAL_WORDS"
echo "Total lines: $TOTAL_LINES"
echo "Total characters: $TOTAL_CHARS"
echo ""

# Category breakdown
echo "CATEGORY BREAKDOWN"
echo "=================="

count_category_words() {
    local dir="$1"
    local name="$2"
    local count=$(find "$dir" -type f -name "*.md" -exec wc -w {} + 2>/dev/null | awk '{sum+=$1} END {print sum+0}')
    local files=$(find "$dir" -type f -name "*.md" 2>/dev/null | wc -l)
    printf "%-30s %5d files  %8s words\n" "$name:" "$files" "$count"
}

count_category_words "docs/volumes" "Volumes"
count_category_words "docs/phases" "Phases (7 phases)"
count_category_words "experiments" "Experiments"
count_category_words "docs/labs" "Labs"
count_category_words "docs/00-META" "Meta files"
count_category_words "docs/learning-resources/tutorials" "Tutorials"
count_category_words "docs/learning-resources/cheat-sheets" "Cheat Sheets"
count_category_words "docs/learning-resources/projects" "Projects"
count_category_words "docs/use-cases" "Use Cases"
count_category_words "docs/comparisons" "Comparisons"
count_category_words "docs/industry" "Industry"
count_category_words "docs/solutions" "Solutions"
echo ""

# Volume-specific counts
echo "VOLUME-SPECIFIC ANALYSIS"
echo "========================"
for vol in docs/volumes/VOLUME-*.md; do
    if [ -f "$vol" ]; then
        words=$(wc -w < "$vol")
        basename=$(basename "$vol" .md)
        printf "%-35s %5s words\n" "$basename" "$words"
    fi
done
echo ""

# Phase-specific counts
echo "PHASE-SPECIFIC ANALYSIS"
echo "======================"
for phase in docs/phases/phase*; do
    if [ -d "$phase" ]; then
        words=$(find "$phase" -type f -name "*.md" -exec wc -w {} + 2>/dev/null | awk '{sum+=$1} END {print sum+0}')
        files=$(find "$phase" -type f -name "*.md" 2>/dev/null | wc -l)
        basename=$(basename "$phase")
        printf "%-35s %5s files  %8s words\n" "$basename:" "$files" "$words"
    fi
done
echo ""

# Special content analysis
CODE_BLOCKS=$(grep -r '```' docs --include="*.md" | wc -l)
MERMAID_DIAGRAMS=$(grep -r 'mermaid' docs --include="*.md" | wc -l)
TABLES=$(grep -r '^|' docs --include="*.md" | wc -l)

echo "SPECIAL CONTENT ANALYSIS"
echo "========================"
echo "Total code blocks: $CODE_BLOCKS"
echo "Total Mermaid diagrams: $MERMAID_DIAGRAMS"
echo "Total table rows: $TABLES"
echo ""

# Page calculations
echo "PAGE CALCULATIONS BY FORMAT"
echo "==========================="
echo ""

# A5 Format (14x21cm) - standard book (~350 words/page)
echo "A5 FORMAT (14x21cm) - Standard Book"
echo "  Words per page: 350"
echo "  Text-only pages: $((TOTAL_WORDS / 350))"
echo "  With code blocks (1.5x): $((TOTAL_WORDS / 350 * 3 / 2))"
echo "  With diagrams + code (1.8x): $((TOTAL_WORDS / 350 * 18 / 10))"
echo ""

# B5 Format (17x25cm) - technical book (~450 words/page)
echo "B5 FORMAT (17x25cm) - Technical Book"
echo "  Words per page: 450"
echo "  Text-only pages: $((TOTAL_WORDS / 450))"
echo "  With code blocks (1.5x): $((TOTAL_WORDS / 450 * 3 / 2))"
echo "  With diagrams + code (1.8x): $((TOTAL_WORDS / 450 * 18 / 10))"
echo ""

# A4 Format (21x30cm) - workbook (~500 words/page)
echo "A4 FORMAT (21x30cm) - Workbook"
echo "  Words per page: 500"
echo "  Text-only pages: $((TOTAL_WORDS / 500))"
echo "  With code blocks (1.5x): $((TOTAL_WORDS / 500 * 3 / 2))"
echo "  With diagrams + code (1.8x): $((TOTAL_WORDS / 500 * 18 / 10))"
echo ""

# Additional pages for special content
ADDITIONAL_PAGES=$(( (CODE_BLOCKS / 4) + (MERMAID_DIAGRAMS / 2) + (TABLES / 10) ))
echo "ADDITIONAL PAGES ESTIMATE"
echo "========================="
echo "Code blocks (1 page per 4 blocks): $((CODE_BLOCKS / 4))"
echo "Mermaid diagrams (1 page per 2): $((MERMAID_DIAGRAMS / 2))"
echo "Complex tables (1 page per 10 rows): $((TABLES / 10))"
echo "Total additional pages: $ADDITIONAL_PAGES"
echo ""

# Notebook content
echo "NOTEBOOK ANALYSIS"
echo "================="
NB_COUNT=$(find docs/notebooks -type f -name "*.ipynb" 2>/dev/null | wc -l)
echo "Total Jupyter Notebooks: $NB_COUNT"
echo "Notebooks are INTERACTIVE and should stay DIGITAL"
echo "Estimated notebook print pages (if forced): $((NB_COUNT * 8))"
echo ""

# Learning resources breakdown
LEARNING_WORDS=0
for dir in "docs/learning-resources/tutorials" "docs/learning-resources/cheat-sheets" "docs/learning-resources/projects" "docs/labs"; do
    LEARNING_WORDS=$((LEARNING_WORDS + $(find "$dir" -type f -name "*.md" -exec wc -w {} + 2>/dev/null | awk '{sum+=$1} END {print sum+0}')))
done

echo "LEARNING RESOURCES SUMMARY"
echo "========================="
echo "Tutorials + Labs + Projects + Cheat Sheets"
echo "Total words: $LEARNING_WORDS"
echo "B5 pages (with code): $((LEARNING_WORDS / 450 * 3 / 2))"
echo ""
