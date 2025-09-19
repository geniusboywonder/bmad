# Test Marker Maintenance Report

## Summary

- **Marker Suggestions**: 687
- **Marker Validations**: 0
- **Invalid Markers**: 0

## Marker Suggestions

### High Confidence (>80%)
- **test_workflow_execution** in test_bmad_template_loading.py
  - Suggested: `mock_data`
.1f
  - Reasoning: Test uses mocked dependencies for unit testing

- **test_check_api_health_success** in test_specialized_adk_tools.py
  - Suggested: `external_service`
.1f
  - Reasoning: Test mocks external APIs or services

- **test_check_api_health_unhealthy_response** in test_specialized_adk_tools.py
  - Suggested: `external_service`
.1f
  - Reasoning: Test mocks external APIs or services

- **test_check_api_health_with_method** in test_specialized_adk_tools.py
  - Suggested: `external_service`
.1f
  - Reasoning: Test mocks external APIs or services

- **test_check_api_health_health_indicators** in test_specialized_adk_tools.py
  - Suggested: `external_service`
.1f
  - Reasoning: Test mocks external APIs or services

- **test_load_template_success** in test_template_service.py
  - Suggested: `mock_data`
.1f
  - Reasoning: Test uses mocked dependencies for unit testing

- **test_load_template_parse_error** in test_template_service.py
  - Suggested: `mock_data`
.1f
  - Reasoning: Test uses mocked dependencies for unit testing

- **test_list_available_templates** in test_template_service.py
  - Suggested: `mock_data`
.1f
  - Reasoning: Test uses mocked dependencies for unit testing

- **test_find_template_file** in test_template_service.py
  - Suggested: `mock_data`
.1f
  - Reasoning: Test uses mocked dependencies for unit testing

- **test_list_available_workflows** in test_workflow_service.py
  - Suggested: `mock_data`
.1f
  - Reasoning: Test uses mocked dependencies for unit testing

- **test_find_workflow_file** in test_workflow_service.py
  - Suggested: `mock_data`
.1f
  - Reasoning: Test uses mocked dependencies for unit testing

- **test_create_structured_handoff** in test_adk_handoff_service.py
  - Suggested: `mock_data`
.1f
  - Reasoning: Test uses mocked dependencies for unit testing

- **test_project_with_artifacts** in test_artifact_service.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_create_project_zip_creates_file** in test_artifact_service.py
  - Suggested: `mock_data`
.1f
  - Reasoning: Test uses mocked dependencies for unit testing

- **test_create_project_zip_handles_large_content** in test_artifact_service.py
  - Suggested: `mock_data`
.1f
  - Reasoning: Test uses mocked dependencies for unit testing

- **test_valid_project_model_creation** in test_project_initiation.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_project_model_with_minimal_fields** in test_project_initiation.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_project_model_name_requirements** in test_project_initiation.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_project_model_long_name_handling** in test_project_initiation.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_auto_generate_artifacts_success** in test_project_completion_service.py
  - Suggested: `mock_data`
.1f
  - Reasoning: Test uses mocked dependencies for unit testing

- **test_auto_generate_artifacts_no_artifacts** in test_project_completion_service.py
  - Suggested: `mock_data`
.1f
  - Reasoning: Test uses mocked dependencies for unit testing

- **test_auto_generate_artifacts_error_handling** in test_project_completion_service.py
  - Suggested: `mock_data`
.1f
  - Reasoning: Test uses mocked dependencies for unit testing

- **test_get_project_completion_status_detailed_metrics** in test_project_completion_service.py
  - Suggested: `mock_data`
.1f
  - Reasoning: Test uses mocked dependencies for unit testing

- **test_process_agent_task_failure** in test_agent_tasks.py
  - Suggested: `mock_data`
.1f
  - Reasoning: Test uses mocked dependencies for unit testing

- **test_process_agent_task_with_context** in test_agent_tasks.py
  - Suggested: `mock_data`
.1f
  - Reasoning: Test uses mocked dependencies for unit testing

- **test_process_agent_task_database_error** in test_agent_tasks.py
  - Suggested: `mock_data`
.1f
  - Reasoning: Test uses mocked dependencies for unit testing

- **test_process_agent_task_artifact_creation** in test_agent_tasks.py
  - Suggested: `mock_data`
.1f
  - Reasoning: Test uses mocked dependencies for unit testing

- **test_create_context_artifact** in test_context_persistence_sprint2_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_read_context_artifact_by_id** in test_context_persistence_sprint2_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_update_context_artifact** in test_context_persistence_sprint2_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_delete_context_artifact** in test_context_persistence_sprint2_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_large_volume_artifact_creation** in test_context_persistence_sprint2_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_large_volume_artifact_queries** in test_context_persistence_sprint2_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_concurrent_artifact_operations** in test_context_persistence_sprint2_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_project_persisted_to_database** in test_project_initiation_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_database_transaction_integrity** in test_project_initiation_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_project_database_constraints** in test_project_initiation_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_project_database_relationships** in test_project_initiation_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_initial_task_created_with_project** in test_project_initiation_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_orchestrator_can_create_initial_task** in test_project_initiation_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_initial_task_properties** in test_project_initiation_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_task_database_persistence** in test_project_initiation_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_orchestrator_creates_task_from_valid_handoff** in test_sequential_task_handoff_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_source_task_completion_before_handoff** in test_sequential_task_handoff_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_handoff_task_creation_after_completion** in test_sequential_task_handoff_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_agent_status_updates_during_handoff** in test_sequential_task_handoff_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_invalid_enum_values_fail** in test_database_schema_validation.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_hitl_request_creation_via_orchestrator** in test_hitl_response_handling_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_hitl_request_validation_constraints** in test_hitl_response_handling_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_multiple_hitl_requests_per_project** in test_hitl_response_handling_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_update_context_artifact** in test_context_persistence_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_delete_context_artifact** in test_context_persistence_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_task_status_updates_persisted** in test_context_persistence_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_task_completion_timestamps** in test_context_persistence_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_task_error_state_persistence** in test_context_persistence_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_task_output_data_persistence** in test_context_persistence_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_service_layer_isolates_database_concerns** in test_context_persistence_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

- **test_service_layer_transaction_management** in test_context_persistence_integration.py
  - Suggested: `real_data`
.1f
  - Reasoning: Test appears to use real database operations or service calls

### Medium Confidence (60-80%)
- **test_standardized_input_output_format** in test_llm_providers.py
  - Suggested: `external_service`
.1f

- **test_openai_initialization** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_openai_text_generation** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_openai_error_handling** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_openai_token_counting** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_anthropic_initialization** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_anthropic_text_generation** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_anthropic_rate_limiting** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_gemini_initialization** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_gemini_text_generation** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_gemini_authentication** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_environment_based_mapping** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_load_balancing** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_template_parsing** in test_bmad_template_loading.py
  - Suggested: `mock_data`
.1f

- **test_jinja2_variable_substitution** in test_bmad_template_loading.py
  - Suggested: `mock_data`
.1f

- **test_template_service_initialization** in test_bmad_template_loading.py
  - Suggested: `mock_data`
.1f

- **test_dynamic_template_loading** in test_bmad_template_loading.py
  - Suggested: `mock_data`
.1f

- **test_template_caching** in test_bmad_template_loading.py
  - Suggested: `mock_data`
.1f

- **test_template_inheritance** in test_bmad_template_loading.py
  - Suggested: `mock_data`
.1f

- **test_template_category_organization** in test_bmad_template_loading.py
  - Suggested: `mock_data`
.1f

- **test_parallel_phase_execution** in test_bmad_template_loading.py
  - Suggested: `mock_data`
.1f

- **test_workflow_timeout_handling** in test_bmad_template_loading.py
  - Suggested: `mock_data`
.1f

- **test_template_hot_reload** in test_bmad_template_loading.py
  - Suggested: `mock_data`
.1f

- **test_ai_mediation** in test_hitl_triggers.py
  - Suggested: `mock_data`
.1f

- **test_execute_api_call_success** in test_adk_openapi_tools.py
  - Suggested: `external_service`
.1f

