# Test Marker Compliance Analysis Report

## Executive Summary

- **Total Test Files Analyzed**: 68
- **Total Tests Found**: 1024
- **Tests with Markers**: 634
- **Tests without Markers**: 390
- **Inappropriate Mocks Found**: 8
.1f

## Marker Distribution

| Marker Type | Count | Percentage |
|-------------|-------|------------|
| real_data | 150 | 14.6% |
| external_service | 23 | 2.2% |
| mock_data | 461 | 45.0% |

## Files Requiring Updates

### test_adk_enterprise_integration.py
- **Location**: tests/test_adk_enterprise_integration.py
.1f
- **Total Tests**: 0
- **Marked Tests**: 0
- **Unmarked Tests**: 0
- **Inappropriate Mocks**: 0

### test_autogen_conversation.py
- **Location**: tests/test_autogen_conversation.py
.1f
- **Total Tests**: 26
- **Marked Tests**: 18
- **Unmarked Tests**: 8
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_conversation_execution
- test_conversation_timeout_handling
- test_agent_registration
- test_conversation_flow
- test_speaker_selection_logic
- test_conflict_resolution
- test_conversation_termination_conditions
- test_full_conversation_workflow

### test_orchestrator_services_real.py
- **Location**: tests/test_orchestrator_services_real.py
.1f
- **Total Tests**: 16
- **Marked Tests**: 7
- **Unmarked Tests**: 9
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_create_project_real_db
- test_advance_project_phase_real_db
- test_assign_agent_to_task_real_db
- test_get_available_agents_real_db
- test_execute_workflow_step_real_db
- test_get_workflow_state_real_db
- test_create_handoff_real_db
- test_store_context_real_db
- test_retrieve_context_real_db

### test_adk_dev_tools.py
- **Location**: tests/test_adk_dev_tools.py
.1f
- **Total Tests**: 6
- **Marked Tests**: 0
- **Unmarked Tests**: 6
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_dev_ui_initialization
- test_test_scenarios
- test_benchmarking_tools
- test_development_dashboard
- test_agent_integration_simulation
- test_hitl_simulation

### test_adk_tools.py
- **Location**: tests/test_adk_tools.py
.1f
- **Total Tests**: 4
- **Marked Tests**: 0
- **Unmarked Tests**: 4
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_tool_registry
- test_tool_execution
- test_openapi_registration
- test_tool_integration_with_agent

### test_llm_providers.py
- **Location**: tests/test_llm_providers.py
.1f
- **Total Tests**: 26
- **Marked Tests**: 25
- **Unmarked Tests**: 1
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_provider_failover

### test_adk_integration.py
- **Location**: tests/test_adk_integration.py
.1f
- **Total Tests**: 2
- **Marked Tests**: 0
- **Unmarked Tests**: 2
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_adk_analyst_agent
- test_fallback_functionality

### test_hitl_safety_real_db.py
- **Location**: tests/test_hitl_safety_real_db.py
.1f
- **Total Tests**: 12
- **Marked Tests**: 0
- **Unmarked Tests**: 12
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_create_approval_request_success_real_db
- test_budget_limit_check_success_real_db
- test_budget_limit_check_exceeded_real_db
- test_emergency_stop_trigger_real_db
- test_emergency_stop_deactivation_real_db
- test_budget_usage_update_real_db
- test_full_hitl_workflow_real_db
- test_budget_limit_workflow_real_db
- test_emergency_stop_boolean_field_real_db
- test_agent_budget_control_boolean_field_real_db
- test_response_approval_boolean_field_real_db
- test_websocket_notification_boolean_fields_real_db

### test_bmad_integration.py
- **Location**: tests/test_bmad_integration.py
.1f
- **Total Tests**: 9
- **Marked Tests**: 0
- **Unmarked Tests**: 9
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_project_creation
- test_context_store_integration
- test_agent_orchestration
- test_time_conscious_orchestration
- test_context_granularity
- test_hitl_integration
- test_workflow_execution
- test_performance_analytics
- test_deployment_integration

### test_hitl_safety.py
- **Location**: tests/test_hitl_safety.py
.1f
- **Total Tests**: 12
- **Marked Tests**: 2
- **Unmarked Tests**: 10
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_create_approval_request_success
- test_budget_limit_check_success
- test_budget_limit_check_exceeded
- test_emergency_stop_trigger
- test_emergency_stop_deactivation
- test_wait_for_approval_timeout
- test_wait_for_approval_approved
- test_budget_usage_update
- test_calculate_cost
- test_execute_with_hitl_control_success

