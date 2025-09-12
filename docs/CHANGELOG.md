# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [QA Fixes] - 2025-09-12

### 🔧 Critical Test Infrastructure Fixes

Following comprehensive QA review, implemented systematic fixes to resolve test failures and improve application stability:

### Fixed

#### Core Service Layer Issues
- **🔧 ContextStoreService Enhancement**: Added missing methods required by architecture specification
  - Implemented `get_artifacts_by_project_and_type()` method for artifact filtering by project and type
  - Implemented `get_artifacts_by_project_and_agent()` method for artifact filtering by project and source agent
  - Enhanced `get_artifacts_by_ids()` method to handle mixed UUID/string input types with automatic conversion
  
- **🔧 AgentType Validation**: Enforced proper enum validation in ContextArtifact model
  - Changed `source_agent` field from `str` to `AgentType` enum to enforce PRD compliance
  - Updated all test fixtures to use valid agent types (ORCHESTRATOR, ANALYST, ARCHITECT, CODER, TESTER, DEPLOYER)
  - Fixed 6 test files with invalid "user" agent references

#### Pydantic v2 Compatibility Improvements
- **🔧 Serialization Standardization**: Migrated from deprecated `json_encoders` to modern `field_serializer`
  - Updated `WebSocketEvent` model with proper UUID and datetime field serializers
  - Fixed `AgentStatusModel` configuration from deprecated `Config` class to `ConfigDict`
  - Updated context persistence tests to use `model_dump(mode="json")` for nested object serialization

- **🔧 Method Migration**: Replaced deprecated Pydantic v1 methods throughout test suite
  - Changed all `.dict()` calls to `model_dump()` in 4 test files
  - Enhanced datetime serialization in metadata fields with proper JSON mode handling

#### Database Integration Fixes
- **🔧 SQLAlchemy Session Management**: Fixed critical session generator usage across test infrastructure
  - Corrected `get_db_session()` to use proper generator pattern with `yield from get_session()`
  - Standardized database dependency injection in API endpoints
  - Fixed session lifecycle management in HITL response processing

- **🔧 UUID Database Handling**: Resolved SQLAlchemy UUID conversion errors
  - Fixed `'str' object has no attribute 'hex'` errors in database queries
  - Enhanced UUID conversion logic to handle both string and UUID object inputs
  - Improved type safety in database operations

#### Test Infrastructure Improvements  
- **🔧 Mock System Fixes**: Corrected test mocking infrastructure
  - Fixed `pytest.mock` import errors by replacing with proper `unittest.mock` imports
  - Corrected WebSocket manager patching from non-existent attribute to module-level global instance
  - Updated 9 test files with proper mock import statements

- **🔧 Test Data Validation**: Enhanced test fixture compatibility
  - Updated all test fixtures to use valid AgentType enum values
  - Fixed source agent validation across E2E, integration, and unit test suites
  - Improved test data consistency and validation

### Changed

#### Enhanced Error Handling
- Improved error messages and validation throughout service layer
- Enhanced UUID conversion with proper error handling for malformed inputs
- Better handling of edge cases in database operations

#### Code Quality Improvements
- Removed deprecated Pydantic v1 patterns across all models
- Enhanced type safety with proper Union types for flexible input handling
- Improved method signatures to handle both string and UUID inputs where appropriate

### Technical Debt Addressed

#### Pydantic v2 Migration
- Completed migration of all remaining Pydantic v1 configuration patterns
- Standardized serialization approach across all models
- Enhanced field validation and type safety

#### Test Suite Reliability
- Fixed systematic issues causing test failures across multiple categories
- Improved test infrastructure stability and reliability
- Enhanced mock system compatibility and usage

### Testing Results

#### Test Success Rate Improvement
- **Integration Tests**: 37/38 tests now passing (97.4% pass rate)
- **Context Persistence**: 47/47 unit tests now passing (100% pass rate)
- **Health Checks**: 3/3 tests passing (100% pass rate)
- **Mock Infrastructure**: All mocking systems now functioning correctly

