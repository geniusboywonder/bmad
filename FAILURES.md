# Backend Test Failures Report

**Date:** September 12, 2025
**Total Tests:** 243
**Tests Passed:** 183
**Tests Failed:** 60
**Warnings:** 4477 (mostly deprecation warnings)

---

## Summary of Failure Categories:

1.  **`AttributeError: 'generator' object has no attribute 'query'`**: Indicates issues with SQLAlchemy session handling in FastAPI dependencies.
2.  **`AttributeError: module pytest has no attribute mock`**: Incorrect usage of `pytest.mock` for patching.
3.  **`AttributeError: 'ContextStoreService' object has no attribute '...'`**: Missing or misspelled methods in `ContextStoreService`.
4.  **`AssertionError` (Logic Failures)**: Direct mismatches between expected and actual behavior.
5.  **WebSocket-related patching failures**: Mismatch between test assumptions and actual object structure for WebSocket managers.

---

## Detailed Breakdown of Failures:

### Category 1: `AttributeError: 'generator' object has no attribute 'query'`
**Reason:** The `db` dependency in FastAPI routes, which is expected to be a SQLAlchemy Session object, is being treated as a generator. This prevents database queries from executing. This is a critical issue affecting many integration and E2E tests.

*   **Test:** `backend/tests/e2e/test_context_persistence_sprint2_e2e.py::TestAgentWorkflowWithContextPersistence::test_context_artifact_versioning_in_workflow`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/e2e/test_hitl_response_handling_e2e.py::TestCompleteHitlApproveWorkflow::test_hitl_approval_with_conditions`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/e2e/test_hitl_response_handling_e2e.py::TestCompleteHitlAmendWorkflow::test_multi_round_amendment_workflow`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/e2e/test_sequential_task_handoff_e2e.py::TestCompleteSDLCWorkflowExecution::test_workflow_error_recovery`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/e2e/test_sequential_task_handoff_e2e.py::TestMultiPhaseProjectProgression::test_workflow_phase_dependencies`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/e2e/test_sequential_task_handoff_e2e.py::TestMultiPhaseProjectProgression::test_workflow_context_propagation`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/e2e/test_sprint1_critical_paths.py::TestContextPersistenceWorkflow::test_context_persistence_full_workflow`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/e2e/test_sprint1_critical_paths.py::TestCompleteHITLWorkflow::test_complete_hitl_approval_workflow`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/e2e/test_sprint1_critical_paths.py::TestCompleteHITLWorkflow::test_complete_hitl_amendment_workflow`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/e2e/test_sprint1_critical_paths.py::TestCompleteHITLWorkflow::test_hitl_workflow_error_handling`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/e2e/test_sprint1_critical_paths.py::TestFullApplicationHealth::test_application_json_content_handling`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/integration/test_hitl_response_handling_integration.py::TestResponseProcessingWithDBUpdates::test_hitl_approve_response_processing`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/integration/test_hitl_response_handling_integration.py::TestResponseProcessingWithDBUpdates::test_hitl_reject_response_processing`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/integration/test_hitl_response_handling_integration.py::TestResponseProcessingWithDBUpdates::test_hitl_amend_response_processing`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/integration/test_hitl_response_handling_integration.py::TestResponseProcessingWithDBUpdates::test_hitl_response_error_handling`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/integration/test_hitl_response_handling_integration.py::TestResponseProcessingWithDBUpdates::test_concurrent_hitl_responses`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/integration/test_hitl_response_handling_integration.py::TestWorkflowResumeAfterHitlResponse::test_workflow_resume_after_approval`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/integration/test_hitl_response_handling_integration.py::TestWorkflowResumeAfterHitlResponse::test_workflow_handling_after_rejection`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/integration/test_hitl_response_handling_integration.py::TestWorkflowResumeAfterHitlResponse::test_workflow_continuation_after_amendment`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/integration/test_hitl_response_handling_integration.py::TestWorkflowResumeAfterHitlResponse::test_multi_stage_hitl_workflow`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/integration/test_hitl_response_handling_integration.py::TestHitlRequestHistoryTracking::test_hitl_response_history_creation`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/integration/test_hitl_response_handling_integration.py::TestHitlRequestHistoryTracking::test_multiple_hitl_responses_history_tracking`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/integration/test_hitl_response_handling_integration.py::TestHitlRequestHistoryTracking::test_hitl_history_with_user_information`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/integration/test_hitl_response_handling_integration.py::TestHitlRequestHistoryTracking::test_hitl_history_filtering_and_pagination`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/integration/test_project_initiation_integration.py::TestProjectCreationAPI::test_project_creation_minimal_data`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`
*   **Test:** `backend/tests/integration/test_project_initiation_integration.py::TestDatabaseProjectCreation::test_database_transaction_integrity`
    *   **Error:** `AttributeError: 'generator' object has no attribute 'query'`

### Category 2: `AttributeError: module pytest has no attribute mock`
**Reason:** Tests are attempting to use `pytest.mock.patch.object`, but `pytest` does not expose a `mock` attribute directly. This should likely be `unittest.mock.patch.object` or `mocker.patch.object` if `pytest-mock` is installed.

*   **Test:** `backend/tests/e2e/test_context_persistence_sprint2_e2e.py::TestAgentWorkflowWithContextPersistence::test_complete_agent_workflow_with_persistent_context`
    *   **Error:** `AttributeError: module pytest has no attribute mock`
*   **Test:** `backend/tests/e2e/test_hitl_response_handling_e2e.py::TestCompleteHitlApproveWorkflow::test_complete_hitl_approval_workflow`
    *   **Error:** `AttributeError: module pytest has no attribute mock`
*   **Test:** `backend/tests/e2e/test_hitl_response_handling_e2e.py::TestCompleteHitlAmendWorkflow::test_complete_hitl_amendment_workflow`
    *   **Error:** `AttributeError: module pytest has no attribute mock`
*   **Test:** `backend/tests/e2e/test_sequential_task_handoff_e2e.py::TestCompleteSDLCWorkflowExecution::test_complete_sdlc_workflow_execution`
    *   **Error:** `AttributeError: module pytest has no attribute mock`

### Category 3: `AttributeError: 'ContextStoreService' object has no attribute '...'`
**Reason:** The `ContextStoreService` is missing expected methods or they are misspelled. The error message often suggests the correct method name.

*   **Test:** `backend/tests/integration/test_context_persistence_sprint2_integration.py::TestProjectScopedArtifactQueries::test_filter_artifacts_by_type_within_project`
    *   **Error:** `AttributeError: 'ContextStoreService' object has no attribute 'get_artifacts_by_project_and_type'. Did you mean: 'get_artifacts_by_project'?`
*   **Test:** `backend/tests/integration/test_context_persistence_sprint2_integration.py::TestProjectScopedArtifactQueries::test_filter_artifacts_by_source_agent_within_project`
    *   **Error:** `AttributeError: 'ContextStoreService' object has no attribute 'get_artifacts_by_project_and_agent'. Did you mean: 'get_artifacts_by_project'?`
*   **Test:** `backend/tests/integration/test_context_persistence_sprint2_integration.py::TestArtifactRelationshipMaintenance::test_artifact_version_relationships`
    *   **Error:** `AttributeError: 'ContextStoreService' object has no attribute 'get_artifacts_by_project_and_type'. Did you mean: 'get_artifacts_by_project'?`
*   **Test:** `backend/tests/integration/test_context_persistence_sprint2_integration.py::TestContextStorePerformanceWithVolume::test_large_volume_artifact_queries`
    *   **Error:** `AttributeError: 'ContextStoreService' object has no attribute 'get_artifacts_by_project_and_type'. Did you mean: 'get_artifacts_by_project'?`

### Category 4: `AssertionError` (Logic Failures)
**Reason:** The actual behavior of the code does not match the expected outcome defined by the test's assertions.

*   **Test:** `backend/tests/test_health.py::test_detailed_health_check`
    *   **Error:** `AssertionError: assert 'components' in {'detail': {'components': {...}}}`
    *   **Reason:** The test expects `components` at the top level of the response JSON, but it's nested under a `detail` key.
*   **Test:** `backend/tests/e2e/test_sprint1_critical_paths.py::TestFullApplicationHealth::test_application_health_endpoints`
    *   **Error:** `AssertionError: assert 'components' in detailed_data`
    *   **Reason:** Same as `test_detailed_health_check`, `components` is nested.
*   **Test:** `backend/tests/e2e/test_sprint1_critical_paths.py::TestFullApplicationHealth::test_api_endpoint_accessibility`
    *   **Error:** `AssertionError: assert 404 != 404` (or similar, indicating 404 was returned when not expected)
    *   **Reason:** The test expects a non-404 status code for a non-existent HITL request, but the API returns 404. The test's expectation might be incorrect based on the API's design.
*   **Test:** `backend/tests/integration/test_context_persistence_sprint2_integration.py::TestArtifactRelationshipMaintenance::test_artifact_dependency_tracking`
    *   **Error:** `sqlalchemy.exc.StatementError: (builtins.AttributeError) 'str' object has no attribute 'hex'`
    *   **Reason:** A string UUID is being passed where a UUID object is expected, leading to an `AttributeError` when `hex` is called on it.
*   **Test:** `backend/tests/integration/test_context_persistence_sprint2_integration.py::TestContextStorePerformanceWithVolume::test_concurrent_artifact_operations`
    *   **Error:** `AssertionError: assert 0 == 100`
    *   **Reason:** The test expects 100 artifacts to be created concurrently, but 0 were detected, indicating a failure in the concurrent creation logic or its verification.
*   **Test:** `backend/tests/integration/test_hitl_response_handling_integration.py::TestHitlRequestCreationAndPersistence::test_hitl_request_with_expiration_time`
    *   **Error:** `AssertionError: assert 7199.999546 < 60`
    *   **Reason:** The calculated time difference for expiration is much larger than the allowed threshold, suggesting an issue with how `ttl_hours` is used in the expiration time calculation.
*   **Test:** `backend/tests/integration/test_hitl_response_handling_integration.py::TestHitlRequestCreationAndPersistence::test_hitl_request_validation_constraints`
    *   **Error:** `Failed: DID NOT RAISE (<class 'ValueError'>, <class 'AssertionError'>)`
    *   **Reason:** The test expects a `ValueError` or `AssertionError` for invalid input, but no exception was raised.
*   **Test:** `backend/tests/integration/test_project_initiation_integration.py::TestDatabaseProjectCreation::test_project_timestamps_auto_population`
    *   **Error:** `AssertionError: assert datetime.datetime(...) == datetime.datetime(...)`
    *   **Reason:** The `created_at` and `updated_at` timestamps are not exactly equal, likely due to minor time differences during object creation and update.
*   **Test:** `backend/tests/integration/test_sequential_task_handoff_integration.py::TestOrchestratorTaskCreationFromHandoff::test_orchestrator_creates_task_from_valid_handoff`
    *   **Error:** `AssertionError: assert [UUID(...)] == ['...']`
    *   **Reason:** Type mismatch: a list of `UUID` objects is being compared to a list of string representations of UUIDs.
*   **Test:** `backend/tests/integration/test_sequential_task_handoff_integration.py::TestOrchestratorTaskCreationFromHandoff::test_orchestrator_handles_context_ids_in_handoff`
    *   **Error:** `AssertionError: assert '...' in [UUID(...)]`
    *   **Reason:** Type mismatch: a string UUID is being checked for membership in a list of `UUID` objects.
*   **Test:** `backend/tests/integration/test_sequential_task_handoff_integration.py::TestContextArtifactPassingBetweenPhases::test_context_artifact_retrieval_for_handoff_task`
    *   **Error:** `AttributeError: 'ContextArtifact' object has no attribute 'id'`
    *   **Reason:** The `ContextArtifact` Pydantic model uses `context_id` as its primary identifier, not `id`.
*   **Test:** `backend/tests/integration/test_sequential_task_handoff_integration.py::TestContextArtifactPassingBetweenPhases::test_multiple_context_artifacts_in_handoff`
    *   **Error:** `AttributeError: 'ContextArtifact' object has no attribute 'id'`
    *   **Reason:** Same as above, `ContextArtifact` uses `context_id`.
*   **Test:** `backend/tests/integration/test_sequential_task_handoff_integration.py::TestContextArtifactPassingBetweenPhases::test_context_artifact_filtering_by_relevance`
    *   **Error:** `AttributeError: 'ContextArtifact' object has no attribute 'id'`
    *   **Reason:** Same as above, `ContextArtifact` uses `context_id`.
*   **Test:** `backend/tests/unit/test_context_persistence.py::TestContextArtifactModelValidation::test_context_artifact_invalid_fields`
    *   **Error:** `Failed: DID NOT RAISE <class 'pydantic_core._pydantic_core.ValidationError'>`
    *   **Reason:** The test expects a `ValidationError` for invalid fields, but it was not raised.
*   **Test:** `backend/tests/unit/test_context_persistence.py::TestEventLogModelValidation::test_event_log_serialization`
    *   **Error:** `AssertionError: assert False`
    *   **Reason:** `UUID` objects are not being serialized to strings in the `event.dict()` output, causing the `isinstance` check to fail.
*   **Test:** `backend/tests/unit/test_context_persistence.py::TestContextMetadataSerialization::test_datetime_serialization_in_metadata`
    *   **Error:** `AssertionError: assert False`
    *   **Reason:** `datetime` objects are not being serialized to strings in the `artifact.dict()` output, causing the `isinstance` check to fail.
*   **Test:** `backend/tests/unit/test_hitl_response_handling.py::TestHitlRequestStatusTransitions::test_valid_status_transitions`
    *   **Error:** `AttributeError: type object 'HitlStatus' has no attribute 'EXPIRED'`
    *   **Reason:** The `HitlStatus` enum does not have an `EXPIRED` member, but the test attempts to access it.
*   **Test:** `backend/tests/unit/test_hitl_response_handling.py::TestHitlRequestStatusTransitions::test_terminal_status_validation`
    *   **Error:** `AttributeError: type object 'HitlStatus' has no attribute 'EXPIRED'`
    *   **Reason:** Same as above, `HitlStatus` enum does not have an `EXPIRED` member.
*   **Test:** `backend/tests/unit/test_hitl_response_handling.py::TestAmendmentContentValidation::test_amendment_content_formatting`
    *   **Error:** `AssertionError: assert 'This is amen...ltiple spaces' == 'This is amen...ltiple spaces'`
    *   **Reason:** A subtle difference in whitespace or newline handling causes the string comparison to fail.
*   **Test:** `backend/tests/unit/test_hitl_response_handling.py::TestErrorMessageGeneration::test_validation_error_messages`
    *   **Error:** `AssertionError: assert 'invalid_type' in "Field 'comment' must be of correct type"`
    *   **Reason:** The assertion is checking for a substring that is already present in the target string, indicating a logical error in the test's assertion.
*   **Test:** `backend/tests/unit/test_project_initiation.py::TestTaskModelValidation::test_task_invalid_agent_type_validation`
    *   **Error:** `Failed: DID NOT RAISE <class 'pydantic_core._pydantic_core.ValidationError'>`
    *   **Reason:** The test expects a `ValidationError` for an invalid agent type, but it was not raised.

### Category 5: WebSocket-related patching failures
**Reason:** Tests are attempting to patch `websocket_manager` attributes on `orchestrator_service` or `app.api.hitl`, but these attributes do not exist on the respective objects. This indicates a mismatch between the test's assumptions about the object structure and the actual implementation.

*   **Test:** `backend/tests/integration/test_sequential_task_handoff_integration.py::TestWebSocketEventsForHandoffOperations::test_websocket_events_during_handoff_creation`
    *   **Error:** `AttributeError: <app.services.orchestrator.OrchestratorService object at ...> does not have the attribute 'websocket_manager'`
*   **Test:** `backend/tests/integration/test_sequential_task_handoff_integration.py::TestWebSocketEventsForHandoffOperations::test_real_time_handoff_notifications`
    *   **Error:** `AttributeError: <app.services.orchestrator.OrchestratorService object at ...> does not have the attribute 'websocket_manager'`
*   **Test:** `backend/tests/integration/test_hitl_response_handling_integration.py::TestWebSocketEventEmissionForHitl::test_websocket_events_on_hitl_request_creation`
    *   **Error:** `AttributeError: <app.services.orchestrator.OrchestratorService object at ...> does not have the attribute 'websocket_manager'`
*   **Test:** `backend/tests/integration/test_hitl_response_handling_integration.py::TestWebSocketEventEmissionForHitl::test_websocket_events_on_hitl_response_submission`
    *   **Error:** `AttributeError: <module 'app.api.hitl' from ...> does not have the attribute 'websocket_manager'`
*   **Test:** `backend/tests/integration/test_hitl_response_handling_integration.py::TestWebSocketEventEmissionForHitl::test_websocket_event_emission_performance`
    *   **Error:** `AttributeError: <app.services.orchestrator.OrchestratorService object at ...> does not have the attribute 'websocket_manager'`

---

## Warnings Summary:

Numerous warnings are present, primarily related to:
*   **Pydantic V2 Deprecations**: Many warnings about using deprecated features like `extra` keyword arguments on `Field` and class-based `config`. These should be updated to `json_schema_extra` and `ConfigDict` respectively.
*   **`datetime.utcnow()` Deprecation**: Warnings about using `datetime.utcnow()`, which is deprecated. This should be replaced with timezone-aware objects (e.g., `datetime.now(datetime.UTC)`).
*   **FastAPI `on_event` Deprecation**: Warnings about `on_event` being deprecated, suggesting the use of lifespan event handlers.
*   **SQLAlchemy Warnings**: Warnings related to SQLAlchemy usage, such as `SAWarning: Usage of the 'Session.add()' operation is not currently supported within the execution stage of the flush process.`

These warnings indicate areas for code modernization and adherence to best practices, even though they are not causing test failures directly.
