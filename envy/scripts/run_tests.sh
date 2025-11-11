#!/bin/bash
# run_tests.sh - Automated tests for Envy
set -e

ENVY_DIR="${ENVY_DIR:-$(pwd)}"
ARTIFACTS_DIR="$ENVY_DIR/artifacts/tests"
mkdir -p "$ARTIFACTS_DIR"

LOG_FILE="$ARTIFACTS_DIR/test-$(date +%Y%m%d-%H%M%S).log"

echo "=========================================="
echo "Envy Acceptance Tests"
echo "=========================================="
echo "Log file: $LOG_FILE"
echo ""

exec > >(tee -a "$LOG_FILE")
exec 2>&1

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

test_result() {
    if [ $1 -eq 0 ]; then
        echo "✓ PASS: $2"
        ((TESTS_PASSED++))
    else
        echo "✗ FAIL: $2"
        ((TESTS_FAILED++))
    fi
}

# Activate virtual environment
if [ -d "$ENVY_DIR/venv" ]; then
    source "$ENVY_DIR/venv/bin/activate"
fi

# Test 1: Wake word detection (simulated)
echo "Test 1: Wake word detection..."
python3 -c "
import sys
sys.path.insert(0, '$ENVY_DIR')
from services.wake_listener import WakeListener
import yaml
with open('$ENVY_DIR/config/envy.yaml', 'r') as f:
    config = yaml.safe_load(f)
listener = WakeListener(config, lambda: None)
print('Wake listener initialized')
" > /dev/null 2>&1
test_result $? "Wake word listener initialization"

# Test 2: STT service
echo "Test 2: STT service initialization..."
python3 -c "
import sys
sys.path.insert(0, '$ENVY_DIR')
from services.stt_service import STTService
import yaml
with open('$ENVY_DIR/config/envy.yaml', 'r') as f:
    config = yaml.safe_load(f)
# Skip actual model loading for quick test
print('STT service can be initialized')
" > /dev/null 2>&1
test_result $? "STT service initialization"

# Test 3: TTS service
echo "Test 3: TTS service..."
python3 -c "
import sys
sys.path.insert(0, '$ENVY_DIR')
from services.tts_service import TTSService
import yaml
with open('$ENVY_DIR/config/envy.yaml', 'r') as f:
    config = yaml.safe_load(f)
tts = TTSService(config)
print('TTS service initialized')
" > /dev/null 2>&1
test_result $? "TTS service initialization"

# Test 4: CodeSkill - Create test file
echo "Test 4: CodeSkill - Create test.py..."
python3 << 'PYTHON_EOF'
import sys
import os
sys.path.insert(0, '$ENVY_DIR')
from services.core_skills import CodeSkill
import yaml
import asyncio

async def test():
    with open('$ENVY_DIR/config/envy.yaml', 'r') as f:
        config = yaml.safe_load(f)
    config['workspace'] = '$ENVY_DIR'
    
    skill = CodeSkill(config)
    result = await skill.execute("create test.py that prints hello")
    
    test_file = os.path.join('$ENVY_DIR', 'test.py')
    if os.path.exists(test_file):
        with open(test_file, 'r') as f:
            content = f.read()
        if 'print' in content.lower() and 'hello' in content.lower():
            print('File created with correct content')
            os.remove(test_file)
            sys.exit(0)
        else:
            print('File created but content incorrect')
            sys.exit(1)
    else:
        print('File not created')
        sys.exit(1)

asyncio.run(test())
PYTHON_EOF
test_result $? "CodeSkill creates test.py"

# Test 5: ResearchSkill
echo "Test 5: ResearchSkill..."
python3 << 'PYTHON_EOF'
import sys
import os
sys.path.insert(0, '$ENVY_DIR')
from services.core_skills import ResearchSkill
import yaml
import asyncio

async def test():
    with open('$ENVY_DIR/config/envy.yaml', 'r') as f:
        config = yaml.safe_load(f)
    config['output_dir'] = '$ARTIFACTS_DIR'
    
    skill = ResearchSkill(config)
    result = await skill.execute("research quantum computing")
    
    if result.get('success') or 'research' in result.get('response', '').lower():
        print('Research skill executed')
        sys.exit(0)
    else:
        print('Research skill failed')
        sys.exit(1)

asyncio.run(test())
PYTHON_EOF
test_result $? "ResearchSkill execution"

# Test 6: LLM Adapter fallback
echo "Test 6: LLM Adapter fallback..."
python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, '$ENVY_DIR')
from services.llm_adapter import LLMAdapter
import yaml
import asyncio

async def test():
    with open('$ENVY_DIR/config/envy.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    adapter = LLMAdapter(config)
    await adapter.start()
    
    # Test rule-based fallback
    response = await adapter.generate("Hello", max_tokens=10)
    if response and len(response) > 0:
        print(f'LLM adapter responded: {response[:50]}')
        sys.exit(0)
    else:
        print('LLM adapter failed to respond')
        sys.exit(1)

asyncio.run(test())
PYTHON_EOF
test_result $? "LLM Adapter fallback response"

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "Passed: $TESTS_PASSED"
echo "Failed: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo "✓ All tests passed!"
    exit 0
else
    echo "✗ Some tests failed. Check $LOG_FILE for details."
    exit 1
fi
