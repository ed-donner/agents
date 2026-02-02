#!/bin/bash
# Test Runner Script for Career Bot Application

echo "🧪 Starting Test Suite for Career Bot..."
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if pytest is installed
echo -e "${YELLOW}📦 Installing test dependencies...${NC}"
uv pip install -r requirements_test.txt

# Run Unit Tests
echo -e "\n${YELLOW}📝 Running Simplified Tests...${NC}"
uv run pytest test_simple.py -v --tb=short
TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Tests PASSED${NC}"
else
    echo -e "${RED}❌ Tests FAILED${NC}"
fi

# Run UI Tests (optional - requires app to be running)
echo -e "\n${YELLOW}🖥️  UI Tests (Skipping - requires running app)${NC}"
echo -e "${YELLOW}   To run UI tests:${NC}"
echo -e "${YELLOW}   1. Start app: uv run app_new.py${NC}"
echo -e "${YELLOW}   2. In another terminal: uv run pytest test_ui.py -v${NC}"

# Generate Coverage Report
echo -e "\n${YELLOW}📊 Generating Coverage Report...${NC}"
uv run pytest test_simple.py --cov=app_new --cov-report=html --cov-report=term-missing
echo -e "${GREEN}📂 Coverage report generated: htmlcov/index.html${NC}"

# Summary
echo -e "\n========================================"
echo -e "📊 Test Summary:"
echo -e "========================================"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All Tests: PASSED${NC}"
    TOTAL_EXIT_CODE=0
else
    echo -e "${RED}❌ Tests: FAILED${NC}"
    TOTAL_EXIT_CODE=1
fi

echo -e "========================================\n"

if [ $TOTAL_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}🎉 All Tests PASSED! Ready for deployment.${NC}"
else
    echo -e "${RED}❌ Some tests FAILED. Please fix before deployment.${NC}"
fi

exit $TOTAL_EXIT_CODE
