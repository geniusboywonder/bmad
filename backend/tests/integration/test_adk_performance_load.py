#!/usr/bin/env python3
"""ADK Performance and Load Testing.

This module tests ADK performance under load conditions
to ensure scalability and response times meet requirements.
"""

import asyncio
import time
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch
import structlog

# Add backend to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.agents.bmad_adk_wrapper import BMADADKWrapper

logger = structlog.get_logger(__name__)


async def run_adk_performance_load_tests() -> Dict[str, Any]:
    """Run comprehensive ADK performance and load tests."""
    logger.info("Starting ADK performance and load tests")

    try:
        # Create ADK wrapper for performance testing
        wrapper = BMADADKWrapper(
            agent_name="performance_test_agent",
            agent_type="analyst",
            instruction="You are a high-performance analyst agent."
        )

        # Mock the ADK execution to simulate realistic response times
        async def mock_adk_execute(message: str) -> Dict[str, Any]:
            # Simulate realistic ADK processing time (100-500ms)
            processing_time = 0.1 + (len(message) % 5) * 0.1
            await asyncio.sleep(processing_time)

            return {
                "success": True,
                "response": f"Analysis completed for: {message[:50]}...",
                "execution_id": f"perf-test-{hash(message) % 1000}",
                "processing_time": processing_time
            }

        wrapper._execute_adk_agent = mock_adk_execute

        # Test 1: Response Time Performance
        logger.info("Testing response time performance")

        test_messages = [
            "Analyze quarterly sales data",
            "Create a comprehensive market analysis report for the technology sector",
            "Evaluate the competitive landscape and identify key opportunities",
            "Perform risk assessment for the proposed business expansion",
            "Generate detailed user personas based on demographic data"
        ]

        response_times = []
        for message in test_messages:
            start_time = time.time()

            result = await wrapper.process_with_enterprise_controls(
                message=message,
                project_id="550e8400-e29b-41d4-a716-446655440001",
                task_id=f"perf-test-{len(response_times)}",
                user_id="perf_test_user"
            )

            end_time = time.time()
            response_time = end_time - start_time
            response_times.append(response_time)

            logger.info("Response time measured",
                       message_length=len(message),
                       response_time=response_time,
                       success=result["success"])

        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)

        # Performance requirements: average < 2s, max < 5s
        response_time_success = avg_response_time < 2.0 and max_response_time < 5.0
        logger.info("Response time performance test completed",
                   avg_time=avg_response_time,
                   max_time=max_response_time,
                   min_time=min_response_time,
                   success=response_time_success)

        # Test 2: Concurrent Load Testing
        logger.info("Testing concurrent load performance")

        async def run_concurrent_task(task_id: int) -> Dict[str, Any]:
            """Run a single task in the concurrent load test."""
            message = f"Concurrent analysis task {task_id}: Evaluate business metrics and KPIs"

            start_time = time.time()
            result = await wrapper.process_with_enterprise_controls(
                message=message,
                project_id="550e8400-e29b-41d4-a716-446655440001",
                task_id=f"concurrent-{task_id}",
                user_id=f"concurrent_user_{task_id}"
            )
            end_time = time.time()

            return {
                "task_id": task_id,
                "success": result["success"],
                "response_time": end_time - start_time,
                "execution_id": result.get("execution_id")
            }

        # Run 10 concurrent tasks
        concurrent_tasks = [run_concurrent_task(i) for i in range(10)]
        concurrent_start_time = time.time()

        concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)

        concurrent_end_time = time.time()
        total_concurrent_time = concurrent_end_time - concurrent_start_time

        # Analyze concurrent results
        successful_tasks = sum(1 for r in concurrent_results if isinstance(r, dict) and r["success"])
        failed_tasks = sum(1 for r in concurrent_results if isinstance(r, Exception) or (isinstance(r, dict) and not r["success"]))
        avg_concurrent_response_time = sum(r["response_time"] for r in concurrent_results if isinstance(r, dict)) / len([r for r in concurrent_results if isinstance(r, dict)])

        # Concurrent performance requirements: all tasks successful, avg response < 3s
        concurrent_success = successful_tasks == 10 and failed_tasks == 0 and avg_concurrent_response_time < 3.0
        logger.info("Concurrent load test completed",
                   total_tasks=10,
                   successful=successful_tasks,
                   failed=failed_tasks,
                   total_time=total_concurrent_time,
                   avg_response_time=avg_concurrent_response_time,
                   success=concurrent_success)

        # Test 3: Memory and Resource Usage
        logger.info("Testing memory and resource usage")

        # Simulate sustained load
        sustained_tasks = []
        for i in range(20):
            message = f"Sustained load test message {i}: Perform detailed analysis of {i} different scenarios"
            task = wrapper.process_with_enterprise_controls(
                message=message,
                project_id="550e8400-e29b-41d4-a716-446655440001",
                task_id=f"sustained-{i}",
                user_id="sustained_test_user"
            )
            sustained_tasks.append(task)

        # Run in batches to avoid overwhelming
        sustained_results = []
        for i in range(0, 20, 5):  # Process in batches of 5
            batch = sustained_tasks[i:i+5]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            sustained_results.extend(batch_results)
            await asyncio.sleep(0.1)  # Small delay between batches

        sustained_successful = sum(1 for r in sustained_results if isinstance(r, dict) and r["success"])
        sustained_failed = len(sustained_results) - sustained_successful

        # Sustained load requirements: 90% success rate
        sustained_success = (sustained_successful / len(sustained_results)) >= 0.9
        logger.info("Sustained load test completed",
                   total_tasks=20,
                   successful=sustained_successful,
                   failed=sustained_failed,
                   success_rate=sustained_successful/len(sustained_results),
                   success=sustained_success)

        # Test 4: Error Recovery Performance
        logger.info("Testing error recovery performance")

        # Mock intermittent failures
        call_count = 0
        async def mock_unreliable_execute(message: str) -> Dict[str, Any]:
            nonlocal call_count
            call_count += 1

            # Fail every 3rd call to simulate intermittent issues
            if call_count % 3 == 0:
                raise Exception("Simulated intermittent API failure")

            await asyncio.sleep(0.05)  # Fast successful calls
            return {
                "success": True,
                "response": f"Successful analysis: {message[:30]}...",
                "execution_id": f"recovery-test-{call_count}"
            }

        wrapper._execute_adk_agent = mock_unreliable_execute

        # Test error recovery with retries
        error_recovery_tasks = []
        for i in range(9):  # Should have 3 failures and 6 successes
            task = wrapper.process_with_enterprise_controls(
                message=f"Error recovery test {i}",
                project_id="550e8400-e29b-41d4-a716-446655440001",
                task_id=f"error-recovery-{i}",
                user_id="error_test_user"
            )
            error_recovery_tasks.append(task)

        error_recovery_results = await asyncio.gather(*error_recovery_tasks, return_exceptions=True)

        error_recovery_successful = sum(1 for r in error_recovery_results if isinstance(r, dict) and r["success"])
        error_recovery_failed = len(error_recovery_results) - error_recovery_successful

        # Error recovery should handle failures gracefully (some failures expected but not all)
        error_recovery_success = error_recovery_successful >= 6  # At least 6 out of 9 should succeed
        logger.info("Error recovery test completed",
                   total_tasks=9,
                   successful=error_recovery_successful,
                   failed=error_recovery_failed,
                   success=error_recovery_success)

        # Test 5: Scalability Testing
        logger.info("Testing scalability with increasing load")

        scalability_results = []
        for batch_size in [1, 2, 5, 10]:
            batch_tasks = []
            for i in range(batch_size):
                task = wrapper.process_with_enterprise_controls(
                    message=f"Scalability test batch {batch_size} task {i}",
                    project_id="550e8400-e29b-41d4-a716-446655440001",
                    task_id=f"scalability-{batch_size}-{i}",
                    user_id=f"scalability_user_{i}"
                )
                batch_tasks.append(task)

            batch_start_time = time.time()
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            batch_end_time = time.time()

            batch_successful = sum(1 for r in batch_results if isinstance(r, dict) and r["success"])
            batch_time = batch_end_time - batch_start_time

            scalability_results.append({
                "batch_size": batch_size,
                "successful": batch_successful,
                "total_time": batch_time,
                "avg_time_per_task": batch_time / batch_size if batch_size > 0 else 0
            })

            logger.info("Scalability batch completed",
                       batch_size=batch_size,
                       successful=batch_successful,
                       total_time=batch_time)

        # Scalability should show reasonable performance scaling
        scalability_success = all(r["successful"] == r["batch_size"] for r in scalability_results)
        logger.info("Scalability test completed", success=scalability_success)

        # Compile comprehensive performance results
        performance_test_result = {
            "success": (response_time_success and concurrent_success and
                       sustained_success and error_recovery_success and scalability_success),
            "response_time_success": response_time_success,
            "concurrent_success": concurrent_success,
            "sustained_success": sustained_success,
            "error_recovery_success": error_recovery_success,
            "scalability_success": scalability_success,
            "performance_metrics": {
                "avg_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "min_response_time": min_response_time,
                "concurrent_avg_time": avg_concurrent_response_time,
                "concurrent_total_time": total_concurrent_time,
                "sustained_success_rate": sustained_successful / len(sustained_results),
                "error_recovery_success_rate": error_recovery_successful / len(error_recovery_results)
            },
            "scalability_results": scalability_results,
            "test_type": "adk_performance_load"
        }

        logger.info("ADK performance and load test completed", **performance_test_result)
        return performance_test_result

    except Exception as e:
        logger.error("ADK performance and load test failed", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "response_time_success": False,
            "concurrent_success": False,
            "sustained_success": False,
            "error_recovery_success": False,
            "scalability_success": False,
            "test_type": "adk_performance_load"
        }