### test_workflow_engine.py
- **Location**: tests/test_workflow_engine.py
.1f
- **Total Tests**: 17
- **Marked Tests**: 8
- **Unmarked Tests**: 9
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_execute_workflow_step
- test_parallel_step_execution
- test_workflow_pause_resume
- test_workflow_recovery
- test_workflow_with_hitl_interaction
- test_workflow_error_handling
- test_hitl_workflow_integration
- test_hitl_workflow_rejection_handling
- test_hitl_workflow_amendment_handling

### test_llm_providers_simple.py
- **Location**: tests/test_llm_providers_simple.py
.1f
- **Total Tests**: 13
- **Marked Tests**: 12
- **Unmarked Tests**: 1
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_provider_interface_compliance

### test_bmad_template_loading.py
- **Location**: tests/test_bmad_template_loading.py
.1f
- **Total Tests**: 23
- **Marked Tests**: 22
- **Unmarked Tests**: 1
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_full_template_loading_workflow

### test_workflow_engine_real_db.py
- **Location**: tests/test_workflow_engine_real_db.py
.1f
- **Total Tests**: 12
- **Marked Tests**: 3
- **Unmarked Tests**: 9
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_workflow_state_persistence_real_db
- test_workflow_recovery_real_db
- test_workflow_step_task_integration_real_db
- test_project_creation_real_db
- test_task_creation_and_status_updates_real_db
- test_hitl_request_lifecycle_real_db
- test_workflow_state_constraint_validation_real_db
- test_invalid_project_reference_real_db
- test_multiple_workflow_states_real_db

### test_conflict_resolution.py
- **Location**: tests/test_conflict_resolution.py
.1f
- **Total Tests**: 17
- **Marked Tests**: 9
- **Unmarked Tests**: 8
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_detect_output_contradictions
- test_detect_requirement_mismatches
- test_detect_design_inconsistencies
- test_detect_resource_contentions
- test_automatic_merge_resolution
- test_compromise_resolution
- test_priority_based_resolution
- test_escalation_resolution

### test_health.py
- **Location**: tests/test_health.py
.1f
- **Total Tests**: 14
- **Marked Tests**: 7
- **Unmarked Tests**: 7
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_check_llm_providers_openai_configured_healthy
- test_check_llm_providers_openai_authentication_error
- test_check_llm_providers_openai_rate_limit_error
- test_check_llm_providers_openai_timeout_error
- test_check_llm_providers_anthropic_configured
- test_check_llm_providers_google_configured
- test_check_llm_providers_all_not_configured

### test_hitl_service_basic.py
- **Location**: tests/test_hitl_service_basic.py
.1f
- **Total Tests**: 15
- **Marked Tests**: 13
- **Unmarked Tests**: 2
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_cleanup_expired_requests
- test_get_hitl_statistics_empty

### test_adk_system_integration.py
- **Location**: tests/test_adk_system_integration.py
.1f
- **Total Tests**: 12
- **Marked Tests**: 0
- **Unmarked Tests**: 12
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_module_imports
- test_core_functionality
- test_agent_factory_integration
- test_feature_flags_system
- test_performance_optimization
- test_multi_model_features
- test_custom_tools_integration
- test_observability_system
- test_configuration_management
- test_error_handling_resilience
- test_security_validation
- test_performance_benchmarks

### test_adk_openapi_tools.py
- **Location**: tests/unit/test_adk_openapi_tools.py
.1f
- **Total Tests**: 31
- **Marked Tests**: 21
- **Unmarked Tests**: 10
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_tool_initialization_invalid_spec
- test_execute_api_call_success
- test_execute_api_call_with_body
- test_execute_api_call_timeout
- test_execute_api_call_connection_error
- test_execute_with_enterprise_controls_not_initialized
- test_execute_with_enterprise_controls_low_risk
- test_execute_with_enterprise_controls_high_risk_approved
- test_execute_with_enterprise_controls_high_risk_denied
- test_execute_with_enterprise_controls_execution_error

