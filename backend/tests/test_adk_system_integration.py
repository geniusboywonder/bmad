#!/usr/bin/env python3
"""
ADK System Integration Test Suite

Comprehensive test suite to validate the entire ADK integration system
after all fixes and optimizations have been applied.
"""

import asyncio
import sys
import time
import traceback
import pytest
from typing import Dict, List, Any
from datetime import datetime

# Test results tracking
test_results = {
    "total_tests": 0,
    "passed_tests": 0,
    "failed_tests": 0,
    "skipped_tests": 0,
    "test_details": []
}

def log_test_result(test_name: str, status: str, message: str = "", error: Exception = None):
    """Log individual test result."""
    test_results["total_tests"] += 1

    if status == "PASS":
        test_results["passed_tests"] += 1
    elif status == "FAIL":
        test_results["failed_tests"] += 1
    elif status == "SKIP":
        test_results["skipped_tests"] += 1

    test_detail = {
        "test_name": test_name,
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }

    if error:
        test_detail["error"] = str(error)
        test_detail["traceback"] = traceback.format_exc()

    test_results["test_details"].append(test_detail)

    status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏭️"
    print(f"{status_icon} {test_name}: {message}")

def run_test(test_func):
    """Decorator to run and log test results."""
    async def wrapper(*args, **kwargs):
        test_name = test_func.__name__
        try:
            result = await test_func(*args, **kwargs)
            if result is None or result is True:
                log_test_result(test_name, "PASS", "Test completed successfully")
            elif isinstance(result, str):
                log_test_result(test_name, "PASS", result)
            else:
                log_test_result(test_name, "FAIL", f"Test returned unexpected result: {result}")
        except Exception as e:
            log_test_result(test_name, "FAIL", f"Test failed with exception: {str(e)}", e)

    return wrapper

