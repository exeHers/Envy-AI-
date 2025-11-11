#!/bin/bash
# Build log generator for Cursor

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

LOG_FILE="cursor-build-log.txt"

echo "==========================================" > "$LOG_FILE"
echo "Envy Build Log" >> "$LOG_FILE"
echo "Started: $(date)" >> "$LOG_FILE"
echo "==========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Test 1: Wake word detection
echo "[TEST 1] Wake word detection..." | tee -a "$LOG_FILE"
cd envy
python3 -c "
from services.wake_listener import WakeWordListener
from services.config_loader import EnvyConfig
import logging
logging.basicConfig(level=logging.WARNING)

config = EnvyConfig.load_from_file('config/envy.yaml')
listener = WakeWordListener(config)
if listener.initialize():
    print('PASS: Wake word listener initialized')
    exit(0)
else:
    print('FAIL: Wake word listener failed')
    exit(1)
" 2>&1 | tee -a "../$LOG_FILE"
WAKE_TEST=${PIPESTATUS[0]}

# Test 2: CodeSkill
echo "" >> "../$LOG_FILE"
echo "[TEST 2] CodeSkill end-to-end..." | tee -a "../$LOG_FILE"
python3 -c "
from skills.codeskill import CodeSkill
from services.config_loader import EnvyConfig
import os
import logging
logging.basicConfig(level=logging.WARNING)

config = EnvyConfig.load_from_file('config/envy.yaml')
skill = CodeSkill(config)
result = skill.execute({'text': 'create test.py that prints hello'})

if result.get('success') and os.path.exists('test.py'):
    content = open('test.py').read()
    if 'hello' in content.lower() or 'print' in content.lower():
        print('PASS: CodeSkill created test.py')
        os.remove('test.py')
        exit(0)
    else:
        print('FAIL: Content incorrect')
        exit(1)
else:
    print('FAIL: CodeSkill failed')
    exit(1)
" 2>&1 | tee -a "../$LOG_FILE"
CODE_TEST=${PIPESTATUS[0]}

# Test 3: TTS
echo "" >> "../$LOG_FILE"
echo "[TEST 3] TTS service..." | tee -a "../$LOG_FILE"
python3 -c "
from services.tts_service import TTSService
from services.config_loader import EnvyConfig
import logging
logging.basicConfig(level=logging.WARNING)

config = EnvyConfig.load_from_file('config/envy.yaml')
tts = TTSService(config)
if tts.initialize():
    if tts.save_to_file('Hello from Envy test', 'artifacts/tts-output.wav'):
        print('PASS: TTS service works')
        exit(0)
    else:
        print('FAIL: TTS save failed')
        exit(1)
else:
    print('FAIL: TTS initialization failed')
    exit(1)
" 2>&1 | tee -a "../$LOG_FILE"
TTS_TEST=${PIPESTATUS[0]}

# Summary
cd ..
echo "" >> "$LOG_FILE"
echo "==========================================" >> "$LOG_FILE"
echo "Test Summary" >> "$LOG_FILE"
echo "Wake word test: $([ $WAKE_TEST -eq 0 ] && echo 'PASS' || echo 'FAIL')" >> "$LOG_FILE"
echo "CodeSkill test: $([ $CODE_TEST -eq 0 ] && echo 'PASS' || echo 'FAIL')" >> "$LOG_FILE"
echo "TTS test: $([ $TTS_TEST -eq 0 ] && echo 'PASS' || echo 'FAIL')" >> "$LOG_FILE"
echo "Completed: $(date)" >> "$LOG_FILE"
echo "==========================================" >> "$LOG_FILE"

if [ $WAKE_TEST -eq 0 ] && [ $CODE_TEST -eq 0 ] && [ $TTS_TEST -eq 0 ]; then
    echo "All core tests passed!" >> "$LOG_FILE"
    exit 0
else
    echo "Some tests failed!" >> "$LOG_FILE"
    exit 1
fi
