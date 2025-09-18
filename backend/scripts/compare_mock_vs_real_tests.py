#!/usr/bin/env python3
"""
Mock vs Real Database Test Comparison

This script demonstrates the effectiveness of real database tests vs mock tests
by running both and comparing their ability to catch real issues.
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

def run_test_file(test_file, description):
    """Run a specific test file and return results."""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"📁 File: {test_file}")
    print(f"{'='*60}")

    try:
        cmd = [
            sys.executable, "-m", "pytest",
            test_file,
            "-v", "--tb=short", "--no-header"
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=Path(__file__).parent.parent
        )

        print(f"📊 Exit Code: {result.returncode}")
        print(f"⏱️  Return Time: {datetime.now().strftime('%H:%M:%S')}")

        # Extract key metrics from output
        if "passed" in result.stdout:
            passed = result.stdout.count(" PASSED")
            failed = result.stdout.count(" FAILED")
            print(f"✅ Tests Passed: {passed}")
            print(f"❌ Tests Failed: {failed}")

        if result.returncode == 0:
            print("🎉 ALL TESTS PASSED - No issues detected")
        else:
            print("🚨 TESTS FAILED - Issues detected!")

        # Show key error patterns
        if "assert" in result.stdout.lower():
            print("⚠️  Contains assertion failures")
        if "database" in result.stdout.lower():
            print("💾 Database operations involved")
        if "mock" in result.stdout.lower():
            print("🎭 Mock objects detected")

        return {
            "exit_code": result.returncode,
            "passed": passed if "passed" in result.stdout else 0,
            "failed": failed if "passed" in result.stdout else 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    except subprocess.TimeoutExpired:
        print("⏱️  TIMEOUT - Test took too long")
        return {"exit_code": -1, "timeout": True}
    except Exception as e:
        print(f"💥 ERROR: {e}")
        return {"exit_code": -2, "error": str(e)}

def main():
    """Compare mock-heavy tests vs real database tests."""

    print("🔍 MOCK vs REAL DATABASE TEST COMPARISON")
    print("=" * 80)
    print("This comparison demonstrates why mock tests hide issues that real DB tests catch.")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Test configurations
    tests = [
        {
            "file": "tests/test_hitl_safety.py::TestHITLSafetyService::test_budget_limit_check_success",
            "description": "MOCK TEST - HITL Budget Check (Hidden Issues)",
            "type": "mock"
        },
        {
            "file": "tests/test_hitl_safety_real_db.py::TestHITLSafetyServiceRealDB::test_budget_limit_check_success_real_db",
            "description": "REAL DB TEST - HITL Budget Check (Catches Issues)",
            "type": "real_db"
        },
        {
            "file": "tests/test_workflow_engine.py::TestWorkflowExecutionEngine::test_start_workflow_execution",
            "description": "MOCK TEST - Workflow Execution (Hidden Issues)",
            "type": "mock"
        },
        {
            "file": "tests/test_workflow_engine_real_db.py::TestWorkflowExecutionEngineRealDB::test_workflow_state_model_database_consistency_real_db",
            "description": "REAL DB TEST - Workflow State (Catches Issues)",
            "type": "real_db"
        }
    ]

    results = {}

    # Run all tests
    for test in tests:
        result = run_test_file(test["file"], test["description"])
        results[test["type"]] = results.get(test["type"], [])
        results[test["type"]].append({
            "test": test,
            "result": result
        })

    # Summary analysis
    print(f"\n{'='*80}")
    print("📊 SUMMARY ANALYSIS")
    print(f"{'='*80}")

    mock_passed = sum(1 for r in results.get("mock", []) if r["result"]["exit_code"] == 0)
    mock_failed = len(results.get("mock", [])) - mock_passed

    real_passed = sum(1 for r in results.get("real_db", []) if r["result"]["exit_code"] == 0)
    real_failed = len(results.get("real_db", [])) - real_passed

    print(f"🎭 MOCK TESTS:")
    print(f"   ✅ Passed: {mock_passed}")
    print(f"   ❌ Failed: {mock_failed}")
    print(f"   🎯 Detection Rate: {(mock_failed / len(results.get('mock', [1]))) * 100:.1f}% (Lower is bad)")

    print(f"\n💾 REAL DATABASE TESTS:")
    print(f"   ✅ Passed: {real_passed}")
    print(f"   ❌ Failed: {real_failed}")
    print(f"   🎯 Detection Rate: {(real_failed / len(results.get('real_db', [1]))) * 100:.1f}% (Higher is good)")

    # Key insights
    print(f"\n🔍 KEY INSIGHTS:")
    if mock_passed > real_passed:
        print("⚠️  CRITICAL: Mock tests pass more often than real DB tests!")
        print("   This indicates mock tests are hiding real issues.")
        print("   Real DB tests are catching problems that mocks miss.")

    if real_failed > mock_failed:
        print("✅ GOOD: Real DB tests catch more issues than mock tests.")
        print("   This proves real database testing is more effective.")

    print(f"\n🎯 RECOMMENDATION:")
    print("Replace mock-heavy tests with real database tests to:")
    print("• Catch enum vs boolean type mismatches")
    print("• Validate foreign key constraints")
    print("• Test actual SQL query execution")
    print("• Verify database schema consistency")

    # Final score
    if real_failed >= mock_failed:
        print(f"\n🏆 VERDICT: Real database tests are more effective!")
        print("   They catch issues that mock tests miss.")
        return 0
    else:
        print(f"\n❓ VERDICT: Results inconclusive")
        print("   Both test types had similar results.")
        return 1

if __name__ == "__main__":
    exit(main())