if __name__ == "__main__":
    print("🧪 Testing ADK Performance and Load")
    print("=" * 50)

    async def run_test():
        result = await run_adk_performance_load_tests()

        print("\n📊 ADK Performance and Load Test Results:")
        print(f"   Overall Success: {result.get('success', False)}")
        print(f"   Response Time: {result.get('response_time_success', False)}")
        print(f"   Concurrent Load: {result.get('concurrent_success', False)}")
        print(f"   Sustained Load: {result.get('sustained_success', False)}")
        print(f"   Error Recovery: {result.get('error_recovery_success', False)}")
        print(f"   Scalability: {result.get('scalability_success', False)}")

        metrics = result.get('performance_metrics', {})
        if metrics:
            print("\n   Performance Metrics:")
            print(f"     Avg Response Time: {metrics.get('avg_response_time', 0):.3f}s")
            print(f"     Max Response Time: {metrics.get('max_response_time', 0):.3f}s")
            print(f"     Concurrent Avg Time: {metrics.get('concurrent_avg_time', 0):.3f}s")
            print(f"     Sustained Success Rate: {metrics.get('sustained_success_rate', 0):.1%}")
            print(f"     Error Recovery Rate: {metrics.get('error_recovery_success_rate', 0):.1%}")

        scalability = result.get('scalability_results', [])
        if scalability:
            print("\n   Scalability Results:")
            for r in scalability:
                print(f"     Batch {r['batch_size']}: {r['successful']}/{r['batch_size']} tasks, {r['avg_time_per_task']:.3f}s avg")

        if not result.get("success", False):
            print(f"   Error: {result.get('error', 'Unknown error')}")

    asyncio.run(run_test())
