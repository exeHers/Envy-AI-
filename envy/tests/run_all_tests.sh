#!/bin/bash
# Run all acceptance tests for Envy AI Assistant

set -e

echo "======================================================================"
echo "Envy AI Assistant - Acceptance Test Suite"
echo "======================================================================"
echo ""

# Create artifacts directory
mkdir -p ../artifacts/tests

# Change to envy directory
cd "$(dirname "$0")/.."

# Run tests
echo "Running tests..."
echo ""

PASSED=0
FAILED=0

# Function to run test
run_test() {
    TEST_NAME=$1
    TEST_FILE=$2
    
    echo "----------------------------------------------------------------------"
    echo "Running: $TEST_NAME"
    echo "----------------------------------------------------------------------"
    
    if python3 "$TEST_FILE" 2>&1 | tee "./artifacts/tests/${TEST_NAME}.log"; then
        echo "✓ PASSED: $TEST_NAME"
        ((PASSED++))
    else
        echo "✗ FAILED: $TEST_NAME"
        ((FAILED++))
    fi
    echo ""
}

# Run individual tests
run_test "test_wake_word" "tests/test_wake_word.py"
run_test "test_stt" "tests/test_stt.py"
run_test "test_tts" "tests/test_tts.py"
run_test "test_llm" "tests/test_llm.py"
run_test "test_code_skill" "tests/test_code_skill.py"
run_test "test_research_skill" "tests/test_research_skill.py"

# Summary
echo "======================================================================"
echo "Test Results Summary"
echo "======================================================================"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✓ ALL TESTS PASSED"
    exit 0
else
    echo "✗ SOME TESTS FAILED"
    exit 1
fi
