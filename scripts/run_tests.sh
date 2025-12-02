#!/usr/bin/env bash

# Test runner script for Multi-Agent Mobile UI Assistant
# Usage: ./run_tests.sh [options]

set -e

echo "=================================="
echo "Multi-Agent Mobile UI Assistant"
echo "Test Runner"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}Error: uv is not installed${NC}"
    echo "Install it with: pip install uv"
    exit 1
fi

# Parse command line arguments
COVERAGE=false
VERBOSE=false
SPECIFIC_TEST=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -t|--test)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: ./run_tests.sh [options]"
            echo ""
            echo "Options:"
            echo "  -c, --coverage     Run with coverage report"
            echo "  -v, --verbose      Run with verbose output"
            echo "  -t, --test FILE    Run specific test file"
            echo "  -h, --help         Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run_tests.sh                          # Run all tests"
            echo "  ./run_tests.sh -c                       # Run with coverage"
            echo "  ./run_tests.sh -v                       # Run with verbose output"
            echo "  ./run_tests.sh -t test_ui_generator.py  # Run specific test"
            echo "  ./run_tests.sh -c -v                    # Coverage + verbose"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Ensure dependencies are installed
echo -e "${YELLOW}Checking dependencies...${NC}"
uv sync --extra dev > /dev/null 2>&1
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Build pytest command
PYTEST_CMD="uv run pytest"

if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=src/multi_agent_mobile_ui_assistant --cov-report=term-missing --cov-report=html"
fi

if [ -n "$SPECIFIC_TEST" ]; then
    PYTEST_CMD="$PYTEST_CMD tests/$SPECIFIC_TEST"
fi

# Run tests
echo -e "${YELLOW}Running tests...${NC}"
echo "Command: $PYTEST_CMD"
echo ""

if $PYTEST_CMD; then
    echo ""
    echo -e "${GREEN}=================================="
    echo "✓ All tests passed!"
    echo "==================================${NC}"
    
    if [ "$COVERAGE" = true ]; then
        echo ""
        echo -e "${YELLOW}Coverage report generated:${NC}"
        echo "  - Terminal: above"
        echo "  - HTML: htmlcov/index.html"
        echo ""
        echo "To view HTML report:"
        echo "  open htmlcov/index.html"
    fi
    
    exit 0
else
    echo ""
    echo -e "${RED}=================================="
    echo "✗ Tests failed"
    echo "==================================${NC}"
    exit 1
fi
