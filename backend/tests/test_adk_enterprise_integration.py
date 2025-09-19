#!/usr/bin/env python3
"""Main Enterprise Integration Testing Runner for Google ADK + BMAD.

This module orchestrates comprehensive enterprise integration testing
by running tests across multiple specialized test modules.
"""

import asyncio
import time
from typing import Dict, Any
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)

class EnterpriseIntegrationTestRunner:
    """Main test runner for enterprise integration tests."""

    def __init__(self):
        self.test_modules = [
            "test_hitl_integration",
            "test_context_store_integration",
            "test_websocket_integration",
            "test_audit_trail_integration",
            "test_security_integration",
            "test_performance_load",
            "test_compliance_validation"
        ]

    async def run_all_enterprise_tests(self) -> Dict[str, Any]:
        """Run all enterprise integration test modules."""
        logger.info("Starting comprehensive enterprise integration tests")

        test_start_time = time.time()
        all_results = {}

        # Import and run each test module
        for module_name in self.test_modules:
            try:
                logger.info(f"Running test module: {module_name}")

                # Dynamic import of test module
                module = __import__(f"backend.tests.integration.{module_name}",
                                   fromlist=[f"run_{module_name.replace('test_', '')}_tests"])

                # Get the test function
                test_function_name = f"run_{module_name.replace('test_', '')}_tests"
                test_function = getattr(module, test_function_name)

                # Run the test
                result = await test_function()
                all_results[module_name] = result

                logger.info(f"Completed test module: {module_name}",
                          success=result.get("success", False))

            except Exception as e:
                logger.error(f"Failed to run test module: {module_name}", error=str(e))
                all_results[module_name] = {
                    "success": False,
                    "error": str(e),
                    "module": module_name
                }

        test_duration = time.time() - test_start_time

        # Generate comprehensive report
        report = {
            "test_suite": "ADK Enterprise Integration (Multi-Module)",
            "execution_time": test_duration,
            "timestamp": datetime.now().isoformat(),
            "test_results": all_results,
            "overall_status": self._calculate_overall_status(all_results),
            "summary": self._generate_test_summary(all_results),
            "recommendations": self._generate_enterprise_recommendations(all_results)
        }

        logger.info("Enterprise integration tests completed", duration=test_duration)
        return report

    def _calculate_overall_status(self, test_results: Dict[str, Any]) -> str:
        """Calculate overall test status."""
        successful_tests = sum(1 for result in test_results.values()
                             if result.get("success", False))
        total_tests = len(test_results)

        if successful_tests == total_tests:
            return "ALL_PASSED"
        elif successful_tests >= total_tests * 0.8:  # 80% success rate
            return "MOSTLY_PASSED"
        elif successful_tests >= total_tests * 0.5:  # 50% success rate
            return "PARTIALLY_PASSED"
        else:
            return "MOSTLY_FAILED"

    def _generate_test_summary(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of all test results."""
        total_tests = len(test_results)
        successful_tests = sum(1 for result in test_results.values()
                             if result.get("success", False))
        failed_tests = total_tests - successful_tests

        return {
            "total_test_modules": total_tests,
            "successful_modules": successful_tests,
            "failed_modules": failed_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "failed_module_names": [
                name for name, result in test_results.items()
                if not result.get("success", False)
            ]
        }

    def _generate_enterprise_recommendations(self, test_results: Dict[str, Any]) -> list:
        """Generate enterprise recommendations based on test results."""
        recommendations = []

        for module_name, result in test_results.items():
            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error")
                recommendations.append(
                    f"Fix issues in {module_name}: {error_msg}"
                )

        if not recommendations:
            recommendations.append("All enterprise integration tests passed successfully")

        return recommendations

async def run_enterprise_integration_tests() -> Dict[str, Any]:
    """Convenience function to run all enterprise integration tests."""
    runner = EnterpriseIntegrationTestRunner()
    return await runner.run_all_enterprise_tests()

if __name__ == "__main__":
    print("🚀 Starting Enterprise Integration Tests")
    print("Framework: Google ADK + BMAD Enterprise Integration")
    print("Mode: Multi-Module Testing")
    print()

    async def run_tests():
        try:
            results = await run_enterprise_integration_tests()

            print("\n📊 Enterprise Integration Test Results:")
            print(f"   Overall Status: {results.get('overall_status', 'UNKNOWN')}")
            print(f"   Execution Time: {results.get('execution_time', 0):.2f}s")
            print(f"   Test Modules: {results['summary']['total_test_modules']}")
            print(f"   Successful: {results['summary']['successful_modules']}")
            print(f"   Failed: {results['summary']['failed_modules']}")

            # Print individual test results
            for test_name, test_result in results.get('test_results', {}).items():
                status = "✅ PASSED" if test_result.get('success') else "❌ FAILED"
                print(f"   {test_name}: {status}")

            print("\nRecommendations:")
            for rec in results.get('recommendations', []):
                print(f"   • {rec}")

        except Exception as e:
            print(f"❌ Test execution failed: {str(e)}")
            import traceback
            traceback.print_exc()

    # Run the tests
    asyncio.run(run_tests())