- **test_execute_api_call_with_body** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_execute_api_call_timeout** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_execute_api_call_connection_error** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_execute_with_enterprise_controls_low_risk** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_execute_with_enterprise_controls_high_risk_approved** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_execute_with_enterprise_controls_high_risk_denied** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_execute_with_enterprise_controls_execution_error** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_create_multi_agent_workflow** in test_adk_orchestration_service.py
  - Suggested: `mock_data`
.1f

- **test_create_workflow_with_uninitialized_agent_fails** in test_adk_orchestration_service.py
  - Suggested: `mock_data`
.1f

- **test_get_workflow_status_for_existing_workflow** in test_adk_orchestration_service.py
  - Suggested: `mock_data`
.1f

- **test_list_active_workflows_with_project_filter** in test_adk_orchestration_service.py
  - Suggested: `mock_data`
.1f

- **test_terminate_workflow** in test_adk_orchestration_service.py
  - Suggested: `mock_data`
.1f

- **test_execute_collaborative_analysis_success** in test_adk_orchestration_service.py
  - Suggested: `mock_data`
.1f

- **test_workflow_creation_and_listing_integration** in test_adk_orchestration_service.py
  - Suggested: `mock_data`
.1f

- **test_workflow_lifecycle** in test_adk_orchestration_service.py
  - Suggested: `mock_data`
.1f

- **test_check_deployment_readiness_low_readiness** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_agent_creation_unregistered_type** in test_agent_framework.py
  - Suggested: `mock_data`
.1f

- **test_agent_instance_reuse** in test_agent_framework.py
  - Suggested: `mock_data`
.1f

- **test_force_new_agent_creation** in test_agent_framework.py
  - Suggested: `mock_data`
.1f

- **test_get_existing_agent** in test_agent_framework.py
  - Suggested: `mock_data`
.1f

- **test_get_nonexistent_agent** in test_agent_framework.py
  - Suggested: `mock_data`
.1f

- **test_has_agent** in test_agent_framework.py
  - Suggested: `mock_data`
.1f

- **test_remove_agent** in test_agent_framework.py
  - Suggested: `mock_data`
.1f

- **test_clear_all_agents** in test_agent_framework.py
  - Suggested: `mock_data`
.1f

- **test_factory_status** in test_agent_framework.py
  - Suggested: `mock_data`
.1f

- **test_agent_initialization** in test_agent_framework.py
  - Suggested: `external_service`
.1f

- **test_execute_task** in test_agent_framework.py
  - Suggested: `mock_data`
.1f

- **test_create_handoff** in test_agent_framework.py
  - Suggested: `mock_data`
.1f

- **test_prepare_context_message** in test_agent_framework.py
  - Suggested: `mock_data`
.1f

- **test_get_agent_info** in test_agent_framework.py
  - Suggested: `mock_data`
.1f

- **test_execute_task_with_agent_success** in test_agent_framework.py
  - Suggested: `real_data`
.1f

- **test_create_agent_handoff** in test_agent_framework.py
  - Suggested: `real_data`
.1f

- **test_get_agent_status_summary** in test_agent_framework.py
  - Suggested: `real_data`
.1f

- **test_reset_agent_status** in test_agent_framework.py
  - Suggested: `real_data`
.1f

- **test_get_template_metadata** in test_template_service.py
  - Suggested: `mock_data`
.1f

- **test_load_workflow_success** in test_workflow_service.py
  - Suggested: `mock_data`
.1f

- **test_start_workflow_execution** in test_workflow_service.py
  - Suggested: `mock_data`
.1f

- **test_get_next_agent** in test_workflow_service.py
  - Suggested: `mock_data`
.1f

- **test_generate_handoff** in test_workflow_service.py
  - Suggested: `mock_data`
.1f

- **test_get_workflow_execution_status** in test_workflow_service.py
  - Suggested: `mock_data`
.1f

- **test_get_workflow_metadata** in test_workflow_service.py
  - Suggested: `mock_data`
.1f

- **test_validate_workflow_execution** in test_workflow_service.py
  - Suggested: `mock_data`
.1f

- **test_workflow_definition_validation** in test_workflow_service.py
  - Suggested: `mock_data`
.1f

- **test_workflow_definition_get_methods** in test_workflow_service.py
  - Suggested: `mock_data`
.1f

- **test_create_agent_with_adk** in test_agent_factory_adk.py
  - Suggested: `mock_data`
.1f

- **test_create_agent_without_adk** in test_agent_factory_adk.py
  - Suggested: `mock_data`
.1f

- **test_agent_instance_reuse** in test_agent_factory_adk.py
  - Suggested: `mock_data`
.1f

- **test_agent_instance_recreation_when_adk_changes** in test_agent_factory_adk.py
  - Suggested: `mock_data`
.1f

- **test_factory_lifecycle_methods** in test_agent_factory_adk.py
  - Suggested: `mock_data`
.1f

- **test_get_registered_types** in test_agent_factory_adk.py
  - Suggested: `mock_data`
.1f

- **test_clear_all_agents** in test_agent_factory_adk.py
  - Suggested: `mock_data`
.1f

- **test_successful_call_no_retry** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_retry_on_timeout_error** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_permanent_failure_after_max_retries** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_non_retryable_error_immediate_failure** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_create_handoff_with_invalid_data_fails** in test_adk_handoff_service.py
  - Suggested: `mock_data`
.1f

- **test_create_handoff_with_empty_instructions_fails** in test_adk_handoff_service.py
  - Suggested: `mock_data`
.1f

- **test_create_handoff_with_invalid_priority_fails** in test_adk_handoff_service.py
  - Suggested: `mock_data`
.1f

- **test_get_handoff_status_for_active_handoff** in test_adk_handoff_service.py
  - Suggested: `mock_data`
.1f

- **test_list_active_handoffs** in test_adk_handoff_service.py
  - Suggested: `mock_data`
.1f

- **test_list_active_handoffs_with_project_filter** in test_adk_handoff_service.py
  - Suggested: `mock_data`
.1f

- **test_cancel_handoff** in test_adk_handoff_service.py
  - Suggested: `mock_data`
.1f

- **test_cleanup_completed_handoffs** in test_adk_handoff_service.py
  - Suggested: `mock_data`
.1f

- **test_execute_handoff_with_orchestration_error** in test_adk_handoff_service.py
  - Suggested: `mock_data`
.1f

- **test_full_handoff_lifecycle** in test_adk_handoff_service.py
  - Suggested: `mock_data`
.1f

- **test_register_openapi_tool_success** in test_adk_tool_registry.py
  - Suggested: `external_service`
.1f

- **test_register_openapi_tool_initialization_failure** in test_adk_tool_registry.py
  - Suggested: `external_service`
.1f

- **test_cleanup_inactive_tools** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_service_initializes_with_artifacts_directory** in test_artifact_service.py
  - Suggested: `mock_data`
.1f

- **test_extract_requirements_from_code_artifacts** in test_artifact_service.py
  - Suggested: `mock_data`
.1f

- **test_extract_requirements_filters_stdlib** in test_artifact_service.py
  - Suggested: `mock_data`
.1f

- **test_extract_requirements_handles_from_imports** in test_artifact_service.py
  - Suggested: `mock_data`
.1f

- **test_generate_filename_from_metadata** in test_artifact_service.py
  - Suggested: `mock_data`
.1f

- **test_generate_filename_from_agent_and_type** in test_artifact_service.py
  - Suggested: `mock_data`
.1f

- **test_generate_filename_sanitization** in test_artifact_service.py
  - Suggested: `mock_data`
.1f

- **test_generate_project_summary** in test_artifact_service.py
  - Suggested: `mock_data`
.1f

- **test_generate_readme** in test_artifact_service.py
  - Suggested: `mock_data`
.1f

- **test_cleanup_old_artifacts** in test_artifact_service.py
  - Suggested: `mock_data`
.1f

- **test_notify_artifacts_ready** in test_artifact_service.py
  - Suggested: `mock_data`
.1f

- **test_notify_artifacts_ready_handles_websocket_errors** in test_artifact_service.py
  - Suggested: `mock_data`
.1f

- **test_update_agent_status_with_error_message** in test_agent_status_service.py
  - Suggested: `mock_data`
