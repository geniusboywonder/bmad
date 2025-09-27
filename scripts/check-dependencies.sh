#!/bin/bash

# BMAD Dependency Health Check Script
# This script checks for outdated dependencies and security vulnerabilities

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

echo -e "${BLUE}🔍 BMAD Dependency Health Check${NC}"
echo "======================================="

# Check if we're in the right directory
if [[ ! -f "$PROJECT_ROOT/frontend/package.json" ]] || [[ ! -f "$PROJECT_ROOT/backend/requirements.txt" ]]; then
    echo -e "${RED}❌ Error: Could not find frontend/package.json or backend/requirements.txt${NC}"
    echo "Make sure you're running this script from the project root."
    exit 1
fi

# Function to check command availability
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}❌ $1 is not installed${NC}"
        return 1
    fi
    return 0
}

# Check required tools
echo -e "${BLUE}📋 Checking required tools...${NC}"
TOOLS_MISSING=0

if ! check_command "npm"; then TOOLS_MISSING=1; fi
if ! check_command "pip"; then TOOLS_MISSING=1; fi

if [[ $TOOLS_MISSING -eq 1 ]]; then
    echo -e "${RED}❌ Some required tools are missing. Please install them and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All required tools are available${NC}"

# Frontend dependency check
echo -e "\n${BLUE}🖥️  Frontend Dependencies${NC}"
echo "================================"

cd "$PROJECT_ROOT/frontend"

# Check for outdated packages
echo -e "${YELLOW}📦 Checking for outdated npm packages...${NC}"
if npm outdated > /tmp/npm_outdated.txt 2>&1; then
    echo -e "${GREEN}✅ All npm packages are up to date${NC}"
else
    echo -e "${YELLOW}⚠️  Found outdated packages:${NC}"
    cat /tmp/npm_outdated.txt
fi

# Security audit
echo -e "\n${YELLOW}🔒 Running npm security audit...${NC}"
if npm audit --audit-level high > /tmp/npm_audit.txt 2>&1; then
    echo -e "${GREEN}✅ No high-severity vulnerabilities found${NC}"
else
    AUDIT_EXIT_CODE=$?
    if [[ $AUDIT_EXIT_CODE -eq 1 ]]; then
        echo -e "${RED}❌ High-severity vulnerabilities found:${NC}"
        cat /tmp/npm_audit.txt
    else
        echo -e "${YELLOW}⚠️  Security audit completed with warnings:${NC}"
        cat /tmp/npm_audit.txt
    fi
fi

# Check package lock
if [[ -f "package-lock.json" ]]; then
    echo -e "${GREEN}✅ package-lock.json exists${NC}"
else
    echo -e "${YELLOW}⚠️  package-lock.json not found${NC}"
fi

# Backend dependency check
echo -e "\n${BLUE}🐍 Backend Dependencies${NC}"
echo "=========================="

cd "$PROJECT_ROOT/backend"

# Check for outdated packages
echo -e "${YELLOW}📦 Checking for outdated pip packages...${NC}"
if pip list --outdated > /tmp/pip_outdated.txt 2>&1; then
    if [[ -s /tmp/pip_outdated.txt ]]; then
        echo -e "${YELLOW}⚠️  Found outdated packages:${NC}"
        cat /tmp/pip_outdated.txt
    else
        echo -e "${GREEN}✅ All pip packages are up to date${NC}"
    fi
else
    echo -e "${RED}❌ Error checking pip packages${NC}"
fi

# Security check with safety (if available)
if command -v safety &> /dev/null; then
    echo -e "\n${YELLOW}🔒 Running safety security check...${NC}"
    if safety check > /tmp/safety_check.txt 2>&1; then
        echo -e "${GREEN}✅ No known security vulnerabilities found${NC}"
    else
        echo -e "${RED}❌ Security vulnerabilities found:${NC}"
        cat /tmp/safety_check.txt
    fi
else
    echo -e "${YELLOW}⚠️  'safety' tool not installed. Install with: pip install safety${NC}"
fi

# Check requirements files
if [[ -f "requirements.txt" ]]; then
    echo -e "${GREEN}✅ requirements.txt exists${NC}"

    # Count dependencies
    DEPS_COUNT=$(grep -v '^#' requirements.txt | grep -v '^$' | wc -l)
    echo -e "${BLUE}📊 Total dependencies: $DEPS_COUNT${NC}"
else
    echo -e "${RED}❌ requirements.txt not found${NC}"
fi

# Critical dependency versions check
echo -e "\n${BLUE}🎯 Critical Dependencies Status${NC}"
echo "=================================="

# Frontend critical deps
cd "$PROJECT_ROOT/frontend"
echo -e "${YELLOW}Frontend:${NC}"

# Check CopilotKit version
COPILOT_VERSION=$(npm list @copilotkit/react-core --depth=0 2>/dev/null | grep '@copilotkit/react-core@' | sed 's/.*@copilotkit\/react-core@//' || echo "Not installed")
echo -e "  CopilotKit: ${COPILOT_VERSION}"

# Check Next.js version
NEXT_VERSION=$(npm list next --depth=0 2>/dev/null | grep 'next@' | sed 's/.*next@//' || echo "Not installed")
echo -e "  Next.js: ${NEXT_VERSION}"

# Check React version
REACT_VERSION=$(npm list react --depth=0 2>/dev/null | grep 'react@' | sed 's/.*react@//' || echo "Not installed")
echo -e "  React: ${REACT_VERSION}"

# Backend critical deps
cd "$PROJECT_ROOT/backend"
echo -e "\n${YELLOW}Backend:${NC}"

# Check if we're in a virtual environment
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo -e "  ${GREEN}✅ Virtual environment active: $(basename "$VIRTUAL_ENV")${NC}"
else
    echo -e "  ${YELLOW}⚠️  No virtual environment detected${NC}"
fi

# Check Google ADK version
ADK_VERSION=$(pip show google-adk 2>/dev/null | grep Version | cut -d' ' -f2 || echo "Not installed")
echo -e "  Google ADK: ${ADK_VERSION}"

# Check FastAPI version
FASTAPI_VERSION=$(pip show fastapi 2>/dev/null | grep Version | cut -d' ' -f2 || echo "Not installed")
echo -e "  FastAPI: ${FASTAPI_VERSION}"

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
echo -e "  Python: ${PYTHON_VERSION}"

# Summary
echo -e "\n${BLUE}📊 Summary${NC}"
echo "============"

# Count issues
ISSUES=0

# Check for high-severity npm vulnerabilities
if npm audit --audit-level high > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend security: No high-severity vulnerabilities${NC}"
else
    echo -e "${RED}❌ Frontend security: High-severity vulnerabilities found${NC}"
    ISSUES=$((ISSUES + 1))
fi

# Check backend security
if command -v safety &> /dev/null && safety check > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend security: No known vulnerabilities${NC}"
elif command -v safety &> /dev/null; then
    echo -e "${RED}❌ Backend security: Vulnerabilities found${NC}"
    ISSUES=$((ISSUES + 1))
else
    echo -e "${YELLOW}⚠️  Backend security: Unable to check (install 'safety')${NC}"
fi

# Final status
if [[ $ISSUES -eq 0 ]]; then
    echo -e "\n${GREEN}🎉 All dependency checks passed!${NC}"
    exit 0
else
    echo -e "\n${RED}⚠️  Found $ISSUES critical issue(s) that need attention${NC}"
    exit 1
fi

# Cleanup
rm -f /tmp/npm_outdated.txt /tmp/npm_audit.txt /tmp/pip_outdated.txt /tmp/safety_check.txt