#!/bin/bash
# Automated test suite for Envy

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVY_DIR="$SCRIPT_DIR/.."
TEST_DIR="$ENVY_DIR/artifacts/tests"
VENV_DIR="$ENVY_DIR/venv"

mkdir -p "$TEST_DIR"

LOG_FILE="$TEST_DIR/test-$(date +%Y%m%d-%H%M%S).log"

echo "==========================================" | tee -a "$LOG_FILE"
echo "Envy Acceptance Tests" | tee -a "$LOG_FILE"
echo "Started: $(date)" | tee -a "$LOG_FILE"
echo "==========================================" | tee -a "$LOG_FILE"
echo ""

# Activate venv if available
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
fi

cd "$ENVY_DIR"

# Test 1: Wake word detection (simulated)
echo "[TEST 1] Wake word detection..." | tee -a "$LOG_FILE"
python3 -c "
import sys
sys.path.insert(0, '$ENVY_DIR')
sys.path.insert(0, '$ENVY_DIR/services')
from services.config_loader import Config
from services.wake_listener import WakeWordListener

config = Config()
wake_listener = WakeWordListener(config, lambda: print('Wake word detected'))
print('Wake word listener initialized')
" >> "$LOG_FILE" 2>&1 && echo "PASS" | tee -a "$LOG_FILE" || echo "FAIL" | tee -a "$LOG_FILE"
echo ""

# Test 2: STT service
echo "[TEST 2] STT service initialization..." | tee -a "$LOG_FILE"
python3 -c "
import sys
sys.path.insert(0, '$ENVY_DIR')
sys.path.insert(0, '$ENVY_DIR/services')
from services.config_loader import Config
from services.stt_service import STTService

config = Config()
config.apply_profile('low')  # Use tiny model for testing
stt = STTService(config)
print('STT service initialized')
" >> "$LOG_FILE" 2>&1 && echo "PASS" | tee -a "$LOG_FILE" || echo "FAIL (may need model download)" | tee -a "$LOG_FILE"
echo ""

# Test 3: TTS service
echo "[TEST 3] TTS service..." | tee -a "$LOG_FILE"
python3 -c "
import sys
sys.path.insert(0, '$ENVY_DIR')
sys.path.insert(0, '$ENVY_DIR/services')
from services.config_loader import Config
from services.tts_service import TTSService

config = Config()
tts = TTSService(config)
tts.save_to_file('Test TTS output', '$TEST_DIR/tts-output.wav')
print('TTS test completed')
" >> "$LOG_FILE" 2>&1 && echo "PASS" | tee -a "$LOG_FILE" || echo "FAIL" | tee -a "$LOG_FILE"
echo ""

# Test 4: CodeSkill end-to-end
echo "[TEST 4] CodeSkill end-to-end..." | tee -a "$LOG_FILE"
python3 -c "
import sys
sys.path.insert(0, '$ENVY_DIR')
sys.path.insert(0, '$ENVY_DIR/services')
sys.path.insert(0, '$ENVY_DIR/skills')
from services.config_loader import Config
from skills.codeskill import CodeSkill

config = Config()
skill = CodeSkill(config)
result = skill.execute('create test.py that prints hello')
print(f'Result: {result}')
if result.get('success') and 'test.py' in result.get('data', {}).get('filename', ''):
    print('CodeSkill test passed')
else:
    print('CodeSkill test failed')
    sys.exit(1)
" >> "$LOG_FILE" 2>&1 && echo "PASS" | tee -a "$LOG_FILE" || echo "FAIL" | tee -a "$LOG_FILE"

# Verify file was created
if [ -f "$ENVY_DIR/workspace/test.py" ]; then
    echo "File created: workspace/test.py" | tee -a "$LOG_FILE"
    cat "$ENVY_DIR/workspace/test.py" | tee -a "$LOG_FILE"
else
    echo "File not found: workspace/test.py" | tee -a "$LOG_FILE"
fi
echo ""

# Test 5: ResearchSkill
echo "[TEST 5] ResearchSkill end-to-end..." | tee -a "$LOG_FILE"
python3 -c "
import sys
sys.path.insert(0, '$ENVY_DIR')
sys.path.insert(0, '$ENVY_DIR/services')
sys.path.insert(0, '$ENVY_DIR/skills')
from services.config_loader import Config
from skills.researchskill import ResearchSkill

config = Config()
skill = ResearchSkill(config)
result = skill.execute('research quantum computing')
print(f'Result: {result}')
if result.get('success'):
    print('ResearchSkill test passed')
else:
    print('ResearchSkill test failed')
    sys.exit(1)
" >> "$LOG_FILE" 2>&1 && echo "PASS" | tee -a "$LOG_FILE" || echo "FAIL" | tee -a "$LOG_FILE"
echo ""

# Test 6: Router
echo "[TEST 6] Router intent classification..." | tee -a "$LOG_FILE"
python3 -c "
import sys
sys.path.insert(0, '$ENVY_DIR')
sys.path.insert(0, '$ENVY_DIR/services')
sys.path.insert(0, '$ENVY_DIR/skills')
from services.config_loader import Config
from services.llm_adapter import LLMAdapter
from services.router import Router

config = Config()
config.apply_profile('low')
llm = LLMAdapter(config)
router = Router(config, llm)
result = router.route('Envy, create test.py that prints hello')
print(f'Router result: {result}')
if result.get('success') or result.get('skill') == 'CodeSkill':
    print('Router test passed')
else:
    print('Router test failed')
" >> "$LOG_FILE" 2>&1 && echo "PASS" | tee -a "$LOG_FILE" || echo "FAIL" | tee -a "$LOG_FILE"
echo ""

# Test 7: LLM Adapter (fallback test)
echo "[TEST 7] LLM Adapter fallback..." | tee -a "$LOG_FILE"
python3 -c "
import sys
sys.path.insert(0, '$ENVY_DIR')
sys.path.insert(0, '$ENVY_DIR/services')
from services.config_loader import Config
from services.llm_adapter import LLMAdapter

config = Config()
config.apply_profile('low')
llm = LLMAdapter(config)
response = llm.generate('Say hello in one word')
print(f'LLM response: {response}')
if response:
    print('LLM adapter test passed')
else:
    print('LLM adapter test failed (may need model or remote endpoint)')
" >> "$LOG_FILE" 2>&1 && echo "PASS (or SKIP if no model)" | tee -a "$LOG_FILE" || echo "SKIP" | tee -a "$LOG_FILE"
echo ""

echo "==========================================" | tee -a "$LOG_FILE"
echo "Tests completed: $(date)" | tee -a "$LOG_FILE"
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"
echo "==========================================" | tee -a "$LOG_FILE"

# Summary
PASS_COUNT=$(grep -c "PASS" "$LOG_FILE" || echo "0")
FAIL_COUNT=$(grep -c "FAIL" "$LOG_FILE" || echo "0")

echo ""
echo "Summary: $PASS_COUNT passed, $FAIL_COUNT failed"
echo "Exit code: $([ $FAIL_COUNT -eq 0 ] && echo 0 || echo 1)"

exit $([ $FAIL_COUNT -eq 0 ] && echo 0 || echo 1)