.1f

- **test_update_agent_status_broadcasts_websocket_event** in test_agent_status_service.py
  - Suggested: `mock_data`
.1f

- **test_invalid_agent_type_handled_gracefully** in test_agent_status_service.py
  - Suggested: `mock_data`
.1f

- **test_concurrent_status_updates** in test_agent_status_service.py
  - Suggested: `mock_data`
.1f

- **test_set_agent_working** in test_agent_status_service.py
  - Suggested: `mock_data`
.1f

- **test_set_agent_idle** in test_agent_status_service.py
  - Suggested: `mock_data`
.1f

- **test_set_agent_waiting_for_hitl** in test_agent_status_service.py
  - Suggested: `mock_data`
.1f

- **test_set_agent_error** in test_agent_status_service.py
  - Suggested: `mock_data`
.1f

- **test_completion_with_completion_indicators_overrides_incomplete_tasks** in test_project_completion_service.py
  - Suggested: `mock_data`
.1f

- **test_handle_project_completion_updates_status** in test_project_completion_service.py
  - Suggested: `mock_data`
.1f

- **test_handle_project_completion_database_error** in test_project_completion_service.py
  - Suggested: `mock_data`
.1f

- **test_force_project_completion_success** in test_project_completion_service.py
  - Suggested: `mock_data`
.1f

- **test_force_project_completion_project_not_found** in test_project_completion_service.py
  - Suggested: `mock_data`
.1f

- **test_force_project_completion_error** in test_project_completion_service.py
  - Suggested: `mock_data`
.1f

- **test_get_project_completion_status_project_not_found** in test_project_completion_service.py
  - Suggested: `mock_data`
.1f

- **test_get_project_completion_status_database_error** in test_project_completion_service.py
  - Suggested: `mock_data`
.1f

- **test_artifact_filtering_by_type** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_artifact_filtering_by_source_agent** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_artifact_content_search** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_artifact_metadata_filtering** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_artifact_sorting_logic** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_crud_transaction_integrity** in test_context_persistence_sprint2_integration.py
  - Suggested: `real_data`
.1f

- **test_create_project_persists_to_database** in test_full_stack_api_database_flow.py
  - Suggested: `mock_data`
.1f

- **test_project_timestamps_auto_population** in test_project_initiation_integration.py
  - Suggested: `real_data`
.1f

- **test_project_creation_empty_request** in test_project_initiation_integration.py
  - Suggested: `real_data`
.1f

- **test_project_creation_missing_name** in test_project_initiation_integration.py
  - Suggested: `real_data`
.1f

- **test_project_creation_invalid_json** in test_project_initiation_integration.py
  - Suggested: `real_data`
.1f

- **test_project_creation_wrong_content_type** in test_project_initiation_integration.py
  - Suggested: `real_data`
.1f

- **test_project_creation_sql_injection_attempt** in test_project_initiation_integration.py
  - Suggested: `real_data`
.1f

- **test_hitl_approval_mock** in test_replace_critical_mocks.py
  - Suggested: `mock_data`
.1f

- **test_hitl_approval_real_db** in test_replace_critical_mocks.py
  - Suggested: `real_data`
.1f

- **test_orchestrator_handles_context_ids_in_handoff** in test_sequential_task_handoff_integration.py
  - Suggested: `real_data`
.1f

- **test_parallel_task_handling_during_handoff** in test_sequential_task_handoff_integration.py
  - Suggested: `real_data`
.1f

- **test_context_artifact_retrieval_for_handoff_task** in test_sequential_task_handoff_integration.py
  - Suggested: `mock_data`
.1f

- **test_multiple_context_artifacts_in_handoff** in test_sequential_task_handoff_integration.py
  - Suggested: `mock_data`
.1f

- **test_context_artifact_filtering_by_relevance** in test_sequential_task_handoff_integration.py
  - Suggested: `mock_data`
.1f

- **test_concurrent_agent_status_management** in test_sequential_task_handoff_integration.py
  - Suggested: `real_data`
.1f

- **test_websocket_events_during_handoff_creation** in test_sequential_task_handoff_integration.py
  - Suggested: `mock_data`
.1f

- **test_real_time_handoff_notifications** in test_sequential_task_handoff_integration.py
  - Suggested: `mock_data`
.1f

- **test_handoff_event_payload_structure** in test_sequential_task_handoff_integration.py
  - Suggested: `mock_data`
.1f

- **test_websocket_notification_boolean_operations** in test_database_schema_validation.py
  - Suggested: `real_data`
.1f

- **test_emergency_stop_boolean_operations** in test_database_schema_validation.py
  - Suggested: `real_data`
.1f

- **test_agent_budget_control_boolean_operations** in test_database_schema_validation.py
  - Suggested: `real_data`
.1f

- **test_task_enum_operations** in test_database_schema_validation.py
  - Suggested: `real_data`
.1f

- **test_websocket_events_on_hitl_request_creation** in test_hitl_response_handling_integration.py
  - Suggested: `mock_data`
.1f

- **test_websocket_events_on_hitl_response_submission** in test_hitl_response_handling_integration.py
  - Suggested: `mock_data`
.1f

- **test_websocket_event_payload_structure** in test_hitl_response_handling_integration.py
  - Suggested: `mock_data`
.1f

- **test_websocket_event_emission_performance** in test_hitl_response_handling_integration.py
  - Suggested: `mock_data`
.1f

- **test_hitl_response_history_creation** in test_hitl_response_handling_integration.py
  - Suggested: `real_data`
.1f

- **test_multiple_hitl_responses_history_tracking** in test_hitl_response_handling_integration.py
  - Suggested: `real_data`
.1f

- **test_hitl_history_with_user_information** in test_hitl_response_handling_integration.py
  - Suggested: `real_data`
.1f

- **test_hitl_history_filtering_and_pagination** in test_hitl_response_handling_integration.py
  - Suggested: `real_data`
.1f

- **test_artifact_creation_event_logging** in test_context_persistence_integration.py
  - Suggested: `real_data`
.1f

- **test_task_status_change_event_logging** in test_context_persistence_integration.py
  - Suggested: `real_data`
.1f

### Low Confidence (<60%)
- **test_abstract_methods_defined** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_provider_interface_contract** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_invalid_provider_type** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_provider_selection_logic** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_cost_tracking_openai** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_cost_tracking_anthropic** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_cost_tracking_gemini** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_usage_aggregation** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_mapping_validation** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_fallback_mapping** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_multi_provider_validation_criteria** in test_llm_providers.py
  - Suggested: `mock_data`
.1f

- **test_orchestrator_alias** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_hitl_alias** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_workflow_aliases** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_autogen_alias** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_template_alias** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_hitl_services_exist** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_workflow_services_exist** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_autogen_services_exist** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_template_services_exist** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_orchestrator_interfaces_exist** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_hitl_interfaces_exist** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_workflow_interfaces_exist** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_autogen_interfaces_exist** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_template_interfaces_exist** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_single_responsibility_principle** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_dependency_inversion_principle** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_interface_segregation_principle** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_orchestrator_line_counts** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_hitl_line_counts** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_workflow_line_counts** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_all_monolithic_services_backed_up** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_refactored_packages_exist** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_interface_layer_complete** in test_solid_refactored_services.py
  - Suggested: `mock_data`
.1f

- **test_parallel_step_execution** in test_workflow_engine.py
  - Suggested: `mock_data`
.1f

- **test_workflow_pause_resume** in test_workflow_engine.py
  - Suggested: `mock_data`
.1f

- **test_workflow_status_tracking** in test_workflow_engine.py
  - Suggested: `mock_data`
.1f

- **test_workflow_error_handling** in test_workflow_engine.py
  - Suggested: `mock_data`
.1f

- **test_hitl_workflow_integration** in test_workflow_engine.py
  - Suggested: `mock_data`
.1f

- **test_hitl_workflow_rejection_handling** in test_workflow_engine.py
  - Suggested: `mock_data`
.1f

- **test_hitl_workflow_amendment_handling** in test_workflow_engine.py
  - Suggested: `mock_data`
.1f

- **test_provider_factory_exists** in test_llm_providers_simple.py
  - Suggested: `mock_data`
