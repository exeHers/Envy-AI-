#!/usr/bin/env python3
"""
Cursor Build Log Generator
Generates a summary log for Cursor agents.
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

LOG_FILE = Path(__file__).parent.parent / 'cursor-build-log.txt'
ENVY_DIR = Path(__file__).parent.parent

def main():
    """Generate build log."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(LOG_FILE, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("Envy Build Log\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write("=" * 60 + "\n\n")
        
        # Check package
        package_file = ENVY_DIR / 'envy-ready.zip'
        if package_file.exists():
            f.write("✓ PASS: envy-ready.zip exists\n")
            f.write(f"  Location: {package_file}\n")
            f.write(f"  Size: {package_file.stat().st_size / 1024 / 1024:.2f} MB\n\n")
        else:
            f.write("✗ FAIL: envy-ready.zip not found\n\n")
        
        # Check test results
        test_results = ENVY_DIR / 'artifacts' / 'tests' / 'test_results.json'
        if test_results.exists():
            with open(test_results) as tf:
                results = json.load(tf)
                passed = sum(1 for r in results if r.get('passed'))
                total = len(results)
                f.write(f"Tests: {passed}/{total} passed\n")
                for result in results:
                    status = "✓" if result.get('passed') else "✗"
                    f.write(f"  {status} {result.get('test', 'Unknown')}\n")
                f.write("\n")
        else:
            f.write("⚠ WARNING: Test results not found\n\n")
        
        # Check key files
        key_files = [
            ('src/main.py', 'Main orchestrator'),
            ('config/envy.yaml', 'Configuration'),
            ('install_envy.sh', 'Linux installer'),
            ('install_envy.bat', 'Windows installer'),
            ('run_envy_local.sh', 'Linux runner'),
            ('run_envy_local.bat', 'Windows runner'),
            ('README.md', 'Documentation'),
            ('LICENSE', 'License'),
        ]
        
        f.write("Key Files:\n")
        for file_path, description in key_files:
            full_path = ENVY_DIR / file_path
            if full_path.exists():
                f.write(f"  ✓ {file_path} - {description}\n")
            else:
                f.write(f"  ✗ {file_path} - MISSING\n")
        f.write("\n")
        
        # Check skills
        skills_dir = ENVY_DIR / 'skills'
        if skills_dir.exists():
            skills = list(skills_dir.glob('*.py'))
            f.write(f"Skills: {len(skills)} found\n")
            for skill in skills:
                f.write(f"  - {skill.name}\n")
            f.write("\n")
        
        # Acceptance criteria
        f.write("Acceptance Criteria:\n")
        
        # Check wake word test
        f.write("  [ ] Wake word detection test\n")
        
        # Check CodeSkill test
        test_file = ENVY_DIR / 'test.py'
        if test_file.exists():
            content = test_file.read_text()
            if 'hello' in content.lower():
                f.write("  [✓] CodeSkill created test.py with hello\n")
            else:
                f.write("  [✗] CodeSkill test file missing hello\n")
        else:
            f.write("  [✗] CodeSkill test file not created\n")
        
        # Check TTS output
        tts_output = ENVY_DIR / 'artifacts' / 'tts' / 'test_tts_output.wav'
        if tts_output.exists() or (ENVY_DIR / 'artifacts' / 'tests' / 'test_tts_output.wav').exists():
            f.write("  [✓] TTS synthesized output\n")
        else:
            f.write("  [ ] TTS output not found\n")
        
        # Check router/LLM
        f.write("  [ ] Router used LLMAdapter\n")
        
        # Check package contents
        if package_file.exists():
            f.write("  [✓] envy-ready.zip exists\n")
            # Check zip contents (basic check)
            try:
                import zipfile
                with zipfile.ZipFile(package_file) as zf:
                    files = zf.namelist()
                    required = ['run_envy_local.sh', 'install_envy.sh', 'config/envy.yaml']
                    for req in required:
                        if any(req in f for f in files):
                            f.write(f"  [✓] Package contains {req}\n")
                        else:
                            f.write(f"  [✗] Package missing {req}\n")
            except:
                f.write("  [ ] Could not verify package contents\n")
        
        # Check test logs
        test_log = ENVY_DIR / 'artifacts' / 'tests' / 'test_results.log'
        if test_log.exists():
            f.write("  [✓] Test logs exist\n")
        else:
            f.write("  [ ] Test logs not found\n")
        
        f.write("\n")
        f.write("=" * 60 + "\n")
        f.write("Build log complete\n")
        f.write("=" * 60 + "\n")
    
    print(f"Build log written to: {LOG_FILE}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