#### Categories Fixed
- ✅ **Database Session Management**: Fixed generator usage across all tests
- ✅ **Pydantic v2 Compatibility**: Complete migration and serialization fixes
- ✅ **Service Method Implementation**: All architecture-required methods now implemented
- ✅ **UUID Standardization**: Proper handling of UUID/string conversion throughout
- ✅ **Test Infrastructure**: Mock imports and WebSocket patching fixed
- ✅ **Agent Type Validation**: Enum validation enforced per PRD requirements

#### Remaining Issues
- 1 performance test failing due to SQLAlchemy concurrency limitations in parallel operations
- Some deprecation warnings for `datetime.utcnow()` (Python 3.12+ compatibility)

### Migration Notes

#### For Developers
- **Service Usage**: ContextStoreService now supports filtering by type and agent
- **UUID Handling**: Methods now accept both string and UUID inputs with automatic conversion
- **Test Writing**: Use proper AgentType enum values, avoid deprecated "user" agent type
- **Mock Testing**: Import from `unittest.mock`, patch module-level WebSocket manager

#### For API Integration
- Enhanced context artifact filtering capabilities
- More robust UUID handling in API requests
- Improved error messages for validation failures

---

## [Sprint 2] - 2025-09-12

### 🎉 Major Achievements
- **P0 Test Suite Improvement**: Increased pass rate from 49.3% to 78.1% (+28.8% improvement)
- **Fixed 21 failing tests**: Reduced from 37 failed tests to 16 failed tests
- **Sprint 2 Outstanding Work**: Completed all critical deliverables identified in backend/SPRINT2_OUTSTANDING_WORK.md

### Added

#### Database Models
- Added `response_comment` field to `HitlRequestDB` model for storing user response comments
- Added `responded_at` field to `HitlRequestDB` model for tracking response timestamps  
- Added `expiration_time` field to `HitlRequestDB` model as alias for `expires_at` (compatibility)
- Added `SYSTEM_ARCHITECTURE` artifact type to `ArtifactType` enum
- Added `DEPLOYMENT_PACKAGE` artifact type to `ArtifactType` enum

#### Service Methods
- Added `process_hitl_response()` method to `OrchestratorService` for handling HITL approval/rejection/amendment workflows
- Added dual-interface support to `create_task_from_handoff()` method supporting both `HandoffSchema` objects and raw dictionary data
- Added TTL (Time-To-Live) support to `create_hitl_request()` method with `ttl_hours` parameter

#### API Enhancements  
- Enhanced HITL API endpoint `/api/v1/hitl/{request_id}/respond` to set `response_comment` and `responded_at` fields
- Updated HITL response processing to support rejection workflow resumption

### Fixed

#### Critical Database Issues
- **🔧 UUID JSON Serialization**: Fixed critical JSON serialization error when storing UUID objects in database JSON columns (orchestrator.py:182)
  - Context IDs now properly converted to strings before database storage
  - Task model creation properly converts string UUIDs back to UUID objects
  - Affects all task creation and handoff operations

#### Context Persistence Service
- **🔧 Parameter Interface**: Fixed `update_artifact()` method to accept both `context_id` and `artifact_id` parameters for test compatibility
- **🔧 Bulk Retrieval**: Enhanced `get_artifacts_by_ids()` method to properly handle empty and None input lists
- **🔧 Database Transactions**: Improved error handling and transaction integrity in artifact persistence operations

#### HITL Response Processing
- **🔧 Database Integration**: Fixed HITL request creation to properly store expiration times and validation metadata
- **🔧 Workflow Resumption**: Fixed response processing to properly update request status and resume workflows
- **🔧 Error Handling**: Enhanced validation for HITL request parameters and response data

#### Task Handoff Integration  
- **🔧 Schema Compatibility**: Fixed `create_task_from_handoff()` to support integration test interfaces expecting raw dictionary data
- **🔧 Context ID Handling**: Proper conversion of string UUIDs to UUID objects in handoff context processing
- **🔧 Metadata Storage**: Enhanced handoff metadata storage with JSON serialization compatibility