.1f

- **test_provider_factory_has_providers** in test_llm_providers_simple.py
  - Suggested: `mock_data`
.1f

- **test_provider_factory_supports_required_providers** in test_llm_providers_simple.py
  - Suggested: `mock_data`
.1f

- **test_get_openai_provider** in test_llm_providers_simple.py
  - Suggested: `mock_data`
.1f

- **test_get_anthropic_provider** in test_llm_providers_simple.py
  - Suggested: `mock_data`
.1f

- **test_get_google_provider** in test_llm_providers_simple.py
  - Suggested: `mock_data`
.1f

- **test_invalid_provider_raises_error** in test_llm_providers_simple.py
  - Suggested: `mock_data`
.1f

- **test_base_provider_is_abstract** in test_llm_providers_simple.py
  - Suggested: `mock_data`
.1f

- **test_base_provider_interface** in test_llm_providers_simple.py
  - Suggested: `mock_data`
.1f

- **test_all_three_providers_available** in test_llm_providers_simple.py
  - Suggested: `mock_data`
.1f

- **test_provider_abstraction_layer_exists** in test_llm_providers_simple.py
  - Suggested: `mock_data`
.1f

- **test_provider_factory_pattern_implemented** in test_llm_providers_simple.py
  - Suggested: `mock_data`
.1f

- **test_get_engine_creation** in test_database_setup.py
  - Suggested: `mock_data`
.1f

- **test_database_tables_exist** in test_database_setup.py
  - Suggested: `mock_data`
.1f

- **test_database_indexes_exist** in test_database_setup.py
  - Suggested: `mock_data`
.1f

- **test_database_migration_status** in test_database_setup.py
  - Suggested: `mock_data`
.1f

- **test_celery_app_configuration** in test_database_setup.py
  - Suggested: `mock_data`
.1f

- **test_celery_app_tasks** in test_database_setup.py
  - Suggested: `mock_data`
.1f

- **test_celery_queue_configuration** in test_database_setup.py
  - Suggested: `mock_data`
.1f

- **test_database_with_proper_indexing** in test_database_setup.py
  - Suggested: `mock_data`
.1f

- **test_redis_backed_celery_operational** in test_database_setup.py
  - Suggested: `mock_data`
.1f

- **test_workflow_states_table_exists** in test_database_setup.py
  - Suggested: `mock_data`
.1f

- **test_context_management_delegation** in test_orchestrator_refactoring.py
  - Suggested: `mock_data`
.1f

- **test_interface_segregation_principle** in test_orchestrator_refactoring.py
  - Suggested: `mock_data`
.1f

- **test_yaml_parser_initialization** in test_bmad_template_loading.py
  - Suggested: `mock_data`
.1f

- **test_template_validation** in test_bmad_template_loading.py
  - Suggested: `mock_data`
.1f

- **test_conditional_logic_evaluation** in test_bmad_template_loading.py
  - Suggested: `mock_data`
.1f

- **test_workflow_definition_creation** in test_bmad_template_loading.py
  - Suggested: `mock_data`
.1f

- **test_workflow_validation** in test_bmad_template_loading.py
  - Suggested: `mock_data`
.1f

- **test_phase_dependency_resolution** in test_bmad_template_loading.py
  - Suggested: `mock_data`
.1f

- **test_workflow_serialization** in test_bmad_template_loading.py
  - Suggested: `mock_data`
.1f

- **test_workflow_engine_initialization** in test_bmad_template_loading.py
  - Suggested: `mock_data`
.1f

- **test_workflow_state_persistence** in test_bmad_template_loading.py
  - Suggested: `mock_data`
.1f

- **test_workflow_error_handling** in test_bmad_template_loading.py
  - Suggested: `mock_data`
.1f

- **test_bmad_core_validation_criteria** in test_bmad_template_loading.py
  - Suggested: `mock_data`
.1f

- **test_conflict_resolver_initialization** in test_conflict_resolution.py
  - Suggested: `mock_data`
.1f

- **test_conflict_resolution_complexity_calculation** in test_conflict_resolution.py
  - Suggested: `mock_data`
.1f

- **test_conflict_escalation_logic** in test_conflict_resolution.py
  - Suggested: `mock_data`
.1f

- **test_conflict_resolution_strategy_recommendation** in test_conflict_resolution.py
  - Suggested: `mock_data`
.1f

- **test_conflict_statistics_tracking** in test_conflict_resolution.py
  - Suggested: `mock_data`
.1f

- **test_content_similarity_calculation** in test_conflict_resolution.py
  - Suggested: `mock_data`
.1f

- **test_conflict_pattern_detection** in test_conflict_resolution.py
  - Suggested: `mock_data`
.1f

- **test_conflict_summary_generation** in test_conflict_resolution.py
  - Suggested: `mock_data`
.1f

- **test_conflict_pattern_report_generation** in test_conflict_resolution.py
  - Suggested: `mock_data`
.1f

- **test_autogen_ext_import** in test_autogen_simple.py
  - Suggested: `mock_data`
.1f

- **test_autogen_core_availability** in test_autogen_simple.py
  - Suggested: `mock_data`
.1f

- **test_autogen_libraries_installed** in test_autogen_simple.py
  - Suggested: `mock_data`
.1f

- **test_assistant_agent_creation** in test_autogen_simple.py
  - Suggested: `mock_data`
.1f

- **test_basic_conversation_pattern_readiness** in test_autogen_simple.py
  - Suggested: `mock_data`
.1f

- **test_identify_missing_autogen_components** in test_autogen_simple.py
  - Suggested: `mock_data`
.1f

- **test_generate_hitl_question_phase_completion** in test_hitl_service_basic.py
  - Suggested: `mock_data`
.1f

- **test_generate_hitl_question_quality_threshold** in test_hitl_service_basic.py
  - Suggested: `mock_data`
.1f

- **test_get_hitl_options_base** in test_hitl_service_basic.py
  - Suggested: `mock_data`
.1f

- **test_get_hitl_options_conflict** in test_hitl_service_basic.py
  - Suggested: `mock_data`
.1f

- **test_validate_hitl_response_approve** in test_hitl_service_basic.py
  - Suggested: `mock_data`
.1f

- **test_validate_hitl_response_amend_without_content** in test_hitl_service_basic.py
  - Suggested: `mock_data`
.1f

- **test_validate_hitl_response_without_comment** in test_hitl_service_basic.py
  - Suggested: `mock_data`
.1f

- **test_get_hitl_response_message** in test_hitl_service_basic.py
  - Suggested: `mock_data`
.1f

- **test_bulk_approval_validation** in test_hitl_service_basic.py
  - Suggested: `mock_data`
.1f

- **test_artifact_storage** in test_context_store_mixed_granularity.py
  - Suggested: `mock_data`
.1f

- **test_artifact_retrieval** in test_context_store_mixed_granularity.py
  - Suggested: `mock_data`
.1f

- **test_context_injection** in test_context_store_mixed_granularity.py
  - Suggested: `mock_data`
.1f

- **test_cache_management** in test_context_store_mixed_granularity.py
  - Suggested: `mock_data`
.1f

- **test_compression_handling** in test_context_store_mixed_granularity.py
  - Suggested: `mock_data`
.1f

- **test_retention_policy** in test_context_store_mixed_granularity.py
  - Suggested: `mock_data`
.1f

- **test_granularity_determination** in test_context_store_mixed_granularity.py
  - Suggested: `mock_data`
.1f

- **test_document_sectioning** in test_context_store_mixed_granularity.py
  - Suggested: `mock_data`
.1f

- **test_concept_extraction** in test_context_store_mixed_granularity.py
  - Suggested: `mock_data`
.1f

- **test_knowledge_unit_creation** in test_context_store_mixed_granularity.py
  - Suggested: `mock_data`
.1f

- **test_redundancy_detection** in test_context_store_mixed_granularity.py
  - Suggested: `mock_data`
.1f

- **test_artifact_relationship_mapping** in test_context_store_mixed_granularity.py
  - Suggested: `mock_data`
.1f

- **test_artifact_versioning** in test_context_store_mixed_granularity.py
  - Suggested: `mock_data`
