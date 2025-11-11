#!/bin/bash
# Run Envy acceptance tests

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
ARTIFACTS_DIR="$BASE_DIR/artifacts/tests"

mkdir -p "$ARTIFACTS_DIR"

echo "========================================"
echo "Running Envy Acceptance Tests"
echo "========================================"
echo ""

# Activate virtual environment if it exists
if [ -d "$BASE_DIR/venv" ]; then
    source "$BASE_DIR/venv/bin/activate"
fi

cd "$BASE_DIR"

# Run tests and capture output
TEST_LOG="$ARTIFACTS_DIR/test_run_$(date +%Y%m%d_%H%M%S).log"

python3 -m pytest tests/test_acceptance.py -v --tb=short -s 2>&1 | tee "$TEST_LOG"

EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo "========================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ All tests passed!"
else
    echo "✗ Some tests failed (exit code: $EXIT_CODE)"
fi
echo "========================================"
echo ""
echo "Test log saved to: $TEST_LOG"
echo ""

exit $EXIT_CODE
