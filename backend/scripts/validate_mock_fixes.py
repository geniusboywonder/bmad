#!/usr/bin/env python3
"""
Validation Script for Mock Fixes

This script validates that the mock fixes are working correctly by:
1. Running specific tests that were fixed
2. Checking for proper test markers
3. Verifying real service usage
"""

import subprocess
import sys
import os
from pathlib import Path

def run_test_file(test_file: str, markers: str = None) -> dict:
    """Run a specific test file and return results."""
    cmd = ["python", "-m", "pytest", test_file, "-v"]
    if markers:
        cmd.extend(["-m", markers])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "returncode": -1
        }

def validate_test_markers(test_file: str) -> dict:
    """Validate that tests have proper data classification markers."""
    try:
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Count marker usage
        real_data_count = content.count('@pytest.mark.real_data')
        mock_data_count = content.count('@pytest.mark.mock_data')
        external_service_count = content.count('@pytest.mark.external_service')
        
        return {
            "real_data_tests": real_data_count,
            "mock_data_tests": mock_data_count,
            "external_service_tests": external_service_count,
            "total_marked": real_data_count + mock_data_count + external_service_count
        }
    except Exception as e:
        return {"error": str(e)}

def main():
    """Main validation function."""
    print("🔍 VALIDATING MOCK FIXES")
    print("=" * 50)
    
    # Test files that were fixed
    fixed_files = [
        "tests/test_autogen_conversation.py",
        "tests/test_extracted_orchestrator_services.py", 
        "tests/test_sdlc_orchestration.py",
        "tests/test_llm_providers.py"
    ]
    
    results = {}
    
    for test_file in fixed_files:
        print(f"\n📁 Validating: {test_file}")
        print("-" * 40)
        
        # Check if file exists
        if not Path(test_file).exists():
            print(f"❌ File not found: {test_file}")
            continue
        
        # Validate markers
        marker_info = validate_test_markers(test_file)
        if "error" in marker_info:
            print(f"❌ Error reading file: {marker_info['error']}")
            continue
        
        print(f"📊 Test Markers:")
        print(f"   Real Data Tests: {marker_info['real_data_tests']}")
        print(f"   Mock Data Tests: {marker_info['mock_data_tests']}")
        print(f"   External Service Tests: {marker_info['external_service_tests']}")
        print(f"   Total Marked: {marker_info['total_marked']}")
        
        # Run real_data tests only (to avoid external dependencies)
        print(f"\n🧪 Running real_data tests...")
        test_result = run_test_file(test_file, "real_data")
        
        if test_result["success"]:
            print("✅ Tests passed!")
        else:
            print(f"❌ Tests failed (exit code: {test_result['returncode']})")
            if test_result.get("stderr"):
                print(f"Error output: {test_result['stderr'][:500]}...")
        
        results[test_file] = {
            "markers": marker_info,
            "test_result": test_result
        }
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    total_real_data = sum(r["markers"].get("real_data_tests", 0) for r in results.values())
    total_external_service = sum(r["markers"].get("external_service_tests", 0) for r in results.values())
    passed_files = sum(1 for r in results.values() if r["test_result"]["success"])
    
    print(f"✅ Files with real_data tests: {len([f for f, r in results.items() if r['markers'].get('real_data_tests', 0) > 0])}")
    print(f"📊 Total real_data tests added: {total_real_data}")
    print(f"🌐 Total external_service tests: {total_external_service}")
    print(f"🎯 Test files passing: {passed_files}/{len(results)}")
    
    if passed_files == len(results):
        print("\n🎉 ALL VALIDATIONS PASSED!")
        print("✅ Mock fixes are working correctly")
        return 0
    else:
        print(f"\n⚠️  {len(results) - passed_files} files have test failures")
        print("🔧 Review test output above for details")
        return 1

if __name__ == "__main__":
    sys.exit(main())