.1f

- **test_content_complexity_analysis** in test_context_store_mixed_granularity.py
  - Suggested: `mock_data`
.1f

- **test_optimal_granularity_recommendation** in test_context_store_mixed_granularity.py
  - Suggested: `mock_data`
.1f

- **test_section_boundary_detection** in test_context_store_mixed_granularity.py
  - Suggested: `mock_data`
.1f

- **test_concept_relationship_analysis** in test_context_store_mixed_granularity.py
  - Suggested: `mock_data`
.1f

- **test_performance_optimization_recommendations** in test_context_store_mixed_granularity.py
  - Suggested: `mock_data`
.1f

- **test_artifact_validation** in test_context_store_mixed_granularity.py
  - Suggested: `mock_data`
.1f

- **test_artifact_serialization** in test_context_store_mixed_granularity.py
  - Suggested: `mock_data`
.1f

- **test_knowledge_unit_creation** in test_context_store_mixed_granularity.py
  - Suggested: `mock_data`
.1f

- **test_phase_completion_trigger** in test_hitl_triggers.py
  - Suggested: `mock_data`
.1f

- **test_quality_gate_trigger** in test_hitl_triggers.py
  - Suggested: `mock_data`
.1f

- **test_confidence_threshold_trigger** in test_hitl_triggers.py
  - Suggested: `mock_data`
.1f

- **test_hitl_request_creation** in test_hitl_triggers.py
  - Suggested: `mock_data`
.1f

- **test_hitl_request_escalation** in test_hitl_triggers.py
  - Suggested: `mock_data`
.1f

- **test_smart_trigger_logic** in test_hitl_triggers.py
  - Suggested: `mock_data`
.1f

- **test_gate_evaluation** in test_hitl_triggers.py
  - Suggested: `mock_data`
.1f

- **test_build_quality_gate** in test_hitl_triggers.py
  - Suggested: `mock_data`
.1f

- **test_validation_quality_gate** in test_hitl_triggers.py
  - Suggested: `mock_data`
.1f

- **test_gate_waiver_system** in test_hitl_triggers.py
  - Suggested: `mock_data`
.1f

- **test_strict_mode_enforcement** in test_hitl_triggers.py
  - Suggested: `mock_data`
.1f

- **test_conflict_detection** in test_hitl_triggers.py
  - Suggested: `mock_data`
.1f

- **test_conflict_severity_assessment** in test_hitl_triggers.py
  - Suggested: `mock_data`
.1f

- **test_automated_conflict_resolution** in test_hitl_triggers.py
  - Suggested: `mock_data`
.1f

- **test_conflict_escalation** in test_hitl_triggers.py
  - Suggested: `mock_data`
.1f

- **test_conflict_resolution_tracking** in test_hitl_triggers.py
  - Suggested: `mock_data`
.1f

- **test_hitl_request_creation** in test_hitl_triggers.py
  - Suggested: `mock_data`
.1f

- **test_hitl_request_validation** in test_hitl_triggers.py
  - Suggested: `mock_data`
.1f

- **test_request_lifecycle** in test_hitl_triggers.py
  - Suggested: `mock_data`
.1f

- **test_request_serialization** in test_hitl_triggers.py
  - Suggested: `mock_data`
.1f

- **test_tool_initialization_invalid_spec** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_validate_openapi_spec_valid** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_validate_openapi_spec_missing_openapi** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_validate_openapi_spec_missing_info** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_validate_openapi_spec_missing_paths** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_extract_base_url_with_servers** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_extract_base_url_without_servers** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_extract_endpoints** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_extract_security_schemes** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_build_headers_default** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_build_headers_with_custom** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_generate_tool_description** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_get_tool_info** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_assess_api_risk_low** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_assess_api_risk_medium** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_assess_api_risk_high_write_operations** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_assess_api_risk_high_admin_endpoints** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_assess_api_risk_high_sensitive_data** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_sanitize_parameters_for_approval** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_estimate_tokens** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_estimate_response_tokens** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_execute_with_enterprise_controls_not_initialized** in test_adk_openapi_tools.py
  - Suggested: `mock_data`
.1f

- **test_service_initialization** in test_adk_orchestration_service.py
  - Suggested: `mock_data`
.1f

- **test_create_workflow_with_no_agents_fails** in test_adk_orchestration_service.py
  - Suggested: `mock_data`
.1f

- **test_get_workflow_status_for_unknown_workflow** in test_adk_orchestration_service.py
  - Suggested: `mock_data`
.1f

- **test_list_active_workflows** in test_adk_orchestration_service.py
  - Suggested: `mock_data`
.1f

- **test_terminate_unknown_workflow** in test_adk_orchestration_service.py
  - Suggested: `mock_data`
.1f

- **test_get_workflow_config_defaults** in test_adk_orchestration_service.py
  - Suggested: `mock_data`
.1f

- **test_get_workflow_config_requirements_analysis** in test_adk_orchestration_service.py
  - Suggested: `mock_data`
.1f

- **test_get_workflow_config_system_design** in test_adk_orchestration_service.py
  - Suggested: `mock_data`
.1f

- **test_get_workflow_config_with_overrides** in test_adk_orchestration_service.py
  - Suggested: `mock_data`
.1f

- **test_enhance_prompt_with_context** in test_adk_orchestration_service.py
  - Suggested: `mock_data`
.1f

- **test_enhance_prompt_without_context** in test_adk_orchestration_service.py
  - Suggested: `mock_data`
.1f

- **test_cleanup_completed_workflows** in test_adk_orchestration_service.py
  - Suggested: `mock_data`
.1f

- **test_execute_collaborative_analysis_unknown_workflow** in test_adk_orchestration_service.py
  - Suggested: `mock_data`
.1f

- **test_configuration_methods_exist** in test_adk_orchestration_service.py
  - Suggested: `mock_data`
.1f

- **test_analyze_code_quality_simple** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_analyze_code_quality_complex** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_analyze_code_quality_empty** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_analyze_code_quality_with_language** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_analyze_code_quality_error_handling** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_check_api_health_timeout** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_check_api_health_connection_error** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_query_project_metrics_basic** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_query_project_metrics_with_filters** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_query_project_metrics_empty_filters** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_query_project_metrics_agent_performance** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_query_project_metrics_quality_metrics** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_query_project_metrics_timeline** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_analyze_system_architecture_comprehensive** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_analyze_system_architecture_security** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_analyze_system_architecture_performance** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_analyze_system_architecture_scalability** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_analyze_system_architecture_empty_doc** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_analyze_system_architecture_risk_assessment** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_check_deployment_readiness_production** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_check_deployment_readiness_staging** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_check_deployment_readiness_high_readiness** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_check_deployment_readiness_checklist_structure** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_check_deployment_readiness_warnings_and_issues** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_register_specialized_tools** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_get_specialized_tools_for_agent** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_get_tool_capabilities** in test_specialized_adk_tools.py
  - Suggested: `mock_data`
.1f

- **test_global_agent_factory** in test_agent_framework.py
  - Suggested: `mock_data`
.1f

- **test_service_initialization** in test_template_service.py
  - Suggested: `mock_data`
.1f

- **test_load_template_file_not_found** in test_template_service.py
  - Suggested: `mock_data`
.1f

- **test_render_template_success** in test_template_service.py
  - Suggested: `mock_data`
.1f

- **test_render_template_validation_failure** in test_template_service.py
  - Suggested: `mock_data`
.1f

- **test_validate_template_variables** in test_template_service.py
  - Suggested: `mock_data`
.1f

- **test_cache_operations** in test_template_service.py
  - Suggested: `mock_data`
.1f

- **test_format_output_markdown** in test_template_service.py
  - Suggested: `mock_data`
.1f

- **test_format_output_json** in test_template_service.py
  - Suggested: `mock_data`
.1f

- **test_format_output_html** in test_template_service.py
  - Suggested: `mock_data`
.1f

- **test_service_initialization** in test_workflow_service.py
  - Suggested: `mock_data`
.1f

- **test_load_workflow_file_not_found** in test_workflow_service.py
  - Suggested: `mock_data`
.1f

