#!/bin/bash

# BMAD Safe Dependency Update Script
# This script performs safe, tier-based dependency updates

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
TIER=${1:-1}
DRY_RUN=${2:-false}

echo -e "${BLUE}🚀 BMAD Dependency Update Script${NC}"
echo "===================================="
echo -e "${BLUE}Tier: ${TIER} | Dry Run: ${DRY_RUN}${NC}"

# Check if we're in the right directory
if [[ ! -f "$PROJECT_ROOT/frontend/package.json" ]] || [[ ! -f "$PROJECT_ROOT/backend/requirements.txt" ]]; then
    echo -e "${RED}❌ Error: Could not find frontend/package.json or backend/requirements.txt${NC}"
    echo "Make sure you're running this script from the project root."
    exit 1
fi

# Function to run command with dry-run support
run_cmd() {
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}[DRY RUN] Would run: $*${NC}"
    else
        echo -e "${BLUE}Running: $*${NC}"
        "$@"
    fi
}

# Function to backup current state
backup_state() {
    echo -e "${YELLOW}📦 Creating backup...${NC}"

    BACKUP_DIR="$PROJECT_ROOT/.backup/$(date +%Y%m%d_%H%M%S)"

    if [[ "$DRY_RUN" != "true" ]]; then
        mkdir -p "$BACKUP_DIR"
        cp "$PROJECT_ROOT/frontend/package.json" "$BACKUP_DIR/"
        cp "$PROJECT_ROOT/frontend/package-lock.json" "$BACKUP_DIR/" 2>/dev/null || true
        cp "$PROJECT_ROOT/backend/requirements.txt" "$BACKUP_DIR/"
        echo -e "${GREEN}✅ Backup created at: $BACKUP_DIR${NC}"
    else
        echo -e "${YELLOW}[DRY RUN] Would create backup at: $BACKUP_DIR${NC}"
    fi
}

# Function to run tests
run_tests() {
    echo -e "${YELLOW}🧪 Running tests...${NC}"

    # Frontend tests
    cd "$PROJECT_ROOT/frontend"
    run_cmd npm test -- --run
    run_cmd npm run lint
    run_cmd npm run build

    # Backend tests
    cd "$PROJECT_ROOT/backend"
    if [[ -f "pytest.ini" ]] || [[ -d "tests" ]]; then
        run_cmd python -m pytest
    fi

    if command -v mypy &> /dev/null; then
        run_cmd python -m mypy . || echo -e "${YELLOW}⚠️  MyPy check failed${NC}"
    fi
}

# Tier 1: Safe updates (patch and minor versions)
update_tier_1() {
    echo -e "\n${GREEN}🔧 Tier 1: Safe Updates (Patches & Bug fixes)${NC}"
    echo "================================================="

    # Frontend Tier 1 updates
    echo -e "${BLUE}Frontend updates:${NC}"
    cd "$PROJECT_ROOT/frontend"

    # CopilotKit updates (safe minor updates)
    run_cmd npm update @copilotkit/react-core @copilotkit/react-textarea @copilotkit/react-ui @copilotkit/runtime

    # Next.js patch updates
    run_cmd npm update next

    # Anthropic Claude Code updates
    run_cmd npm update @anthropic-ai/claude-code

    # Security-focused updates
    run_cmd npm audit fix --audit-level high

    # Backend Tier 1 updates
    echo -e "\n${BLUE}Backend updates:${NC}"
    cd "$PROJECT_ROOT/backend"

    # Google ADK update
    run_cmd pip install google-adk==1.15.1

    # FastAPI ecosystem updates
    run_cmd pip install fastapi==0.117.1
    run_cmd pip install uvicorn[standard]>=0.37.0
    run_cmd pip install google-cloud-aiplatform>=1.117.0

    # Security updates
    run_cmd pip install structlog>=25.4.0
    run_cmd pip install python-dotenv>=1.1.1
}