### test_adk_orchestration_service.py
- **Location**: tests/unit/test_adk_orchestration_service.py
.1f
- **Total Tests**: 22
- **Marked Tests**: 20
- **Unmarked Tests**: 2
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_execute_collaborative_analysis_success
- test_execute_collaborative_analysis_unknown_workflow

### test_specialized_adk_tools.py
- **Location**: tests/unit/test_specialized_adk_tools.py
.1f
- **Total Tests**: 32
- **Marked Tests**: 26
- **Unmarked Tests**: 6
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_check_api_health_success
- test_check_api_health_timeout
- test_check_api_health_connection_error
- test_check_api_health_unhealthy_response
- test_check_api_health_with_method
- test_check_api_health_health_indicators

### test_agent_framework.py
- **Location**: tests/unit/test_agent_framework.py
.1f
- **Total Tests**: 27
- **Marked Tests**: 20
- **Unmarked Tests**: 7
- **Inappropriate Mocks**: 6

**Unmarked Tests**:
- test_execute_task
- test_create_handoff
- test_execute_task_with_agent_success
- test_execute_task_with_agent_failure
- test_create_agent_handoff
- test_get_agent_status_summary
- test_reset_agent_status

**Inappropriate Mocks**:
- test_execute_task_with_agent_success: @patch\(["\']app\.services\.
- test_execute_task_with_agent_failure: @patch\(["\']app\.services\.
- test_create_agent_handoff: @patch\(["\']app\.services\.
- test_get_agent_status_summary: @patch\(["\']app\.services\.
- test_reset_agent_status: @patch\(["\']app\.services\.
- test_get_service_status: @patch\(["\']app\.services\.

### test_llm_reliability.py
- **Location**: tests/unit/test_llm_reliability.py
.1f
- **Total Tests**: 27
- **Marked Tests**: 5
- **Unmarked Tests**: 22
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_validate_valid_json_response
- test_validate_invalid_json_response
- test_validate_oversized_response
- test_detect_malicious_content
- test_sanitize_content_dict
- test_handle_validation_failure_json_recovery
- test_handle_validation_failure_malicious_recovery
- test_auto_format_detection
- test_successful_call_no_retry
- test_retry_on_timeout_error
- test_permanent_failure_after_max_retries
- test_non_retryable_error_immediate_failure
- test_should_retry_classification
- test_track_successful_request
- test_track_failed_request
- test_calculate_openai_costs
- test_calculate_costs_unknown_model
- test_generate_usage_report_empty_data
- test_detect_usage_anomalies_cost_spike
- test_detect_usage_anomalies_high_error_rate
- test_complete_reliability_workflow
- test_complete_failure_scenario

### test_adk_handoff_service.py
- **Location**: tests/unit/test_adk_handoff_service.py
.1f
- **Total Tests**: 22
- **Marked Tests**: 10
- **Unmarked Tests**: 12
- **Inappropriate Mocks**: 1

**Unmarked Tests**:
- test_create_structured_handoff
- test_create_handoff_with_invalid_data_fails
- test_create_handoff_with_empty_instructions_fails
- test_create_handoff_with_invalid_priority_fails
- test_get_handoff_status_for_active_handoff
- test_get_handoff_status_for_unknown_handoff
- test_list_active_handoffs
- test_list_active_handoffs_with_project_filter
- test_cancel_handoff
- test_cancel_unknown_handoff
- test_cleanup_completed_handoffs
- test_full_handoff_lifecycle

**Inappropriate Mocks**:
- test_create_structured_handoff: @patch\(["\']app\.services\.

### test_adk_tool_registry.py
- **Location**: tests/unit/test_adk_tool_registry.py
.1f
- **Total Tests**: 30
- **Marked Tests**: 27
- **Unmarked Tests**: 3
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_function
- test_register_openapi_tool_success
- test_register_openapi_tool_initialization_failure

### test_artifact_service.py
- **Location**: tests/unit/test_artifact_service.py
.1f
- **Total Tests**: 25
- **Marked Tests**: 18
- **Unmarked Tests**: 7
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_generate_project_artifacts_creates_correct_files
- test_generate_project_artifacts_project_not_found
- test_generate_project_artifacts_empty_context
- test_create_project_zip_creates_file
- test_create_project_zip_handles_large_content
- test_notify_artifacts_ready
- test_notify_artifacts_ready_handles_websocket_errors

### test_agent_status_service.py
- **Location**: tests/unit/test_agent_status_service.py
.1f
- **Total Tests**: 16
- **Marked Tests**: 5
- **Unmarked Tests**: 11
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_update_agent_status_creates_correct_model
- test_update_agent_status_with_error_message
- test_update_agent_status_broadcasts_websocket_event
- test_invalid_agent_type_handled_gracefully
- test_concurrent_status_updates
- test_set_agent_working
- test_set_agent_idle
- test_set_agent_waiting_for_hitl
- test_set_agent_error
- test_database_persistence_success
- test_database_persistence_failure_handling

### test_project_initiation.py
- **Location**: tests/unit/test_project_initiation.py
.1f
- **Total Tests**: 25
- **Marked Tests**: 0
- **Unmarked Tests**: 25
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_valid_project_model_creation
- test_project_model_with_minimal_fields
- test_project_model_name_requirements
- test_project_model_long_name_handling
- test_project_model_special_characters
- test_valid_task_pydantic_model_creation
- test_task_with_minimal_required_fields
- test_task_database_model_creation
- test_task_invalid_agent_type_validation
- test_task_with_output_and_error_data
- test_valid_project_creation_request_structure
- test_project_creation_request_name_validation
- test_project_creation_request_optional_fields
- test_task_status_enum_values
- test_task_status_enum_usage_in_task
- test_task_status_string_values
- test_task_status_enum_comparison
- test_project_name_length_boundaries
- test_project_name_character_validation
- test_project_name_whitespace_handling
- test_project_name_edge_cases
- test_project_id_uuid_generation
- test_uuid_uniqueness
- test_uuid_format_validation
- test_project_and_task_id_relationship

### test_audit_service.py
- **Location**: tests/unit/test_audit_service.py
.1f
- **Total Tests**: 13
- **Marked Tests**: 5
- **Unmarked Tests**: 8
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_log_event_success
- test_log_event_database_error
- test_log_task_event
- test_log_hitl_event
- test_get_events_with_filters
- test_get_event_by_id_found
- test_get_event_by_id_not_found
- test_get_events_database_error

### test_project_completion_service.py
- **Location**: tests/unit/test_project_completion_service.py
.1f
- **Total Tests**: 23
- **Marked Tests**: 3
- **Unmarked Tests**: 20
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_completion_detection_all_tasks_completed
- test_completion_detection_mixed_task_states
- test_completion_detection_no_tasks
- test_completion_detection_project_not_found
- test_completion_with_failed_tasks
- test_completion_detection_database_error
- test_completion_with_completion_indicators_overrides_incomplete_tasks
- test_handle_project_completion_updates_status
- test_handle_project_completion_database_error
- test_emit_project_completion_event
- test_emit_project_completion_event_websocket_error
- test_auto_generate_artifacts_success
- test_auto_generate_artifacts_no_artifacts
- test_auto_generate_artifacts_error_handling
- test_force_project_completion_success
- test_force_project_completion_project_not_found
- test_force_project_completion_error
- test_get_project_completion_status_detailed_metrics
- test_get_project_completion_status_project_not_found
- test_get_project_completion_status_database_error

### test_context_persistence_sprint2.py
- **Location**: tests/unit/test_context_persistence_sprint2.py
.1f
- **Total Tests**: 26
- **Marked Tests**: 0
- **Unmarked Tests**: 26
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_valid_context_artifact_creation
- test_context_artifact_required_fields
- test_context_artifact_field_types
- test_context_artifact_optional_fields
- test_context_artifact_immutability_validation
- test_all_artifact_types_defined
- test_artifact_type_values_consistency
- test_artifact_type_uniqueness
- test_artifact_type_string_conversion
- test_artifact_type_from_string_creation
- test_artifact_type_categorization
- test_metadata_structure_validation
- test_metadata_reserved_fields
- test_metadata_size_limits
- test_metadata_type_validation
- test_metadata_nesting_limits
- test_json_content_serialization
- test_content_type_preservation
- test_large_content_serialization
- test_special_character_handling
- test_circular_reference_handling
- test_artifact_filtering_by_type
- test_artifact_filtering_by_source_agent
- test_artifact_content_search
- test_artifact_metadata_filtering
- test_artifact_sorting_logic

### test_agent_tasks_real_db.py
- **Location**: tests/unit/test_agent_tasks_real_db.py
.1f
- **Total Tests**: 12
- **Marked Tests**: 9
- **Unmarked Tests**: 3
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_process_agent_task_database_persistence_real_db
- test_process_agent_task_failure_real_db
- test_process_agent_task_with_context_real_db

### test_project_completion_service_real.py
- **Location**: tests/unit/test_project_completion_service_real.py
.1f
- **Total Tests**: 11
- **Marked Tests**: 5
- **Unmarked Tests**: 6
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_completion_detection_all_tasks_completed_real_db
- test_completion_detection_with_pending_tasks_real_db
- test_artifact_generation_integration_real_services
- test_completion_status_real_db
- test_completion_workflow_end_to_end_real_services
- test_nonexistent

### test_adk_context_integration.py
- **Location**: tests/integration/test_adk_context_integration.py
.1f
- **Total Tests**: 1
- **Marked Tests**: 0
- **Unmarked Tests**: 1
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_context_reading_and_creation

### test_context_persistence_sprint2_integration.py
- **Location**: tests/integration/test_context_persistence_sprint2_integration.py
.1f
- **Total Tests**: 20
- **Marked Tests**: 0
- **Unmarked Tests**: 20
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_create_context_artifact
- test_read_context_artifact_by_id
- test_update_context_artifact
- test_delete_context_artifact
- test_crud_transaction_integrity
- test_retrieve_multiple_artifacts_by_ids
- test_retrieve_artifacts_with_missing_ids
- test_retrieve_artifacts_empty_id_list
- test_retrieve_artifacts_cross_project_isolation
- test_retrieve_artifacts_performance_with_large_id_list
- test_get_all_artifacts_by_project
- test_filter_artifacts_by_type_within_project
- test_filter_artifacts_by_source_agent_within_project
- test_complex_project_artifact_queries
- test_artifact_dependency_tracking
- test_artifact_version_relationships
- test_artifact_reference_integrity
- test_large_volume_artifact_creation
- test_large_volume_artifact_queries
- test_concurrent_artifact_operations

### test_full_stack_api_database_flow.py
- **Location**: tests/integration/test_full_stack_api_database_flow.py
.1f
- **Total Tests**: 14
- **Marked Tests**: 13
- **Unmarked Tests**: 1
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_celery_tasks_are_tracked_in_database

### test_project_initiation_integration.py
- **Location**: tests/integration/test_project_initiation_integration.py
.1f
- **Total Tests**: 22
- **Marked Tests**: 0
- **Unmarked Tests**: 22
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_successful_project_creation_via_api
- test_project_creation_minimal_data
- test_project_creation_content_type_validation
- test_project_creation_response_headers
- test_project_persisted_to_database
- test_database_transaction_integrity
- test_project_database_constraints
- test_project_database_relationships
- test_project_timestamps_auto_population
- test_initial_task_created_with_project
- test_orchestrator_can_create_initial_task
- test_initial_task_properties
- test_task_database_persistence
- test_project_status_endpoint
- test_project_status_with_tasks
- test_project_status_nonexistent_project
- test_project_status_task_details
- test_project_creation_empty_request
- test_project_creation_missing_name
- test_project_creation_invalid_json
- test_project_creation_wrong_content_type
- test_project_creation_sql_injection_attempt

### test_agent_conversation_flow.py
- **Location**: tests/integration/test_agent_conversation_flow.py
.1f
- **Total Tests**: 1
- **Marked Tests**: 0
- **Unmarked Tests**: 1
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_orchestrator_to_analyst_handoff

### test_replace_critical_mocks.py
- **Location**: tests/integration/test_replace_critical_mocks.py
.1f
- **Total Tests**: 9
- **Marked Tests**: 9
- **Unmarked Tests**: 0
- **Inappropriate Mocks**: 1

**Inappropriate Mocks**:
- test_hitl_approval_mock: @patch\(["\']app\.services\.

### test_sequential_task_handoff_integration.py
- **Location**: tests/integration/test_sequential_task_handoff_integration.py
.1f
- **Total Tests**: 15
- **Marked Tests**: 0
- **Unmarked Tests**: 15
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_orchestrator_creates_task_from_valid_handoff
- test_orchestrator_handles_context_ids_in_handoff
- test_orchestrator_validates_handoff_before_task_creation
- test_orchestrator_handles_handoff_priority
- test_source_task_completion_before_handoff
- test_handoff_task_creation_after_completion
- test_parallel_task_handling_during_handoff
- test_context_artifact_retrieval_for_handoff_task
- test_multiple_context_artifacts_in_handoff
- test_context_artifact_filtering_by_relevance
- test_agent_status_updates_during_handoff
- test_concurrent_agent_status_management
- test_websocket_events_during_handoff_creation
- test_real_time_handoff_notifications
- test_handoff_event_payload_structure

### test_adk_integration.py
- **Location**: tests/integration/test_adk_integration.py
.1f
- **Total Tests**: 9
- **Marked Tests**: 1
- **Unmarked Tests**: 8
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_minimal_adk_agent
- test_adk_agent_with_tools
- test_bmad_adk_wrapper_basic
- test_bmad_adk_wrapper_enterprise_features
- test_error_handling
- test_token_and_cost_estimation
- test_hitl_approval_request
- test_audit_trail_integration

### test_adk_websocket_integration.py
- **Location**: tests/integration/test_adk_websocket_integration.py
.1f
- **Total Tests**: 0
- **Marked Tests**: 0
- **Unmarked Tests**: 0
- **Inappropriate Mocks**: 0

### test_hitl_response_handling_integration.py
- **Location**: tests/integration/test_hitl_response_handling_integration.py
.1f
- **Total Tests**: 21
- **Marked Tests**: 0
- **Unmarked Tests**: 21
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_hitl_request_creation_via_orchestrator
- test_hitl_request_with_expiration_time
- test_hitl_request_validation_constraints
- test_multiple_hitl_requests_per_project
- test_hitl_approve_response_processing
- test_hitl_reject_response_processing
- test_hitl_amend_response_processing
- test_hitl_response_error_handling
- test_concurrent_hitl_responses
- test_workflow_resume_after_approval
- test_workflow_handling_after_rejection
- test_workflow_continuation_after_amendment
- test_multi_stage_hitl_workflow
- test_websocket_events_on_hitl_request_creation
- test_websocket_events_on_hitl_response_submission
- test_websocket_event_payload_structure
- test_websocket_event_emission_performance
- test_hitl_response_history_creation
- test_multiple_hitl_responses_history_tracking
- test_hitl_history_with_user_information
- test_hitl_history_filtering_and_pagination

### test_external_services.py
- **Location**: tests/integration/test_external_services.py
.1f
- **Total Tests**: 23
- **Marked Tests**: 20
- **Unmarked Tests**: 3
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_websocket_notification_system
- test_openai_real_api_call
- test_llm_providers_health_check

### test_context_persistence_integration.py
- **Location**: tests/integration/test_context_persistence_integration.py
.1f
- **Total Tests**: 18
- **Marked Tests**: 0
- **Unmarked Tests**: 18
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_create_context_artifact
- test_get_context_artifact_by_id
- test_update_context_artifact
- test_delete_context_artifact
- test_get_artifacts_by_project
- test_task_status_updates_persisted
- test_task_completion_timestamps
- test_task_error_state_persistence
- test_task_output_data_persistence
- test_service_layer_isolates_database_concerns
- test_service_layer_transaction_management
- test_service_layer_error_handling
- test_artifact_creation_event_logging
- test_task_status_change_event_logging
- test_event_log_data_integrity
- test_query_performance_with_volume
- test_single_artifact_retrieval_performance
- test_bulk_artifact_retrieval_performance

### test_agent_task_api_real_db.py
- **Location**: tests/integration/test_agent_task_api_real_db.py
.1f
- **Total Tests**: 2
- **Marked Tests**: 0
- **Unmarked Tests**: 2
- **Inappropriate Mocks**: 0

**Unmarked Tests**:
- test_agent_task_processing_api_real_db
- test_agent_task_failure_api_real_db

## Recommendations

### Immediate Actions
- Add markers to all unmarked tests
- Replace inappropriate database/service mocks with real implementations
- Implement factory-based test data generation

### Process Improvements
- Integrate marker validation into CI/CD pipeline
- Create automated marker suggestion tooling
- Establish marker maintenance workflows

### Quality Gates
- Require 100% marker compliance for all tests
- Block merges with inappropriate mocking patterns
- Automate marker validation in pre-commit hooks