- **test_get_next_agent_no_pending_steps** in test_workflow_service.py
  - Suggested: `mock_data`
.1f

- **test_advance_workflow_execution** in test_workflow_service.py
  - Suggested: `mock_data`
.1f

- **test_advance_workflow_execution_complete** in test_workflow_service.py
  - Suggested: `mock_data`
.1f

- **test_cache_operations** in test_workflow_service.py
  - Suggested: `mock_data`
.1f

- **test_workflow_execution_state_transitions** in test_workflow_service.py
  - Suggested: `mock_data`
.1f

- **test_workflow_step_validation** in test_workflow_service.py
  - Suggested: `mock_data`
.1f

- **test_factory_initialization_with_adk_configs** in test_agent_factory_adk.py
  - Suggested: `mock_data`
.1f

- **test_should_use_adk_logic** in test_agent_factory_adk.py
  - Suggested: `mock_data`
.1f

- **test_adk_rollout_percentage_update** in test_agent_factory_adk.py
  - Suggested: `mock_data`
.1f

- **test_agent_instruction_generation** in test_agent_factory_adk.py
  - Suggested: `mock_data`
.1f

- **test_factory_status_includes_adk_info** in test_agent_factory_adk.py
  - Suggested: `mock_data`
.1f

- **test_error_handling_for_unknown_agent_type** in test_agent_factory_adk.py
  - Suggested: `mock_data`
.1f

- **test_adk_config_completeness** in test_agent_factory_adk.py
  - Suggested: `mock_data`
.1f

- **test_agent_tools_configuration** in test_agent_factory_adk.py
  - Suggested: `mock_data`
.1f

- **test_get_agent_without_instance_fails** in test_agent_factory_adk.py
  - Suggested: `mock_data`
.1f

- **test_get_active_agents** in test_agent_factory_adk.py
  - Suggested: `mock_data`
.1f

- **test_model_configuration_validation** in test_agent_factory_adk.py
  - Suggested: `mock_data`
.1f

- **test_instruction_quality_validation** in test_agent_factory_adk.py
  - Suggested: `mock_data`
.1f

- **test_rollout_configuration_sanity** in test_agent_factory_adk.py
  - Suggested: `mock_data`
.1f

- **test_validate_valid_json_response** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_validate_invalid_json_response** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_validate_oversized_response** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_detect_malicious_content** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_sanitize_content_dict** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_handle_validation_failure_json_recovery** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_handle_validation_failure_malicious_recovery** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_auto_format_detection** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_calculate_backoff_delay** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_should_retry_classification** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_retry_stats_tracking** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_track_successful_request** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_track_failed_request** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_calculate_openai_costs** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_calculate_costs_unknown_model** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_estimate_tokens** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_estimate_tokens_code** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_generate_usage_report_empty_data** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_detect_usage_anomalies_cost_spike** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_detect_usage_anomalies_high_error_rate** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_session_stats_calculation** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_complete_reliability_workflow** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_complete_failure_scenario** in test_llm_reliability.py
  - Suggested: `mock_data`
.1f

- **test_service_initialization** in test_adk_handoff_service.py
  - Suggested: `mock_data`
.1f

- **test_get_handoff_status_for_unknown_handoff** in test_adk_handoff_service.py
  - Suggested: `mock_data`
.1f

- **test_cancel_unknown_handoff** in test_adk_handoff_service.py
  - Suggested: `mock_data`
.1f

- **test_build_handoff_instructions** in test_adk_handoff_service.py
  - Suggested: `mock_data`
.1f

- **test_build_handoff_instructions_minimal** in test_adk_handoff_service.py
  - Suggested: `mock_data`
.1f

- **test_create_handoff_prompt** in test_adk_handoff_service.py
  - Suggested: `mock_data`
.1f

- **test_create_handoff_prompt_minimal_context** in test_adk_handoff_service.py
  - Suggested: `mock_data`
.1f

- **test_validate_handoff_data_success** in test_adk_handoff_service.py
  - Suggested: `mock_data`
.1f

- **test_validate_handoff_data_missing_fields** in test_adk_handoff_service.py
  - Suggested: `mock_data`
.1f

- **test_validate_handoff_data_invalid_priority** in test_adk_handoff_service.py
  - Suggested: `mock_data`
.1f

- **test_execute_handoff_unknown_workflow** in test_adk_handoff_service.py
  - Suggested: `mock_data`
.1f

- **test_registry_initialization** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_register_function_tool_success** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_function** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_register_function_tool_failure** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_unregister_tool_success** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_func** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_unregister_tool_not_found** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_get_tools_for_agent** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_get_tools_for_agent_with_missing_tools** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_get_tool_by_name** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_func** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_update_agent_tool_mapping_success** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_update_agent_tool_mapping_with_invalid_tools** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_get_available_tools** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_get_tool_metadata** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_tool** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_get_registry_status** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_search_tools_by_name** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_search_tools_by_description** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_search_tools_with_type_filter** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_validate_tool_compatibility** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_export_tool_configuration** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_import_tool_configuration_validation** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_full_tool_lifecycle** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_multiple_tool_types_management** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_agent_tool_mapping_edge_cases** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_tool_health_monitoring** in test_adk_tool_registry.py
  - Suggested: `mock_data`
.1f

- **test_project_artifact_creation** in test_artifact_service.py
  - Suggested: `mock_data`
.1f

- **test_project_artifact_default_file_type** in test_artifact_service.py
  - Suggested: `mock_data`
.1f

- **test_extract_content_from_string** in test_artifact_service.py
  - Suggested: `mock_data`
.1f

- **test_extract_content_from_dict_with_content_key** in test_artifact_service.py
  - Suggested: `mock_data`
.1f

- **test_extract_content_from_dict_with_code_key** in test_artifact_service.py
  - Suggested: `mock_data`
.1f

- **test_extract_content_from_dict_no_standard_keys** in test_artifact_service.py
  - Suggested: `mock_data`
.1f

- **test_extract_content_from_other_types** in test_artifact_service.py
  - Suggested: `mock_data`
.1f

- **test_get_agent_status_returns_cached_status** in test_agent_status_service.py
  - Suggested: `mock_data`
.1f

- **test_get_all_agent_statuses_returns_copy** in test_agent_status_service.py
  - Suggested: `mock_data`
.1f

- **test_get_nonexistent_agent_status_returns_none** in test_agent_status_service.py
  - Suggested: `mock_data`
.1f

- **test_project_model_special_characters** in test_project_initiation.py
  - Suggested: `mock_data`
.1f

- **test_valid_task_pydantic_model_creation** in test_project_initiation.py
  - Suggested: `mock_data`
.1f

- **test_task_with_minimal_required_fields** in test_project_initiation.py
  - Suggested: `mock_data`
.1f

- **test_task_database_model_creation** in test_project_initiation.py
  - Suggested: `mock_data`
.1f

- **test_task_invalid_agent_type_validation** in test_project_initiation.py
  - Suggested: `mock_data`
.1f

- **test_task_with_output_and_error_data** in test_project_initiation.py
  - Suggested: `mock_data`
.1f

- **test_valid_project_creation_request_structure** in test_project_initiation.py
  - Suggested: `mock_data`
.1f

- **test_project_creation_request_name_validation** in test_project_initiation.py
  - Suggested: `mock_data`
.1f

- **test_project_creation_request_optional_fields** in test_project_initiation.py
  - Suggested: `mock_data`
.1f

- **test_task_status_enum_values** in test_project_initiation.py
  - Suggested: `mock_data`
.1f

- **test_task_status_enum_usage_in_task** in test_project_initiation.py
  - Suggested: `mock_data`
.1f

- **test_task_status_string_values** in test_project_initiation.py
  - Suggested: `mock_data`
.1f

- **test_task_status_enum_comparison** in test_project_initiation.py
  - Suggested: `mock_data`
.1f

- **test_project_name_length_boundaries** in test_project_initiation.py
  - Suggested: `mock_data`
.1f

- **test_project_name_character_validation** in test_project_initiation.py
  - Suggested: `mock_data`
.1f

- **test_project_name_whitespace_handling** in test_project_initiation.py
  - Suggested: `mock_data`
.1f