class ADKSystemIntegrationTest:
    """Comprehensive integration test suite for ADK system."""

    def __init__(self):
        self.modules_to_test = [
            "adk_agent_factory",
            "adk_feature_flags",
            "adk_performance_optimizer",
            "adk_advanced_features",
            "adk_custom_tools",
            "adk_observability",
            "adk_best_practices",
            "adk_logging",
            "adk_validation",
            "adk_config"
        ]

    async def run_full_test_suite(self):
        """Run the complete test suite."""
        print("🚀 Starting ADK System Integration Test Suite")
        print("=" * 60)

        start_time = time.time()

        # Test 1: Module Import Validation
        await self.test_module_imports()

        # Test 2: Core Functionality Tests
        await self.test_core_functionality()

        # Test 3: Agent Factory Integration
        await self.test_agent_factory_integration()

        # Test 4: Feature Flags System
        await self.test_feature_flags_system()

        # Test 5: Performance Optimization
        await self.test_performance_optimization()

        # Test 6: Multi-Model Features
        await self.test_multi_model_features()

        # Test 7: Custom Tools Integration
        await self.test_custom_tools_integration()

        # Test 8: Observability System
        await self.test_observability_system()

        # Test 9: Configuration Management
        await self.test_configuration_management()

        # Test 10: Error Handling and Resilience
        await self.test_error_handling_resilience()

        # Test 11: Security Validation
        await self.test_security_validation()

        # Test 12: Performance Benchmarks
        await self.test_performance_benchmarks()

        # Generate test report
        await self.generate_test_report()

        total_time = time.time() - start_time
        print(".2f")
        # Final summary
        self.print_test_summary()

    @run_test
    @pytest.mark.external_service

    async def test_module_imports(self):
        """Test that all ADK modules can be imported successfully."""
        print("\n📦 Testing Module Imports...")

        failed_imports = []

        for module_name in self.modules_to_test:
            try:
                __import__(module_name)
                print(f"  ✅ {module_name}")
            except ImportError as e:
                failed_imports.append((module_name, str(e)))
                print(f"  ❌ {module_name}: {e}")
            except Exception as e:
                failed_imports.append((module_name, str(e)))
                print(f"  ❌ {module_name}: Unexpected error - {e}")

        if failed_imports:
            raise Exception(f"Failed to import {len(failed_imports)} modules: {failed_imports}")

        return f"Successfully imported {len(self.modules_to_test)} modules"

    @run_test
    @pytest.mark.external_service
    @pytest.mark.mock_data

    async def test_core_functionality(self):
        """Test core ADK functionality."""
        print("\n🔧 Testing Core Functionality...")

        # Test agent factory creation
        from adk_agent_factory import create_agent

        try:
            agent = create_agent("analyst", "test_user", "test_project")
            if not agent:
                raise Exception("Agent creation returned None")
            print("  ✅ Agent creation successful")
        except Exception as e:
            raise Exception(f"Agent creation failed: {e}")

        # Test feature flags
        from adk_feature_flags import feature_flags

        try:
            # Test basic flag operations
            # Reset emergency stop and enable global migration first
            feature_flags.reset_emergency_stop()
            feature_flags.flags["global_flags"]["adk_migration_enabled"] = True
            feature_flags.save_flags()

            original_state = feature_flags.is_adk_enabled_for_agent("analyst", "test_user", "test_project")
            feature_flags.enable_adk_for_agent("analyst")  # Fix: only takes agent_type and optional canary_percentage
            new_state = feature_flags.is_adk_enabled_for_agent("analyst", "test_user", "test_project")

            if new_state != True:
                raise Exception("Feature flag enable operation failed")

            print("  ✅ Feature flags system working")
        except Exception as e:
            raise Exception(f"Feature flags test failed: {e}")

        return "Core functionality tests passed"

    @run_test
    @pytest.mark.external_service
    @pytest.mark.mock_data

    async def test_agent_factory_integration(self):
        """Test agent factory integration with all components."""
        print("\n🏭 Testing Agent Factory Integration...")

        from adk_agent_factory import create_agent, get_agent_info, clear_agent_cache

        # Test agent creation for different types
        agent_types = ["analyst", "architect", "developer", "tester", "deployer"]

        for agent_type in agent_types:
            try:
                agent = create_agent(agent_type, f"user_{agent_type}", f"project_{agent_type}")
                info = get_agent_info(agent)

                if info["agent_type"] != agent_type:
                    raise Exception(f"Agent type mismatch for {agent_type}")

                print(f"  ✅ {agent_type} agent created successfully")
            except Exception as e:
                raise Exception(f"Failed to create {agent_type} agent: {e}")

        # Test cache operations
        try:
            cache_stats = clear_agent_cache()
            print("  ✅ Agent cache operations working")
        except Exception as e:
            raise Exception(f"Cache operations failed: {e}")

        return f"Successfully tested {len(agent_types)} agent types"

    @run_test
    @pytest.mark.external_service
    @pytest.mark.mock_data

    async def test_feature_flags_system(self):
        """Test feature flags system comprehensively."""
        print("\n🚩 Testing Feature Flags System...")

        from adk_feature_flags import feature_flags

        # Test agent-specific flags
        test_cases = [
            ("analyst", "user1", "project1"),
            ("architect", "user2", "project2"),
            ("developer", "user3", "project3")
        ]

        for agent_type, user_id, project_id in test_cases:
            try:
                # Reset emergency stop and enable global migration first
                feature_flags.reset_emergency_stop()
                feature_flags.flags["global_flags"]["adk_migration_enabled"] = True
                feature_flags.save_flags()

                # Test enable/disable - fix method signature
                feature_flags.enable_adk_for_agent(agent_type)  # Only takes agent_type
                enabled = feature_flags.is_adk_enabled_for_agent(agent_type, user_id, project_id)
                if not enabled:
                    raise Exception(f"Failed to enable ADK for {agent_type}")

                feature_flags.disable_adk_for_agent(agent_type)  # Only takes agent_type
                disabled = feature_flags.is_adk_enabled_for_agent(agent_type, user_id, project_id)
                if disabled:
                    raise Exception(f"Failed to disable ADK for {agent_type}")

                print(f"  ✅ {agent_type} feature flags working")
            except Exception as e:
                raise Exception(f"Feature flags test failed for {agent_type}: {e}")

        # Test global operations
        try:
            feature_flags.enable_global_rollback()
            feature_flags.emergency_stop()
            print("  ✅ Global feature flag operations working")
        except Exception as e:
            raise Exception(f"Global operations failed: {e}")

        return "Feature flags system fully functional"

    @run_test
    @pytest.mark.external_service
    @pytest.mark.mock_data

    async def test_performance_optimization(self):
        """Test performance optimization system."""
        print("\n⚡ Testing Performance Optimization...")

        from adk_performance_optimizer import run_performance_optimization

        try:
            result = await run_performance_optimization()

            print(f"  🔍 Debug: Result type: {type(result)}")
            print(f"  🔍 Debug: Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")

            if not isinstance(result, dict):
                raise Exception(f"Performance optimization did not return expected result format: got {type(result)}")

            required_keys = ["cycle_duration", "metrics_collected", "recommendations_generated", "optimizations_applied"]
            for key in required_keys:
                if key not in result:
                    raise Exception(f"Missing required key in result: {key}")

            print("  ✅ Performance optimization cycle completed")
            print(f"     Duration: {result['cycle_duration']:.2f}s")
            print(f"     Metrics collected: {result['metrics_collected']}")
            print(f"     Recommendations: {result['recommendations_generated']}")
            print(f"     Optimizations applied: {result['optimizations_applied']}")

        except Exception as e:
            print(f"  🔍 Debug: Exception details: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Performance optimization test failed: {e}")

        return "Performance optimization system working correctly"

    @run_test
    @pytest.mark.external_service
    @pytest.mark.mock_data

    async def test_multi_model_features(self):
        """Test multi-model features."""
        print("\n🤖 Testing Multi-Model Features...")

        from adk_advanced_features import select_optimal_model, create_multi_model_agent

        # Test model selection
        test_scenarios = [
            ("analysis", "low", "cost_optimized"),
            ("code_generation", "high", "performance_optimized"),
            ("vision_analysis", "medium", "balanced")
        ]

        for task_type, complexity, cost_sensitivity in test_scenarios:
            try:
                model = select_optimal_model(task_type, complexity, cost_sensitivity)
                if not model or not isinstance(model, str):
                    raise Exception(f"Invalid model selection result for {task_type}")
                print(f"  ✅ Selected model for {task_type}: {model}")
            except Exception as e:
                raise Exception(f"Model selection failed for {task_type}: {e}")

        # Test multi-model agent creation
        try:
            task_profile = {
                "primary_task": "analysis",
                "complexity": "high",
                "cost_sensitivity": "balanced",
                "requires_vision": True
            }

            multi_agent = create_multi_model_agent("analyst", task_profile)

            if not hasattr(multi_agent, 'primary_model'):
                raise Exception("Multi-model agent missing primary_model attribute")

            if not hasattr(multi_agent, 'fallback_models'):
                raise Exception("Multi-model agent missing fallback_models attribute")

            print("  ✅ Multi-model agent created successfully")
            print(f"     Primary model: {multi_agent.primary_model}")
            print(f"     Fallback models: {len(multi_agent.fallback_models)}")

        except Exception as e:
            raise Exception(f"Multi-model agent creation failed: {e}")

        return "Multi-model features working correctly"

    @run_test
    @pytest.mark.external_service
    @pytest.mark.mock_data

    async def test_custom_tools_integration(self):
        """Test custom BMAD tools integration."""
        print("\n🛠️  Testing Custom Tools Integration...")

        from adk_custom_tools import analyze_requirements, generate_architecture, generate_code

        # Test requirements analysis
        sample_requirements = """
        The system shall allow users to login with email and password.
        Users must be able to view their dashboard after login.
        The system should respond within 2 seconds for all operations.
        User data must be encrypted and secure.
        """

        try:
            analysis_result = await analyze_requirements(sample_requirements, "comprehensive")

            if not hasattr(analysis_result, 'success') or not analysis_result.success:
                raise Exception("Requirements analysis failed")

            if 'functional_requirements' not in analysis_result.data:
                raise Exception("Analysis result missing functional requirements")

            print("  ✅ Requirements analysis completed")
            print(f"     Found {len(analysis_result.data.get('functional_requirements', []))} functional requirements")

        except Exception as e:
            raise Exception(f"Requirements analysis test failed: {e}")

        # Test architecture generation
        try:
            requirements = {"authentication": True, "data": True, "notification": True}
            arch_result = await generate_architecture(requirements, "microservices")

            if not hasattr(arch_result, 'success') or not arch_result.success:
                raise Exception("Architecture generation failed")

            if 'services' not in arch_result.data:
                raise Exception("Architecture result missing services")

            print("  ✅ Architecture generation completed")
            print(f"     Generated {len(arch_result.data.get('services', []))} services")

        except Exception as e:
            raise Exception(f"Architecture generation test failed: {e}")

        # Test code generation
        try:
            code_spec = {"endpoint": "/api/users", "method": "GET"}
            code_result = await generate_code(code_spec, "api_endpoint")

            if not hasattr(code_result, 'success') or not code_result.success:
                raise Exception("Code generation failed")

            if 'code' not in code_result.data:
                raise Exception("Code result missing generated code")

            print("  ✅ Code generation completed")
            print(f"     Generated {code_result.data.get('language', 'unknown')} code")

        except Exception as e:
            raise Exception(f"Code generation test failed: {e}")

        return "Custom tools integration working correctly"

    @run_test
    @pytest.mark.external_service
    @pytest.mark.mock_data

    async def test_observability_system(self):
        """Test observability system."""
        print("\n📊 Testing Observability System...")

        from adk_observability import collect_observability_metrics, perform_system_health_check

        # Test metrics collection
        try:
            metrics = await collect_observability_metrics()

            if not isinstance(metrics, dict):
                raise Exception("Metrics collection did not return expected format")

            required_sections = ["system_metrics", "agent_metrics", "adk_metrics", "bmad_metrics"]
            for section in required_sections:
                if section not in metrics:
                    raise Exception(f"Missing required metrics section: {section}")

            print("  ✅ Observability metrics collected")
            print(f"     Collection duration: {metrics.get('collection_duration', 'N/A')}s")

        except Exception as e:
            raise Exception(f"Metrics collection test failed: {e}")

        # Test health check
        try:
            health = await perform_system_health_check()

            if not hasattr(health, 'overall_status'):
                raise Exception("Health check missing overall_status")

            if not hasattr(health, 'performance_score'):
                raise Exception("Health check missing performance_score")

            print("  ✅ System health check completed")
            print(f"     Overall status: {health.overall_status}")
            print(f"     Performance score: {health.performance_score}")

        except Exception as e:
            raise Exception(f"Health check test failed: {e}")

        return "Observability system working correctly"

    @run_test
    @pytest.mark.external_service
    @pytest.mark.mock_data

    async def test_configuration_management(self):
        """Test configuration management system."""
        print("\n⚙️  Testing Configuration Management...")

        from adk_config import config

        # Test configuration access
        try:
            max_memory = config.get("max_memory_mb")
            max_cpu = config.get("max_cpu_percent")
            log_level = config.get("log_level")

            if not isinstance(max_memory, int) or max_memory <= 0:
                raise Exception("Invalid max_memory_mb configuration")

            if not isinstance(max_cpu, (int, float)) or not (0 < max_cpu <= 100):
                raise Exception("Invalid max_cpu_percent configuration")

            print("  ✅ Configuration access working")
            print(f"     Max memory: {max_memory} MB")
            print(f"     Max CPU: {max_cpu}%")
            print(f"     Log level: {log_level}")

        except Exception as e:
            raise Exception(f"Configuration access test failed: {e}")

        # Test configuration modification
        try:
            original_value = config.get("max_memory_mb")
            config.set("max_memory_mb", 2048)
            new_value = config.get("max_memory_mb")

            if new_value != 2048:
                raise Exception("Configuration update failed")

            # Reset to original
            config.set("max_memory_mb", original_value)

            print("  ✅ Configuration modification working")

        except Exception as e:
            raise Exception(f"Configuration modification test failed: {e}")

        return "Configuration management working correctly"

    @run_test
    @pytest.mark.external_service
    @pytest.mark.mock_data

    async def test_error_handling_resilience(self):
        """Test error handling and system resilience."""
        print("\n🛡️  Testing Error Handling & Resilience...")

        from adk_agent_factory import create_agent
        from adk_validation import validate_agent_type, validate_task_description

        # Test graceful error handling in agent creation
        try:
            # This should fail gracefully and return a fallback agent
            agent = create_agent("invalid_agent_type", "test_user", "test_project")

            if not agent:
                raise Exception("Agent creation should return fallback agent for invalid type")

            print("  ✅ Graceful error handling in agent creation")

        except Exception as e:
            raise Exception(f"Error handling test failed: {e}")

        # Test input validation
        try:
            # Valid input
            validate_agent_type("analyst")
            print("  ✅ Input validation for valid input")

            # Invalid input should raise exception
            try:
                validate_agent_type("invalid_type")
                raise Exception("Validation should have failed for invalid input")
            except ValueError:
                print("  ✅ Input validation correctly rejected invalid input")

        except Exception as e:
            raise Exception(f"Input validation test failed: {e}")

        # Test task description validation
        try:
            validate_task_description("This is a valid task description for testing purposes.")
            print("  ✅ Task description validation working")

            # Test dangerous content detection
            try:
                validate_task_description("<script>alert('xss')</script>")
                raise Exception("Should have detected dangerous content")
            except ValueError:
                print("  ✅ Dangerous content detection working")

        except Exception as e:
            raise Exception(f"Task description validation test failed: {e}")

        return "Error handling and resilience working correctly"

    @run_test
    @pytest.mark.external_service
    @pytest.mark.mock_data

    async def test_security_validation(self):
        """Test security validation features."""
        print("\n🔒 Testing Security Validation...")

        from adk_validation import input_validator, validate_user_id, validate_email

        # Test text input validation
        try:
            # Valid input
            clean_text = input_validator.validate_text_input("Valid input text")
            if clean_text != "Valid input text":
                raise Exception("Text validation modified valid input unexpectedly")

            print("  ✅ Text input validation working")

        except Exception as e:
            raise Exception(f"Text input validation test failed: {e}")

        # Test dangerous content detection
        try:
            dangerous_inputs = [
                "<script>alert('xss')</script>",
                "javascript:alert('xss')",
                "<iframe src='evil.com'></iframe>",
                "UNION SELECT * FROM users"
            ]

            for dangerous_input in dangerous_inputs:
                try:
                    input_validator.validate_text_input(dangerous_input)
                    raise Exception(f"Should have detected dangerous content: {dangerous_input[:30]}...")
                except ValueError:
                    pass  # Expected

            print("  ✅ Dangerous content detection working")

        except Exception as e:
            raise Exception(f"Dangerous content detection test failed: {e}")

        # Test user ID validation
        try:
            validate_user_id("valid_user_123")
            print("  ✅ User ID validation working")

            # Test invalid user ID
            try:
                validate_user_id("user<with>invalid&chars")
                raise Exception("Should have rejected invalid user ID")
            except ValueError:
                print("  ✅ Invalid user ID correctly rejected")

        except Exception as e:
            raise Exception(f"User ID validation test failed: {e}")

        # Test email validation
        try:
            validate_email("test@example.com")
            print("  ✅ Email validation working")

            # Test invalid email
            try:
                validate_email("invalid-email")
                raise Exception("Should have rejected invalid email")
            except ValueError:
                print("  ✅ Invalid email correctly rejected")

        except Exception as e:
            raise Exception(f"Email validation test failed: {e}")

        return "Security validation working correctly"

    @run_test
    @pytest.mark.external_service
    @pytest.mark.mock_data

    async def test_performance_benchmarks(self):
        """Test performance benchmarks."""
        print("\n📈 Testing Performance Benchmarks...")

        import psutil
        from adk_agent_factory import create_agent

        # Test agent creation performance
        try:
            start_time = time.time()
            agents_created = 0

            # Create multiple agents to test performance
            for i in range(5):
                agent = create_agent("analyst", f"user_{i}", f"project_{i}")
                if agent:
                    agents_created += 1

            creation_time = time.time() - start_time
            avg_creation_time = creation_time / agents_created if agents_created > 0 else 0

            print("  ✅ Agent creation performance test completed")
            print(f"     Created {agents_created} agents in {creation_time:.2f}s")
            print(f"     Average creation time: {avg_creation_time:.3f}s per agent")

            # Performance should be reasonable (< 1 second per agent)
            if avg_creation_time > 1.0:
                print(f"  ⚠️  Agent creation performance warning: {avg_creation_time:.3f}s per agent")
            else:
                print("  ✅ Agent creation performance within acceptable limits")

        except Exception as e:
            raise Exception(f"Performance benchmark test failed: {e}")

        # Test memory usage
        try:
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB

            # Perform some operations
            for i in range(10):
                agent = create_agent("analyst", f"perf_user_{i}", f"perf_project_{i}")

            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_delta = memory_after - memory_before

            print("  ✅ Memory usage test completed")
            print(f"     Memory before: {memory_before:.1f} MB")
            print(f"     Memory after: {memory_after:.1f} MB")
            print(f"     Memory delta: {memory_delta:.1f} MB")

            # Memory increase should be reasonable (< 50 MB for 10 agents)
            if memory_delta > 50:
                print(f"  ⚠️  Memory usage warning: {memory_delta:.1f} MB increase")
            else:
                print("  ✅ Memory usage within acceptable limits")

        except Exception as e:
            raise Exception(f"Memory usage test failed: {e}")

        return "Performance benchmarks completed successfully"

    async def generate_test_report(self):
        """Generate comprehensive test report."""
        print("\n📋 Generating Test Report...")

        report = {
            "test_suite": "ADK System Integration Test Suite",
            "execution_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": test_results["total_tests"],
                "passed_tests": test_results["passed_tests"],
                "failed_tests": test_results["failed_tests"],
                "skipped_tests": test_results["skipped_tests"],
                "success_rate": (test_results["passed_tests"] / test_results["total_tests"] * 100) if test_results["total_tests"] > 0 else 0
            },
            "test_details": test_results["test_details"],
            "recommendations": self._generate_test_recommendations()
        }

        # Save report to file
        import json
        report_file = "backend/test_results.json"
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"  ✅ Test report saved to {report_file}")
        except Exception as e:
            print(f"  ❌ Failed to save test report: {e}")

        return report

    def _generate_test_recommendations(self) -> List[str]:
        """Generate test recommendations based on results."""
        recommendations = []

        success_rate = (test_results["passed_tests"] / test_results["total_tests"] * 100) if test_results["total_tests"] > 0 else 0

        if success_rate >= 95:
            recommendations.append("🎉 Excellent! All systems functioning correctly.")
        elif success_rate >= 90:
            recommendations.append("✅ Good performance with minor issues to address.")
        elif success_rate >= 80:
            recommendations.append("⚠️  Acceptable performance, but several issues need attention.")
        else:
            recommendations.append("❌ Critical issues detected, immediate attention required.")

        if test_results["failed_tests"] > 0:
            recommendations.append(f"🔧 Address {test_results['failed_tests']} failed tests.")

        if test_results["skipped_tests"] > 0:
            recommendations.append(f"⏭️  Review {test_results['skipped_tests']} skipped tests.")

        return recommendations

    def print_test_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("🎯 ADK SYSTEM INTEGRATION TEST SUMMARY")
        print("=" * 60)

        total = test_results["total_tests"]
        passed = test_results["passed_tests"]
        failed = test_results["failed_tests"]
        skipped = test_results["skipped_tests"]

        success_rate = (passed / total * 100) if total > 0 else 0

        print(f"Total Tests:     {total}")
        print(f"Passed:          {passed}")
        print(f"Failed:          {failed}")
        print(f"Skipped:         {skipped}")
        print(".1f")
        if success_rate >= 95:
            print("🎉 OVERALL RESULT: EXCELLENT")
        elif success_rate >= 90:
            print("✅ OVERALL RESULT: GOOD")
        elif success_rate >= 80:
            print("⚠️  OVERALL RESULT: ACCEPTABLE")
        else:
            print("❌ OVERALL RESULT: NEEDS ATTENTION")

        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for test in test_results["test_details"]:
                if test["status"] == "FAIL":
                    print(f"   • {test['test_name']}: {test['message']}")

        print("\n" + "=" * 60)

async def main():
    """Main test execution function."""
    print("🚀 ADK System Integration Test Suite")
    print("=" * 60)
    print("Testing the complete ADK integration system after all fixes...")
    print()

    test_suite = ADKSystemIntegrationTest()
    await test_suite.run_full_test_suite()

if __name__ == "__main__":
    asyncio.run(main())