# Tier 2: Planned updates (minor versions with testing)
update_tier_2() {
    echo -e "\n${YELLOW}🔧 Tier 2: Planned Updates (Minor versions)${NC}"
    echo "=============================================="

    # Frontend Tier 2 updates
    echo -e "${BLUE}Frontend updates:${NC}"
    cd "$PROJECT_ROOT/frontend"

    # Testing library updates
    run_cmd npm update @testing-library/react @testing-library/user-event @testing-library/jest-dom

    # Development tools
    run_cmd npm update @vitest/ui vitest
    run_cmd npm update lucide-react

    # UI component updates (careful selection)
    run_cmd npm update @radix-ui/react-toast @radix-ui/react-tooltip @radix-ui/react-progress

    # Backend Tier 2 updates
    echo -e "\n${BLUE}Backend updates:${NC}"
    cd "$PROJECT_ROOT/backend"

    # Testing updates
    run_cmd pip install pytest>=8.4.2
    run_cmd pip install pytest-asyncio>=1.2.0

    # Worker updates
    run_cmd pip install celery>=5.5.3

    # Development tools
    run_cmd pip install httpx>=0.27.0
}

# Tier 3: Major updates (requires manual review)
update_tier_3() {
    echo -e "\n${RED}🔧 Tier 3: Major Updates (Manual review required)${NC}"
    echo "=================================================="

    echo -e "${YELLOW}⚠️  Tier 3 updates require manual review and testing:${NC}"
    echo "  Frontend:"
    echo "    - Tailwind CSS v3 → v4 (breaking changes)"
    echo "    - Zod v3 → v4 (breaking changes)"
    echo "    - React Window v1 → v2 (breaking changes)"
    echo ""
    echo "  Backend:"
    echo "    - Redis v5 → v6 (major version)"
    echo "    - Alembic database migrations"
    echo "    - SQLAlchemy major updates"
    echo ""
    echo -e "${BLUE}Please review docs/dependency-management-strategy.md for detailed migration guides.${NC}"
}

# Function to update requirements.txt with new versions
update_requirements() {
    if [[ "$DRY_RUN" != "true" ]]; then
        echo -e "${YELLOW}📝 Updating requirements.txt...${NC}"
        cd "$PROJECT_ROOT/backend"
        pip freeze > requirements.txt.new
        mv requirements.txt.new requirements.txt
        echo -e "${GREEN}✅ requirements.txt updated${NC}"
    else
        echo -e "${YELLOW}[DRY RUN] Would update requirements.txt${NC}"
    fi
}

# Main execution
main() {
    echo -e "${BLUE}🔍 Pre-update dependency check...${NC}"
    "$SCRIPT_DIR/check-dependencies.sh" || echo -e "${YELLOW}⚠️  Dependency check found issues${NC}"

    # Create backup
    backup_state

    # Run updates based on tier
    case $TIER in
        1)
            update_tier_1
            ;;
        2)
            update_tier_1
            update_tier_2
            ;;
        3)
            update_tier_1
            update_tier_2
            update_tier_3
            ;;
        *)
            echo -e "${RED}❌ Invalid tier: $TIER. Use 1, 2, or 3.${NC}"
            exit 1
            ;;
    esac

    # Update requirements.txt for backend
    if [[ $TIER -le 2 ]]; then
        update_requirements
    fi

    # Run tests
    if [[ "$DRY_RUN" != "true" ]]; then
        echo -e "\n${YELLOW}🧪 Running post-update tests...${NC}"
        run_tests

        echo -e "\n${GREEN}🎉 Dependency updates completed successfully!${NC}"
        echo -e "${BLUE}Next steps:${NC}"
        echo "1. Review git diff to see what changed"
        echo "2. Run integration tests"
        echo "3. Test the application manually"
        echo "4. Commit changes if everything works"

        # Show git status
        cd "$PROJECT_ROOT"
        echo -e "\n${BLUE}Git status:${NC}"
        git status --porcelain || echo "Not a git repository"
    else
        echo -e "\n${GREEN}🎉 Dry run completed!${NC}"
        echo -e "${BLUE}To apply changes, run: $0 $TIER false${NC}"
    fi
}

# Help function
show_help() {
    echo "Usage: $0 [TIER] [DRY_RUN]"
    echo ""
    echo "TIER:"
    echo "  1 - Safe updates (patches, bug fixes) [default]"
    echo "  2 - Planned updates (minor versions)"
    echo "  3 - Show major updates (requires manual review)"
    echo ""
    echo "DRY_RUN:"
    echo "  true  - Show what would be updated without making changes [default]"
    echo "  false - Actually perform the updates"
    echo ""
    echo "Examples:"
    echo "  $0                  # Dry run tier 1 updates"
    echo "  $0 1 false          # Apply tier 1 updates"
    echo "  $0 2 true           # Dry run tier 1 + 2 updates"
    echo "  $0 3 true           # Show all available updates"
}

# Check for help
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    show_help
    exit 0
fi

# Run main function
main