#!/bin/bash
# Automated test suite for Envy

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create test artifacts directory
mkdir -p artifacts/tests
TEST_LOG="artifacts/tests/test-$(date +%Y%m%d-%H%M%S).log"

echo "==========================================" | tee -a "$TEST_LOG"
echo "Envy Acceptance Tests" | tee -a "$TEST_LOG"
echo "Started: $(date)" | tee -a "$TEST_LOG"
echo "==========================================" | tee -a "$TEST_LOG"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Test 1: Wake word detection (simulated)
echo "[TEST 1] Wake word detection..." | tee -a "$TEST_LOG"
python -c "
from services.wake_listener import WakeWordListener
from services.config_loader import EnvyConfig
import logging
logging.basicConfig(level=logging.INFO)

config = EnvyConfig.load_from_file('config/envy.yaml')
listener = WakeWordListener(config)
if listener.initialize():
    print('PASS: Wake word listener initialized')
    exit(0)
else:
    print('FAIL: Wake word listener failed to initialize')
    exit(1)
" 2>&1 | tee -a "$TEST_LOG"
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo "PASS" | tee -a "$TEST_LOG"
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo "FAIL" | tee -a "$TEST_LOG"
fi
echo ""

# Test 2: STT service
echo "[TEST 2] STT service initialization..." | tee -a "$TEST_LOG"
python -c "
from services.stt_service import STTService
from services.config_loader import EnvyConfig
import logging
logging.basicConfig(level=logging.INFO)

config = EnvyConfig.load_from_file('config/envy.yaml')
stt = STTService(config)
if stt.initialize():
    print('PASS: STT service initialized')
    exit(0)
else:
    print('FAIL: STT service failed to initialize')
    exit(1)
" 2>&1 | tee -a "$TEST_LOG"
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo "PASS" | tee -a "$TEST_LOG"
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo "FAIL" | tee -a "$TEST_LOG"
fi
echo ""

# Test 3: TTS service
echo "[TEST 3] TTS service..." | tee -a "$TEST_LOG"
python -c "
from services.tts_service import TTSService
from services.config_loader import EnvyConfig
import logging
logging.basicConfig(level=logging.INFO)

config = EnvyConfig.load_from_file('config/envy.yaml')
tts = TTSService(config)
if tts.initialize():
    # Test saving to file
    if tts.save_to_file('Hello from Envy test', 'artifacts/tts-output.wav'):
        print('PASS: TTS service works')
        exit(0)
    else:
        print('FAIL: TTS save failed')
        exit(1)
else:
    print('FAIL: TTS service failed to initialize')
    exit(1)
" 2>&1 | tee -a "$TEST_LOG"
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo "PASS" | tee -a "$TEST_LOG"
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo "FAIL" | tee -a "$TEST_LOG"
fi
echo ""

# Test 4: CodeSkill end-to-end
echo "[TEST 4] CodeSkill end-to-end..." | tee -a "$TEST_LOG"
python -c "
from skills.codeskill import CodeSkill
from services.config_loader import EnvyConfig
import os
import logging
logging.basicConfig(level=logging.INFO)

config = EnvyConfig.load_from_file('config/envy.yaml')
skill = CodeSkill(config)
result = skill.execute({'text': 'create test.py that prints hello'})

if result.get('success') and os.path.exists('test.py'):
    content = open('test.py').read()
    if 'hello' in content.lower() or 'print' in content.lower():
        print('PASS: CodeSkill created test.py')
        exit(0)
    else:
        print('FAIL: CodeSkill created file but content incorrect')
        exit(1)
else:
    print('FAIL: CodeSkill failed')
    exit(1)
" 2>&1 | tee -a "$TEST_LOG"
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo "PASS" | tee -a "$TEST_LOG"
    # Clean up
    rm -f test.py
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo "FAIL" | tee -a "$TEST_LOG"
fi
echo ""

# Test 5: ResearchSkill end-to-end
echo "[TEST 5] ResearchSkill end-to-end..." | tee -a "$TEST_LOG"
python -c "
from skills.researchskill import ResearchSkill
from services.config_loader import EnvyConfig
import os
import logging
logging.basicConfig(level=logging.INFO)

config = EnvyConfig.load_from_file('config/envy.yaml')
skill = ResearchSkill(config)
result = skill.execute({'text': 'research python programming'})

if result.get('success'):
    print('PASS: ResearchSkill executed successfully')
    exit(0)
else:
    print('FAIL: ResearchSkill failed')
    exit(1)
" 2>&1 | tee -a "$TEST_LOG"
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo "PASS" | tee -a "$TEST_LOG"
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo "FAIL" | tee -a "$TEST_LOG"
fi
echo ""

# Test 6: Router intent classification
echo "[TEST 6] Router intent classification..." | tee -a "$TEST_LOG"
python -c "
from services.router import Router
from services.llm_adapter import LLMAdapter
from services.config_loader import EnvyConfig
import logging
logging.basicConfig(level=logging.INFO)

config = EnvyConfig.load_from_file('config/envy.yaml')
llm = LLMAdapter(config)
llm.initialize()
router = Router(config, llm)
result = router.route('create test.py that prints hello')

if result.get('intent') == 'code':
    print('PASS: Router correctly classified code intent')
    exit(0)
else:
    print(f'FAIL: Router classified as {result.get(\"intent\")} instead of code')
    exit(1)
" 2>&1 | tee -a "$TEST_LOG"
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo "PASS" | tee -a "$TEST_LOG"
else
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo "FAIL" | tee -a "$TEST_LOG"
fi
echo ""

# Summary
echo "==========================================" | tee -a "$TEST_LOG"
echo "Test Summary" | tee -a "$TEST_LOG"
echo "Passed: $TESTS_PASSED" | tee -a "$TEST_LOG"
echo "Failed: $TESTS_FAILED" | tee -a "$TEST_LOG"
echo "Total: $((TESTS_PASSED + TESTS_FAILED))" | tee -a "$TEST_LOG"
echo "Completed: $(date)" | tee -a "$TEST_LOG"
echo "==========================================" | tee -a "$TEST_LOG"

if [ $TESTS_FAILED -eq 0 ]; then
    echo "All tests passed!" | tee -a "$TEST_LOG"
    exit 0
else
    echo "Some tests failed!" | tee -a "$TEST_LOG"
    exit 1
fi
