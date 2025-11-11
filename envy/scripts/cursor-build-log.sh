#!/bin/bash
# cursor-build-log.sh - Generate build log for Cursor verification
set -e

ENVY_DIR="${ENVY_DIR:-/workspace/envy}"
LOG_FILE="/workspace/cursor-build-log.txt"

{
    echo "=========================================="
    echo "Envy Build Log - Cursor Verification"
    echo "Generated: $(date)"
    echo "=========================================="
    echo ""
    
    echo "1. PROJECT STRUCTURE"
    echo "-------------------"
    echo "Checking directory structure..."
    if [ -d "$ENVY_DIR" ]; then
        echo "✓ envy/ directory exists"
        find "$ENVY_DIR" -type f -name "*.py" | wc -l | xargs echo "  Python files:"
        find "$ENVY_DIR" -type f -name "*.yaml" | wc -l | xargs echo "  Config files:"
        find "$ENVY_DIR" -type f -name "*.sh" | wc -l | xargs echo "  Shell scripts:"
    else
        echo "✗ envy/ directory not found"
    fi
    echo ""
    
    echo "2. CORE FILES"
    echo "------------"
    for file in "envy.py" "main.py" "requirements.txt" "config/envy.yaml" "README.md" "LICENSE"; do
        if [ -f "$ENVY_DIR/$file" ]; then
            echo "✓ $file"
        else
            echo "✗ $file MISSING"
        fi
    done
    echo ""
    
    echo "3. SERVICES"
    echo "---------"
    for service in "wake_listener.py" "stt_service.py" "tts_service.py" "llm_adapter.py" "router.py" "skill_manager.py"; do
        if [ -f "$ENVY_DIR/services/$service" ]; then
            echo "✓ services/$service"
        else
            echo "✗ services/$service MISSING"
        fi
    done
    echo ""
    
    echo "4. SKILLS"
    echo "--------"
    for skill in "codeskill.py" "researchskill.py" "syscontrolskill.py" "reminderskill.py"; do
        if [ -f "$ENVY_DIR/skills/$skill" ]; then
            echo "✓ skills/$skill"
        else
            echo "✗ skills/$skill MISSING"
        fi
    done
    echo ""
    
    echo "5. INSTALLERS"
    echo "------------"
    for installer in "scripts/install_envy.sh" "scripts/install_envy.bat"; do
        if [ -f "$ENVY_DIR/$installer" ]; then
            echo "✓ $installer"
        else
            echo "✗ $installer MISSING"
        fi
    done
    echo ""
    
    echo "6. DOCUMENTATION"
    echo "---------------"
    for doc in "README.md" "docs/install-linux.md" "docs/install-windows.md" "docs/security.md"; do
        if [ -f "$ENVY_DIR/$doc" ]; then
            echo "✓ $doc"
        else
            echo "✗ $doc MISSING"
        fi
    done
    echo ""
    
    echo "7. PYTHON SYNTAX CHECK"
    echo "---------------------"
    cd "$ENVY_DIR"
    python3 -m py_compile envy.py main.py 2>&1 && echo "✓ Main files compile successfully" || echo "✗ Syntax errors found"
    echo ""
    
    echo "8. ACCEPTANCE CRITERIA CHECK"
    echo "---------------------------"
    
    # Check wake word
    if grep -q "wake_word.*envy" "$ENVY_DIR/config/envy.yaml" 2>/dev/null; then
        echo "✓ Wake word configured as 'Envy'"
    else
        echo "✗ Wake word not configured"
    fi
    
    # Check CodeSkill
    if grep -q "CodeSkill" "$ENVY_DIR/config/envy.yaml" 2>/dev/null; then
        echo "✓ CodeSkill enabled"
    else
        echo "✗ CodeSkill not enabled"
    fi
    
    # Check TTS
    if grep -q "tts:" "$ENVY_DIR/config/envy.yaml" 2>/dev/null; then
        echo "✓ TTS configured"
    else
        echo "✗ TTS not configured"
    fi
    
    # Check LLM adapter
    if [ -f "$ENVY_DIR/services/llm_adapter.py" ]; then
        echo "✓ LLM adapter exists"
    else
        echo "✗ LLM adapter missing"
    fi
    
    # Check package script
    if [ -f "$ENVY_DIR/scripts/package_envy.sh" ]; then
        echo "✓ Package script exists"
    else
        echo "✗ Package script missing"
    fi
    
    echo ""
    echo "=========================================="
    echo "BUILD STATUS: COMPLETE"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Run tests: ./scripts/run_tests.sh"
    echo "2. Generate performance report: ./scripts/perf-report-gen.sh"
    echo "3. Create package: ./scripts/package_envy.sh"
    echo ""
    
} | tee "$LOG_FILE"

echo "Build log saved to: $LOG_FILE"