- **test_project_name_edge_cases** in test_project_initiation.py
  - Suggested: `mock_data`
.1f

- **test_project_id_uuid_generation** in test_project_initiation.py
  - Suggested: `mock_data`
.1f

- **test_uuid_uniqueness** in test_project_initiation.py
  - Suggested: `mock_data`
.1f

- **test_uuid_format_validation** in test_project_initiation.py
  - Suggested: `mock_data`
.1f

- **test_project_and_task_id_relationship** in test_project_initiation.py
  - Suggested: `mock_data`
.1f

- **test_get_template_requirements_analysis** in test_adk_workflow_templates.py
  - Suggested: `mock_data`
.1f

- **test_get_template_system_design** in test_adk_workflow_templates.py
  - Suggested: `mock_data`
.1f

- **test_get_template_code_review** in test_adk_workflow_templates.py
  - Suggested: `mock_data`
.1f

- **test_get_template_testing_strategy** in test_adk_workflow_templates.py
  - Suggested: `mock_data`
.1f

- **test_get_template_deployment_planning** in test_adk_workflow_templates.py
  - Suggested: `mock_data`
.1f

- **test_get_template_unknown_type_fails** in test_adk_workflow_templates.py
  - Suggested: `mock_data`
.1f

- **test_list_available_templates** in test_adk_workflow_templates.py
  - Suggested: `mock_data`
.1f

- **test_get_template_for_agents_all_available** in test_adk_workflow_templates.py
  - Suggested: `mock_data`
.1f

- **test_get_template_for_agents_partial_availability** in test_adk_workflow_templates.py
  - Suggested: `mock_data`
.1f

- **test_get_template_for_agents_no_matches** in test_adk_workflow_templates.py
  - Suggested: `mock_data`
.1f

- **test_create_custom_template** in test_adk_workflow_templates.py
  - Suggested: `mock_data`
.1f

- **test_workflow_step_creation** in test_adk_workflow_templates.py
  - Suggested: `mock_data`
.1f

- **test_workflow_step_default_values** in test_adk_workflow_templates.py
  - Suggested: `mock_data`
.1f

- **test_workflow_template_creation** in test_adk_workflow_templates.py
  - Suggested: `mock_data`
.1f

- **test_workflow_template_default_fallback_strategies** in test_adk_workflow_templates.py
  - Suggested: `mock_data`
.1f

- **test_workflow_type_values** in test_adk_workflow_templates.py
  - Suggested: `mock_data`
.1f

- **test_workflow_type_string_representation** in test_adk_workflow_templates.py
  - Suggested: `mock_data`
.1f

- **test_event_types_complete** in test_audit_service.py
  - Suggested: `mock_data`
.1f

- **test_event_sources_complete** in test_audit_service.py
  - Suggested: `mock_data`
.1f

- **test_event_log_create_valid** in test_audit_service.py
  - Suggested: `mock_data`
.1f

- **test_event_log_filter_defaults** in test_audit_service.py
  - Suggested: `mock_data`
.1f

- **test_event_log_filter_validation** in test_audit_service.py
  - Suggested: `mock_data`
.1f

- **test_valid_context_artifact_creation** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_context_artifact_required_fields** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_context_artifact_field_types** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_context_artifact_optional_fields** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_context_artifact_immutability_validation** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_all_artifact_types_defined** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_artifact_type_values_consistency** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_artifact_type_uniqueness** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_artifact_type_string_conversion** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_artifact_type_from_string_creation** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_artifact_type_categorization** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_metadata_structure_validation** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_metadata_reserved_fields** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_metadata_size_limits** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_metadata_type_validation** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_metadata_nesting_limits** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_json_content_serialization** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_content_type_preservation** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_large_content_serialization** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_special_character_handling** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_circular_reference_handling** in test_context_persistence_sprint2.py
  - Suggested: `mock_data`
.1f

- **test_event_type_values** in test_event_log_models.py
  - Suggested: `mock_data`
.1f

- **test_event_type_string_representation** in test_event_log_models.py
  - Suggested: `mock_data`
.1f

- **test_event_type_comparison** in test_event_log_models.py
  - Suggested: `mock_data`
.1f

- **test_event_source_values** in test_event_log_models.py
  - Suggested: `mock_data`
.1f

- **test_event_source_string_representation** in test_event_log_models.py
  - Suggested: `mock_data`
.1f

- **test_event_log_create_minimal_valid** in test_event_log_models.py
  - Suggested: `mock_data`
.1f

- **test_event_log_create_full_fields** in test_event_log_models.py
  - Suggested: `mock_data`
.1f

- **test_event_log_create_invalid_event_type** in test_event_log_models.py
  - Suggested: `mock_data`
.1f

- **test_event_log_create_invalid_event_source** in test_event_log_models.py
  - Suggested: `mock_data`
.1f

- **test_event_log_create_missing_required_fields** in test_event_log_models.py
  - Suggested: `mock_data`
.1f

- **test_event_log_create_empty_event_data** in test_event_log_models.py
  - Suggested: `mock_data`
.1f

- **test_event_log_create_complex_event_data** in test_event_log_models.py
  - Suggested: `mock_data`
.1f

- **test_event_log_response_complete** in test_event_log_models.py
  - Suggested: `mock_data`
.1f

- **test_event_log_response_optional_fields_none** in test_event_log_models.py
  - Suggested: `mock_data`
.1f

- **test_event_log_response_json_serialization** in test_event_log_models.py
  - Suggested: `mock_data`
.1f

- **test_event_log_filter_defaults** in test_event_log_models.py
  - Suggested: `mock_data`
.1f

- **test_event_log_filter_with_parameters** in test_event_log_models.py
  - Suggested: `mock_data`
.1f

- **test_event_log_filter_limit_validation** in test_event_log_models.py
  - Suggested: `mock_data`
.1f

- **test_event_log_filter_offset_validation** in test_event_log_models.py
  - Suggested: `mock_data`
.1f

- **test_event_log_filter_date_validation** in test_event_log_models.py
  - Suggested: `mock_data`
.1f

- **test_event_log_filter_enum_validation** in test_event_log_models.py
  - Suggested: `mock_data`
.1f

- **test_event_log_filter_comprehensive_filtering** in test_event_log_models.py
  - Suggested: `mock_data`
.1f

- **test_nonexistent** in test_project_completion_service_real.py
  - Suggested: `mock_data`
.1f

- **test_context_reading_and_creation** in test_adk_context_integration.py
  - Suggested: `mock_data`
.1f

- **test_retrieve_multiple_artifacts_by_ids** in test_context_persistence_sprint2_integration.py
  - Suggested: `mock_data`
.1f

- **test_retrieve_artifacts_with_missing_ids** in test_context_persistence_sprint2_integration.py
  - Suggested: `mock_data`
.1f

- **test_retrieve_artifacts_empty_id_list** in test_context_persistence_sprint2_integration.py
  - Suggested: `mock_data`
.1f

- **test_retrieve_artifacts_cross_project_isolation** in test_context_persistence_sprint2_integration.py
  - Suggested: `mock_data`
.1f

- **test_retrieve_artifacts_performance_with_large_id_list** in test_context_persistence_sprint2_integration.py
  - Suggested: `mock_data`
.1f

- **test_get_all_artifacts_by_project** in test_context_persistence_sprint2_integration.py
  - Suggested: `mock_data`
.1f

- **test_filter_artifacts_by_type_within_project** in test_context_persistence_sprint2_integration.py
  - Suggested: `mock_data`
.1f

- **test_filter_artifacts_by_source_agent_within_project** in test_context_persistence_sprint2_integration.py
  - Suggested: `mock_data`
.1f

- **test_complex_project_artifact_queries** in test_context_persistence_sprint2_integration.py
  - Suggested: `mock_data`
.1f

- **test_artifact_dependency_tracking** in test_context_persistence_sprint2_integration.py
  - Suggested: `mock_data`
.1f

- **test_artifact_version_relationships** in test_context_persistence_sprint2_integration.py
  - Suggested: `mock_data`
.1f

- **test_artifact_reference_integrity** in test_context_persistence_sprint2_integration.py
  - Suggested: `mock_data`
.1f