#### Pydantic v2 Compatibility
- **🔧 Configuration Migration**: Migrated all Pydantic models from deprecated `Config` class to `ConfigDict`
  - Updated `ContextArtifact`, `HandoffSchema`, `HitlRequest`, and `HitlResponse` models
- **🔧 Enum Handling**: Removed `use_enum_values=True` to maintain enum object types in model validation
- **🔧 Field Validation**: Enhanced field type validation for proper enum and UUID handling

### Changed

#### Service Layer Improvements
- Enhanced `OrchestratorService.create_hitl_request()` with comprehensive validation:
  - Empty question validation
  - Automatic expiration time calculation
  - Improved error messaging and logging
- Updated handoff metadata storage to be fully JSON serializable
- Improved logging throughout HITL and handoff workflows with structured logging

#### Database Schema Enhancements
- Enhanced `HitlRequestDB` model with additional tracking fields for better audit trails
- Improved JSON column handling across all models to prevent serialization errors

#### API Response Improvements
- Enhanced HITL API responses with proper workflow resumption flags
- Improved error responses with detailed validation messages
- Better handling of edge cases in request processing

### Technical Debt Addressed

#### Code Quality
- Eliminated deprecated Pydantic v1 configuration patterns
- Improved error handling consistency across all service methods  
- Enhanced type safety with proper UUID handling throughout the application
- Added comprehensive validation for user inputs and data transformations

#### Testing Infrastructure
- Fixed integration test compatibility issues with service method interfaces
- Enhanced test data factories to support new model fields
- Improved test coverage for edge cases and error conditions

### Performance Improvements
- Optimized bulk artifact retrieval with early return for empty ID lists
- Enhanced database query efficiency in context persistence operations
- Reduced unnecessary UUID conversions in high-traffic code paths

### Documentation
- Added comprehensive error messages for validation failures
- Enhanced method documentation with parameter descriptions and usage examples
- Improved logging messages for better debugging and monitoring

### Dependencies
- Maintained compatibility with existing Pydantic v2 installation
- No new external dependencies introduced
- All changes use existing project infrastructure

---

## Migration Notes

### For Developers
- **Pydantic Models**: If extending existing models, use `ConfigDict` instead of `Config` class
- **HITL Workflows**: New `process_hitl_response()` method is now the standard for handling user responses
- **Task Handoffs**: `create_task_from_handoff()` now supports both object and dictionary interfaces
- **UUID Handling**: When storing UUIDs in JSON columns, ensure proper string conversion

### For API Consumers
- HITL response endpoints now return additional metadata fields
- Task creation from handoffs supports more flexible input formats
- New artifact types available: `SYSTEM_ARCHITECTURE`, `DEPLOYMENT_PACKAGE`

### Database Changes
- New fields in `hitl_requests` table: `response_comment`, `responded_at`, `expiration_time`
- Enhanced JSON column validation to prevent serialization errors
- Backward compatible - no breaking changes to existing data

---

## Testing Results

### P0 Test Suite Performance
- **Before Sprint 2**: 36 passed, 37 failed (49.3% pass rate)
- **After Sprint 2**: 57 passed, 16 failed (78.1% pass rate)
- **Improvement**: +21 tests fixed, +28.8% pass rate increase

### Test Categories Fixed
- ✅ Context Persistence Integration: 4/4 tests passing
- ✅ Pydantic v2 Compatibility: 2/2 tests passing  
- ✅ UUID Serialization: All database operations fixed
- ✅ HITL Response Processing: 4/6 tests passing
- ✅ Task Handoff Integration: 2/4 tests passing

### Remaining Test Failures (16 tests)
- E2E workflow coordination (4 tests) - Complex integration scenarios
- HITL integration timing (2 tests) - Timezone and timing edge cases
- Project initiation (2 tests) - API layer integration issues
- Task handoff edge cases (2 tests) - Complex data type handling
- Unit test edge cases (4 tests) - Model validation scenarios

---

*Sprint 2 completion represents a significant stability improvement to the BMAD backend, with enhanced reliability, better error handling, and improved developer experience.*