#!/bin/bash
# GSAS-II Integration - Cleanup Preparation Script
# Execute cleanup tasks in phases

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Progress tracking
PHASE=""
STEP=0

print_phase() {
    PHASE="$1"
    STEP=0
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $PHASE${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo ""
}

print_step() {
    STEP=$((STEP + 1))
    echo -e "${GREEN}[$PHASE - Step $STEP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️  WARNING:${NC} $1"
}

print_error() {
    echo -e "${RED}❌ ERROR:${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ SUCCESS:${NC} $1"
}

# Parse command line arguments
PHASE_TO_RUN="${1:-all}"

# Phase 1: Workspace Organization
phase_1_workspace() {
    print_phase "Phase 1: Workspace Organization"
    
    print_step "Creating directory structure"
    mkdir -p test_output/logs
    mkdir -p test_output/data
    mkdir -p tests/manual
    mkdir -p archive/sprint-summaries/sprints-1-5
    mkdir -p archive/sprint-summaries/sprints-6-8
    mkdir -p archive/planning-docs
    mkdir -p archive/custom-services
    
    print_step "Moving test files to tests/manual/"
    if [ -f "test_json_editor.py" ]; then
        git mv test_json_editor.py tests/manual/ 2>/dev/null || mv test_json_editor.py tests/manual/
        print_success "Moved test_json_editor.py"
    fi
    if [ -f "test_normalize_workflow.py" ]; then
        git mv test_normalize_workflow.py tests/manual/ 2>/dev/null || mv test_normalize_workflow.py tests/manual/
        print_success "Moved test_normalize_workflow.py"
    fi
    
    print_step "Moving log files to test_output/logs/"
    for log in dashboard.log peak_analysis.log workflow_engine.log; do
        if [ -f "$log" ]; then
            mv "$log" test_output/logs/
            print_success "Moved $log"
        fi
    done
    
    print_step "Moving test data to test_output/data/"
    mv detector_5_roi_*.xy test_output/data/ 2>/dev/null || true
    if [ -f "workflow_results.csv" ]; then
        mv workflow_results.csv test_output/data/
    fi
    
    print_step "Cleaning __pycache__ directories"
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    print_success "Phase 1 Complete: Workspace Organized"
}

# Phase 2: Documentation Consolidation
phase_2_docs() {
    print_phase "Phase 2: Documentation Consolidation"
    
    print_step "Archiving Sprint 1-5 daily logs"
    for file in docs/sprint-{1..5}-day-*.md; do
        if [ -f "$file" ]; then
            git mv "$file" archive/sprint-summaries/sprints-1-5/ 2>/dev/null || mv "$file" archive/sprint-summaries/sprints-1-5/
        fi
    done
    
    print_step "Archiving Sprint 6-8 completion docs"
    git mv docs/SPRINT-*-COMPLETION.md archive/sprint-summaries/sprints-6-8/ 2>/dev/null || mv docs/SPRINT-*-COMPLETION.md archive/sprint-summaries/sprints-6-8/ 2>/dev/null || true
    git mv docs/WEEK-*-COMPLETION.md archive/sprint-summaries/sprints-6-8/ 2>/dev/null || mv docs/WEEK-*-COMPLETION.md archive/sprint-summaries/sprints-6-8/ 2>/dev/null || true
    git mv docs/WEEK-*-DAY-*.md archive/sprint-summaries/sprints-6-8/ 2>/dev/null || mv docs/WEEK-*-DAY-*.md archive/sprint-summaries/sprints-6-8/ 2>/dev/null || true
    
    print_step "Archiving planning documents"
    git mv docs/*-mvp-implementation-plan.md archive/planning-docs/ 2>/dev/null || mv docs/*-mvp-implementation-plan.md archive/planning-docs/ 2>/dev/null || true
    git mv docs/*-development-context.md archive/planning-docs/ 2>/dev/null || mv docs/*-development-context.md archive/planning-docs/ 2>/dev/null || true
    
    print_step "Archiving custom services phase docs"
    git mv docs/PHASE-*-COMPLETE.md archive/custom-services/ 2>/dev/null || mv docs/PHASE-*-COMPLETE.md archive/custom-services/ 2>/dev/null || true
    
    print_step "Archiving outdated guides"
    git mv docs/MIGRATION-GUIDE.md archive/planning-docs/ 2>/dev/null || mv docs/MIGRATION-GUIDE.md archive/planning-docs/ 2>/dev/null || true
    git mv docs/DUAL-INTERFACE-PROPOSAL.md archive/planning-docs/ 2>/dev/null || mv docs/DUAL-INTERFACE-PROPOSAL.md archive/planning-docs/ 2>/dev/null || true
    git mv docs/CRITICAL-EVALUATION-Sprint5.md archive/planning-docs/ 2>/dev/null || mv docs/CRITICAL-EVALUATION-Sprint5.md archive/planning-docs/ 2>/dev/null || true
    
    print_success "Phase 2 Complete: Documentation Consolidated"
}

# Phase 3: Git Ignore Updates
phase_3_gitignore() {
    print_phase "Phase 3: Update .gitignore"
    
    print_step "Adding ignore patterns"
    
    # Check if patterns already exist
    if ! grep -q "test_output/logs" .gitignore 2>/dev/null; then
        cat >> .gitignore << 'EOF'

# Cleanup additions (December 2025)
# Log files
*.log
test_output/logs/

# Test output data
test_output/data/*.xy
test_output/data/*.csv
test_output/data/*.chi

# Python caches
__pycache__/
*.pyc
*.pyo
EOF
        print_success "Updated .gitignore"
    else
        print_warning ".gitignore already contains cleanup patterns"
    fi
}

# Phase 4: Validation
phase_4_validate() {
    print_phase "Phase 4: Validation"
    
    print_step "Checking root directory cleanup"
    echo "Remaining files in root:"
    ls -lh *.py *.log *.csv *.xy 2>/dev/null | grep -E "^-" | awk '{print "  - " $9}' || echo "  (none - good!)"
    
    print_step "Checking documentation count"
    ACTIVE_DOCS=$(ls docs/*.md 2>/dev/null | wc -l)
    ARCHIVED_DOCS=$(find archive -name "*.md" 2>/dev/null | wc -l)
    echo "  Active docs: $ACTIVE_DOCS"
    echo "  Archived docs: $ARCHIVED_DOCS"
    
    print_step "Checking for __pycache__ directories"
    PYCACHE_COUNT=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l)
    if [ "$PYCACHE_COUNT" -eq 0 ]; then
        print_success "No __pycache__ directories found"
    else
        print_warning "Found $PYCACHE_COUNT __pycache__ directories"
    fi
    
    print_step "Git status"
    git status --short | head -20
    
    print_success "Phase 4 Complete: Validation Done"
}

# Main execution
main() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  GSAS-II Integration - Cleanup Preparation Script         ║${NC}"
    echo -e "${BLUE}║  Date: December 3, 2025                                    ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    case "$PHASE_TO_RUN" in
        1|workspace)
            phase_1_workspace
            ;;
        2|docs)
            phase_2_docs
            ;;
        3|gitignore)
            phase_3_gitignore
            ;;
        4|validate)
            phase_4_validate
            ;;
        all)
            phase_1_workspace
            phase_2_docs
            phase_3_gitignore
            phase_4_validate
            ;;
        *)
            print_error "Unknown phase: $PHASE_TO_RUN"
            echo ""
            echo "Usage: $0 [phase]"
            echo "  Phases: 1|workspace, 2|docs, 3|gitignore, 4|validate, all"
            exit 1
            ;;
    esac
    
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ Cleanup Tasks Complete                                 ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review changes: git status"
    echo "  2. Run tests: pixi run test"
    echo "  3. Fix failing tests (see docs/GSAS-II-PREP-CLEANUP-PLAN.md)"
    echo "  4. Commit changes: git commit -m 'chore: cleanup for GSAS-II integration'"
    echo ""
}

# Run main
main
