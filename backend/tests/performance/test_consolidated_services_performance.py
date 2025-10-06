"""
Performance tests for consolidated services.
Ensures consolidation didn't impact performance.
"""

import pytest
import time
import asyncio
from typing import Dict, Any, List
from unittest.mock import Mock, patch

from app.services.document_service import DocumentService
from app.services.llm_service import LLMService
from tests.utils.database_test_utils import DatabaseTestManager


class TestConsolidatedServicePerformance:
    """Test performance of consolidated services."""
    
    @pytest.fixture
    def performance_timer(self):
        """Utility for measuring test execution time."""
        class Timer:
            def __init__(self):
                self.start_time = None
                self.end_time = None
            
            def start(self):
                self.start_time = time.time()
            
            def stop(self):
                self.end_time = time.time()
            
            @property
            def elapsed_ms(self):
                if self.start_time and self.end_time:
                    return (self.end_time - self.start_time) * 1000
                return None
        
        return Timer()
    
    @pytest.fixture
    def document_service(self):
        """Create DocumentService for performance testing."""
        config = {
            "enable_deduplication": True,
            "enable_conflict_resolution": True,
            "max_section_size": 8192,
            "min_section_size": 512,
            "enable_semantic_sectioning": True
        }
        return DocumentService(config)
    
    @pytest.fixture
    def llm_service(self):
        """Create LLMService for performance testing."""
        return LLMService()
    
    @pytest.fixture
    def large_artifacts(self):
        """Generate large artifacts for performance testing."""
        artifacts = []
        for i in range(100):  # 100 artifacts
            content = f"# Artifact {i}\n" + "This is content for the artifact. " * 200  # ~5KB each
            artifacts.append({
                "id": f"artifact_{i}",
                "content": content,
                "metadata": {"type": "document", "priority": i % 5}
            })
        return artifacts
    
    @pytest.fixture
    def large_content(self):
        """Generate large content for sectioning performance tests."""
        sections = []
        for i in range(50):
            section_content = f"""
## Section {i}

This is section {i} with substantial content to test performance.
{'Content line. ' * 100}

### Subsection {i}.1
{'More content for subsection. ' * 50}

### Subsection {i}.2
{'Additional subsection content. ' * 50}
"""
            sections.append(section_content)
        
        return "\n".join(sections)  # ~500KB total

    # Document Service Performance Tests
    
    @pytest.mark.real_data
    @pytest.mark.performance
    async def test_document_service_large_assembly(self, document_service, large_artifacts, performance_timer):
        """Test document assembly performance with large datasets."""
        performance_timer.start()
        
        result = await document_service.assemble_document(
            artifacts=large_artifacts,
            project_id="performance_test_project"
        )
        
        performance_timer.stop()
        
        # Verify assembly completed successfully
        assert result is not None
        assert "content" in result
        assert result["metadata"]["artifact_count"] == 100
        
        # Performance requirement: should complete within 2000ms
        elapsed_ms = performance_timer.elapsed_ms
        assert elapsed_ms < 2000, f"Document assembly took {elapsed_ms:.2f}ms, exceeding 2000ms threshold"
        
        print(f"Document assembly performance: {elapsed_ms:.2f}ms for 100 artifacts (~500KB)")

    @pytest.mark.real_data
    @pytest.mark.performance
    def test_document_service_large_sectioning(self, document_service, large_content, performance_timer):
        """Test document sectioning performance with large content."""
        performance_timer.start()
        
        sections = document_service.section_document(large_content, "markdown")
        
        performance_timer.stop()
        
        # Verify sectioning completed successfully
        assert isinstance(sections, list)
        assert len(sections) > 0
        
        # Performance requirement: should complete within 1500ms
        elapsed_ms = performance_timer.elapsed_ms
        assert elapsed_ms < 1500, f"Document sectioning took {elapsed_ms:.2f}ms, exceeding 1500ms threshold"
        
        print(f"Document sectioning performance: {elapsed_ms:.2f}ms for ~500KB content, {len(sections)} sections")

    @pytest.mark.real_data
    @pytest.mark.performance
    async def test_document_service_granularity_analysis_bulk(self, document_service, performance_timer):
        """Test granularity analysis performance with multiple documents."""
        # Generate multiple documents of varying complexity
        documents = [
            "Simple document with basic content.",
            "Medium complexity document with multiple sections and requirements. " * 20,
            "Complex document with detailed specifications, multiple stakeholders, and comprehensive requirements. " * 50,
            "Very complex document with extensive technical details, multiple integration points, and complex business logic. " * 100
        ]
        
        performance_timer.start()
        
        # Analyze all documents
        results = []
        for doc in documents * 25:  # 100 total analyses
            result = await document_service.analyze_granularity(doc)
            results.append(result)
        
        performance_timer.stop()
        
        # Verify all analyses completed
        assert len(results) == 100
        for result in results:
            assert "complexity_score" in result
            assert "size_category" in result
        
        # Performance requirement: should complete within 3000ms
        elapsed_ms = performance_timer.elapsed_ms
        assert elapsed_ms < 3000, f"Granularity analysis took {elapsed_ms:.2f}ms, exceeding 3000ms threshold"
        
        print(f"Granularity analysis performance: {elapsed_ms:.2f}ms for 100 documents")

    # LLM Service Performance Tests
    
    @pytest.mark.real_data
    @pytest.mark.performance
    def test_llm_service_usage_tracking_bulk(self, llm_service, performance_timer):
        """Test LLM usage tracking performance with bulk operations."""
        performance_timer.start()
        
        # Track 1000 usage records
        for i in range(1000):
            llm_service.track_usage(
                agent_type=f"agent_{i % 5}",
                provider=["openai", "anthropic", "google"][i % 3],
                model="test_model",
                tokens=100 + (i % 50),
                response_time=1000.0 + (i % 100),
                estimated_cost=0.002 + (i * 0.0001)
            )
        
        performance_timer.stop()
        
        # Verify all usage was tracked
        assert len(llm_service.usage_history) == 1000
        
        # Performance requirement: should complete within 500ms
        elapsed_ms = performance_timer.elapsed_ms
        assert elapsed_ms < 500, f"Usage tracking took {elapsed_ms:.2f}ms, exceeding 500ms threshold"
        
        print(f"LLM usage tracking performance: {elapsed_ms:.2f}ms for 1000 records")

    @pytest.mark.real_data
    @pytest.mark.performance
    def test_llm_service_usage_summary_performance(self, llm_service, performance_timer):
        """Test LLM usage summary generation performance."""
        # Pre-populate with substantial usage data
        for i in range(5000):
            llm_service.track_usage(
                agent_type=f"agent_{i % 10}",
                provider=["openai", "anthropic", "google"][i % 3],
                model=f"model_{i % 5}",
                tokens=50 + (i % 200),
                response_time=500.0 + (i % 2000),
                estimated_cost=0.001 + (i * 0.00001)
            )
        
        from datetime import datetime, timezone, timedelta
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        end_time = datetime.now(timezone.utc)
        
        performance_timer.start()
        
        summary = llm_service.get_usage_summary(start_time, end_time)
        
        performance_timer.stop()
        
        # Verify summary was generated
        assert summary["total_requests"] == 5000
        assert summary["total_tokens"] > 0
        assert "provider_breakdown" in summary
        assert "agent_breakdown" in summary
        
        # Performance requirement: should complete within 1000ms
        elapsed_ms = performance_timer.elapsed_ms
        assert elapsed_ms < 1000, f"Usage summary took {elapsed_ms:.2f}ms, exceeding 1000ms threshold"
        
        print(f"LLM usage summary performance: {elapsed_ms:.2f}ms for 5000 records")

    @pytest.mark.external_service
    @pytest.mark.performance
    async def test_llm_service_retry_performance(self, llm_service, performance_timer):
        """Test LLM retry decorator performance."""
        from app.services.llm_service import RetryConfig
        
        retry_config = RetryConfig(
            max_retries=3,
            base_delay=0.01,  # Very short delay for testing
            max_delay=0.1,
            jitter=False
        )
        
        call_count = 0
        
        @llm_service.with_retry(retry_config)
        async def fast_operation():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.001)  # Minimal delay
            return {"success": True, "call_count": call_count}
        
        performance_timer.start()
        
        # Execute 100 successful operations
        tasks = [fast_operation() for _ in range(100)]
        results = await asyncio.gather(*tasks)
        
        performance_timer.stop()
        
        # Verify all operations completed
        assert len(results) == 100
        for result in results:
            assert result["success"] is True
        
        # Performance requirement: should complete within 2000ms
        elapsed_ms = performance_timer.elapsed_ms
        assert elapsed_ms < 2000, f"Retry operations took {elapsed_ms:.2f}ms, exceeding 2000ms threshold"
        
        print(f"LLM retry performance: {elapsed_ms:.2f}ms for 100 operations")

    # Memory Usage Tests
    
    @pytest.mark.real_data
    @pytest.mark.performance
    def test_document_service_memory_efficiency(self, document_service):
        """Test document service memory efficiency with large datasets."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process large amount of data
        large_artifacts = []
        for i in range(500):  # 500 artifacts, ~2.5MB total
            content = f"# Large Artifact {i}\n" + "Content line. " * 1000  # ~5KB each
            large_artifacts.append({
                "id": f"artifact_{i}",
                "content": content,
                "metadata": {"type": "document"}
            })
        
        # Process the artifacts
        result = asyncio.run(document_service.assemble_document(
            artifacts=large_artifacts,
            project_id="memory_test"
        ))
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100, f"Memory usage increased by {memory_increase:.2f}MB, exceeding 100MB threshold"
        
        print(f"Document service memory usage: {memory_increase:.2f}MB increase for 500 artifacts")

    @pytest.mark.real_data
    @pytest.mark.performance
    def test_llm_service_memory_efficiency(self, llm_service):
        """Test LLM service memory efficiency with large usage history."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Track large number of usage records
        for i in range(10000):
            llm_service.track_usage(
                agent_type=f"agent_{i % 20}",
                provider=["openai", "anthropic", "google"][i % 3],
                model=f"model_{i % 10}",
                tokens=100 + (i % 500),
                response_time=1000.0 + (i % 5000),
                estimated_cost=0.002 + (i * 0.000001)
            )
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB for 10k records)
        assert memory_increase < 50, f"Memory usage increased by {memory_increase:.2f}MB, exceeding 50MB threshold"
        
        print(f"LLM service memory usage: {memory_increase:.2f}MB for 10,000 usage records")

    # Concurrent Performance Tests
    
    @pytest.mark.real_data
    @pytest.mark.performance
    async def test_document_service_concurrent_assembly(self, document_service, performance_timer):
        """Test document service performance under concurrent load."""
        # Create multiple sets of artifacts
        artifact_sets = []
        for set_num in range(10):
            artifacts = []
            for i in range(20):  # 20 artifacts per set
                content = f"# Artifact {set_num}-{i}\n" + "Content. " * 100
                artifacts.append({
                    "id": f"artifact_{set_num}_{i}",
                    "content": content,
                    "metadata": {"set": set_num}
                })
            artifact_sets.append(artifacts)
        
        performance_timer.start()
        
        # Process all sets concurrently
        tasks = [
            document_service.assemble_document(
                artifacts=artifacts,
                project_id=f"concurrent_test_{i}"
            )
            for i, artifacts in enumerate(artifact_sets)
        ]
        
        results = await asyncio.gather(*tasks)
        
        performance_timer.stop()
        
        # Verify all assemblies completed
        assert len(results) == 10
        for result in results:
            assert result["metadata"]["artifact_count"] == 20
        
        # Performance requirement: should complete within 3000ms
        elapsed_ms = performance_timer.elapsed_ms
        assert elapsed_ms < 3000, f"Concurrent assembly took {elapsed_ms:.2f}ms, exceeding 3000ms threshold"
        
        print(f"Concurrent document assembly: {elapsed_ms:.2f}ms for 10 concurrent operations")

    @pytest.mark.real_data
    @pytest.mark.performance
    def test_llm_service_concurrent_tracking(self, llm_service, performance_timer):
        """Test LLM service performance under concurrent usage tracking."""
        import threading
        
        def track_usage_batch(batch_id, count):
            for i in range(count):
                llm_service.track_usage(
                    agent_type=f"agent_{batch_id}_{i}",
                    provider="openai",
                    model="gpt-4o-mini",
                    tokens=100 + i,
                    response_time=1000.0 + i
                )
        
        performance_timer.start()
        
        # Create 10 threads, each tracking 100 usage records
        threads = []
        for batch_id in range(10):
            thread = threading.Thread(target=track_usage_batch, args=(batch_id, 100))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        performance_timer.stop()
        
        # Verify all usage was tracked
        assert len(llm_service.usage_history) == 1000
        
        # Performance requirement: should complete within 1000ms
        elapsed_ms = performance_timer.elapsed_ms
        assert elapsed_ms < 1000, f"Concurrent usage tracking took {elapsed_ms:.2f}ms, exceeding 1000ms threshold"
        
        print(f"Concurrent LLM usage tracking: {elapsed_ms:.2f}ms for 1000 records across 10 threads")

    # Regression Tests (Ensure Consolidation Didn't Hurt Performance)
    
    @pytest.mark.real_data
    @pytest.mark.performance
    async def test_consolidation_performance_regression(self, document_service, llm_service, performance_timer):
        """Test that service consolidation didn't hurt performance compared to baseline."""
        # This test establishes performance baselines for consolidated services
        
        # Document service baseline test
        artifacts = [
            {"id": f"artifact_{i}", "content": f"Content {i}. " * 50}
            for i in range(50)
        ]
        
        performance_timer.start()
        doc_result = await document_service.assemble_document(artifacts, "baseline_test")
        doc_elapsed = performance_timer.elapsed_ms
        performance_timer.stop()
        
        # LLM service baseline test
        performance_timer.start()
        for i in range(500):
            llm_service.track_usage(
                agent_type="baseline_agent",
                provider="openai",
                model="gpt-4o-mini",
                tokens=100,
                response_time=1000.0
            )
        llm_elapsed = performance_timer.elapsed_ms
        performance_timer.stop()
        
        # Performance baselines (these should be reasonable for consolidated services)
        assert doc_elapsed < 1000, f"Document assembly baseline: {doc_elapsed:.2f}ms exceeds 1000ms"
        assert llm_elapsed < 250, f"LLM tracking baseline: {llm_elapsed:.2f}ms exceeds 250ms"
        
        print(f"Performance baselines - Document: {doc_elapsed:.2f}ms, LLM: {llm_elapsed:.2f}ms")

    # Utility Performance Tests
    
    @pytest.mark.mock_data
    @pytest.mark.performance
    def test_performance_measurement_accuracy(self, performance_timer):
        """Test performance timer accuracy."""
        import time
        
        # Test short duration
        performance_timer.start()
        time.sleep(0.1)  # 100ms
        performance_timer.stop()
        
        elapsed = performance_timer.elapsed_ms
        # Should be approximately 100ms (±20ms tolerance)
        assert 80 <= elapsed <= 120, f"Timer accuracy test failed: {elapsed:.2f}ms (expected ~100ms)"
        
        # Test longer duration
        performance_timer.start()
        time.sleep(0.5)  # 500ms
        performance_timer.stop()
        
        elapsed = performance_timer.elapsed_ms
        # Should be approximately 500ms (±50ms tolerance)
        assert 450 <= elapsed <= 550, f"Timer accuracy test failed: {elapsed:.2f}ms (expected ~500ms)"