- **test_update_project_modifies_database** in test_full_stack_api_database_flow.py
  - Suggested: `mock_data`
.1f

- **test_get_projects_matches_database_state** in test_full_stack_api_database_flow.py
  - Suggested: `mock_data`
.1f

- **test_create_task_persists_to_database** in test_full_stack_api_database_flow.py
  - Suggested: `mock_data`
.1f

- **test_task_status_updates_persist_to_database** in test_full_stack_api_database_flow.py
  - Suggested: `mock_data`
.1f

- **test_task_deletion_removes_from_database** in test_full_stack_api_database_flow.py
  - Suggested: `mock_data`
.1f

- **test_create_hitl_request_persists_to_database** in test_full_stack_api_database_flow.py
  - Suggested: `mock_data`
.1f

- **test_emergency_stop_creates_database_record** in test_full_stack_api_database_flow.py
  - Suggested: `mock_data`
.1f

- **test_budget_controls_persist_correctly** in test_full_stack_api_database_flow.py
  - Suggested: `mock_data`
.1f

- **test_workflow_execution_creates_database_records** in test_full_stack_api_database_flow.py
  - Suggested: `mock_data`
.1f

- **test_no_orphaned_records_after_project_deletion** in test_full_stack_api_database_flow.py
  - Suggested: `mock_data`
.1f

- **test_enum_fields_work_correctly_end_to_end** in test_full_stack_api_database_flow.py
  - Suggested: `mock_data`
.1f

- **test_boolean_fields_work_correctly_end_to_end** in test_full_stack_api_database_flow.py
  - Suggested: `mock_data`
.1f

- **test_celery_tasks_are_tracked_in_database** in test_full_stack_api_database_flow.py
  - Suggested: `mock_data`
.1f

- **test_successful_project_creation_via_api** in test_project_initiation_integration.py
  - Suggested: `mock_data`
.1f

- **test_project_creation_minimal_data** in test_project_initiation_integration.py
  - Suggested: `mock_data`
.1f

- **test_project_creation_content_type_validation** in test_project_initiation_integration.py
  - Suggested: `mock_data`
.1f

- **test_project_creation_response_headers** in test_project_initiation_integration.py
  - Suggested: `mock_data`
.1f

- **test_project_status_endpoint** in test_project_initiation_integration.py
  - Suggested: `mock_data`
.1f

- **test_project_status_with_tasks** in test_project_initiation_integration.py
  - Suggested: `mock_data`
.1f

- **test_project_status_nonexistent_project** in test_project_initiation_integration.py
  - Suggested: `mock_data`
.1f

- **test_project_status_task_details** in test_project_initiation_integration.py
  - Suggested: `mock_data`
.1f

- **test_orchestrator_to_analyst_handoff** in test_agent_conversation_flow.py
  - Suggested: `mock_data`
.1f

- **test_hitl_approval_request_real_database** in test_replace_critical_mocks.py
  - Suggested: `mock_data`
.1f

- **test_emergency_stop_real_database** in test_replace_critical_mocks.py
  - Suggested: `mock_data`
.1f

- **test_budget_controls_real_database** in test_replace_critical_mocks.py
  - Suggested: `mock_data`
.1f

- **test_task_creation_real_database** in test_replace_critical_mocks.py
  - Suggested: `mock_data`
.1f

- **test_task_status_updates_real_database** in test_replace_critical_mocks.py
  - Suggested: `mock_data`
.1f

- **test_task_enum_field_validation_real_database** in test_replace_critical_mocks.py
  - Suggested: `mock_data`
.1f

- **test_artifact_creation_real_database** in test_replace_critical_mocks.py
  - Suggested: `mock_data`
.1f

- **test_orchestrator_validates_handoff_before_task_creation** in test_sequential_task_handoff_integration.py
  - Suggested: `mock_data`
.1f

- **test_orchestrator_handles_handoff_priority** in test_sequential_task_handoff_integration.py
  - Suggested: `mock_data`
.1f

- **test_minimal_adk_agent** in test_adk_integration.py
  - Suggested: `mock_data`
.1f

- **test_adk_agent_with_tools** in test_adk_integration.py
  - Suggested: `mock_data`
.1f

- **test_bmad_adk_wrapper_basic** in test_adk_integration.py
  - Suggested: `mock_data`
.1f

- **test_bmad_adk_wrapper_enterprise_features** in test_adk_integration.py
  - Suggested: `mock_data`
.1f

- **test_error_handling** in test_adk_integration.py
  - Suggested: `mock_data`
.1f

- **test_token_and_cost_estimation** in test_adk_integration.py
  - Suggested: `mock_data`
.1f

- **test_hitl_approval_request** in test_adk_integration.py
  - Suggested: `mock_data`
.1f

- **test_audit_trail_integration** in test_adk_integration.py
  - Suggested: `mock_data`
.1f

- **test_wrapper_initialization** in test_adk_integration.py
  - Suggested: `mock_data`
.1f

- **test_database_is_postgresql** in test_database_schema_validation.py
  - Suggested: `mock_data`
.1f

- **test_enum_vs_boolean_consistency** in test_database_schema_validation.py
  - Suggested: `mock_data`
.1f

- **test_enum_fields_are_actually_enums** in test_database_schema_validation.py
  - Suggested: `mock_data`
.1f

- **test_all_required_tables_exist** in test_database_schema_validation.py
  - Suggested: `mock_data`
.1f

- **test_foreign_key_constraints_exist** in test_database_schema_validation.py
  - Suggested: `mock_data`
.1f

- **test_indexes_exist** in test_database_schema_validation.py
  - Suggested: `mock_data`
.1f

- **test_hitl_request_with_expiration_time** in test_hitl_response_handling_integration.py
  - Suggested: `mock_data`
.1f

- **test_hitl_approve_response_processing** in test_hitl_response_handling_integration.py
  - Suggested: `mock_data`
.1f

- **test_hitl_reject_response_processing** in test_hitl_response_handling_integration.py
  - Suggested: `mock_data`
.1f

- **test_hitl_amend_response_processing** in test_hitl_response_handling_integration.py
  - Suggested: `mock_data`
.1f

- **test_hitl_response_error_handling** in test_hitl_response_handling_integration.py
  - Suggested: `mock_data`
.1f

- **test_concurrent_hitl_responses** in test_hitl_response_handling_integration.py
  - Suggested: `mock_data`
.1f

- **test_workflow_resume_after_approval** in test_hitl_response_handling_integration.py
  - Suggested: `mock_data`
.1f

- **test_workflow_handling_after_rejection** in test_hitl_response_handling_integration.py
  - Suggested: `mock_data`
.1f

- **test_workflow_continuation_after_amendment** in test_hitl_response_handling_integration.py
  - Suggested: `mock_data`
.1f

- **test_multi_stage_hitl_workflow** in test_hitl_response_handling_integration.py
  - Suggested: `mock_data`
.1f

- **test_create_context_artifact** in test_context_persistence_integration.py
  - Suggested: `mock_data`
.1f

- **test_get_context_artifact_by_id** in test_context_persistence_integration.py
  - Suggested: `mock_data`
.1f

- **test_get_artifacts_by_project** in test_context_persistence_integration.py
  - Suggested: `mock_data`
.1f

- **test_service_layer_error_handling** in test_context_persistence_integration.py
  - Suggested: `mock_data`
.1f

- **test_event_log_data_integrity** in test_context_persistence_integration.py
  - Suggested: `mock_data`
.1f

- **test_query_performance_with_volume** in test_context_persistence_integration.py
  - Suggested: `mock_data`
.1f

- **test_single_artifact_retrieval_performance** in test_context_persistence_integration.py
  - Suggested: `mock_data`
.1f

- **test_bulk_artifact_retrieval_performance** in test_context_persistence_integration.py
  - Suggested: `mock_data`
.1f

## Recommendations

### Immediate Actions
- Review and apply 687 marker suggestions

### Process Improvements
- Integrate marker validation into CI/CD pipeline
- Set up automated marker suggestion reviews
- Create marker usage guidelines documentation

### Quality Gates
- Require marker validation before merge
- Automate marker compliance checks
- Monitor marker usage trends