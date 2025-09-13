# LLM Reliability Implementation Plan

**Task Focus**: Enhanced reliability features for existing OpenAI integration in AutoGenService
**Scope**: Response validation, retry logic, and usage tracking only
**Timeline**: 1-2 days implementation

## Implementation Overview

This plan focuses on adding **reliability and monitoring capabilities** to the existing OpenAI integration without implementing multi-provider support. The goal is to enhance the current `AutoGenService` with robust error handling, response validation, and comprehensive usage tracking.

## Implementation Steps

### Phase 1: Response Validation & Sanitization (4-5 hours)

#### 1.1 Create Response Validation System
**File**: `backend/app/services/llm_validation.py` (new)

```python
# Key Classes to Implement:
class LLMResponseValidator:
    async def validate_response(response: str, expected_format: str) -> ValidationResult
    async def sanitize_content(content: Dict[str, Any]) -> Dict[str, Any]
    async def handle_validation_failure(response: str, error: ValidationError) -> str

class ValidationResult:
    is_valid: bool
    sanitized_content: Optional[Dict[str, Any]]
    errors: List[ValidationError]
    
class ValidationError(Exception):
    error_type: str
    message: str
    recoverable: bool
```

**Implementation Requirements:**
- JSON schema validation for structured responses
- Content sanitization (remove malicious scripts, validate data types)
- Size limit enforcement (prevent resource exhaustion)
- Error recovery with fallback strategies
- Integration with existing structured logging

#### 1.2 Update AutoGen Service Integration
**File**: `backend/app/services/autogen_service.py` (modify)

**Changes Required:**
```python
# Add to __init__:
self.response_validator = LLMResponseValidator()

# Enhance run_single_agent_conversation method:
async def run_single_agent_conversation(self, agent, message, task) -> str:
    # Existing conversation logic...
    raw_response = await agent.on_messages([user_message], cancellation_token=None)
    
    # NEW: Validate and sanitize response
    validation_result = await self.response_validator.validate_response(
        raw_response, expected_format="json"
    )
    
    if validation_result.is_valid:
        return validation_result.sanitized_content
    else:
        # Handle validation failure with recovery
        return await self.response_validator.handle_validation_failure(
            raw_response, validation_result.errors[0]
        )
```

### Phase 2: Exponential Backoff Retry System (3-4 hours)

#### 2.1 Create Retry Handler
**File**: `backend/app/services/llm_retry.py` (new)

```python
# Key Classes to Implement:
class LLMRetryHandler:
    async def execute_with_retry(llm_call: Callable, max_retries: int = 3) -> Any
    def calculate_backoff_delay(attempt: int) -> float  # 2^(attempt-1) seconds
    async def should_retry(exception: Exception) -> bool
    
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 8.0
    retryable_exceptions: List[Type[Exception]]
```

**Retry Logic:**
- **Intervals**: 1s, 2s, 4s (exponential backoff)
- **Max Retries**: 3 attempts before escalation
- **Retryable Conditions**: TimeoutError, RateLimitError, TemporaryFailure
- **Non-Retryable**: AuthenticationError, InvalidAPIKey, PermanentFailure

#### 2.2 Integrate with Model Client Creation
**File**: `backend/app/services/autogen_service.py` (modify)

```python
# Add to __init__:
self.retry_handler = LLMRetryHandler()

# Enhance _create_model_client method:
def _create_model_client(self, model: str, temperature: float = 0.7) -> OpenAIChatCompletionClient:
    api_key = os.getenv("OPENAI_API_KEY", "demo-key")
    
    # Create client with retry wrapper
    base_client = OpenAIChatCompletionClient(
        model=model,
        api_key=api_key,
        temperature=temperature
    )
    
    # NEW: Wrap with retry handler
    return self._wrap_client_with_retry(base_client)

def _wrap_client_with_retry(self, client):
    # Wrap client methods with retry logic
    # All API calls will use exponential backoff automatically
```

### Phase 3: Usage Tracking & Cost Monitoring (4-5 hours)

#### 3.1 Create Usage Tracking System
**File**: `backend/app/services/llm_monitoring.py` (new)

```python
# Key Classes to Implement:
class LLMUsageTracker:
    async def track_request(agent_type: str, tokens_used: int, response_time: float, cost: float)
    async def calculate_costs(usage_data: UsageData) -> CostBreakdown
    async def generate_usage_report(project_id: UUID, date_range: DateRange) -> UsageReport
    
class UsageMetrics:
    timestamp: datetime
    agent_type: str
    project_id: UUID
    tokens_used: int
    response_time_ms: float
    estimated_cost: float
    provider: str = "openai"
    model: str
    success: bool
    
class CostBreakdown:
    total_cost: float
    cost_by_agent: Dict[str, float]
    token_usage: Dict[str, int]
    request_count: int
```

**OpenAI Pricing Integration:**
```python
# OpenAI GPT-4 pricing (as of 2024)
OPENAI_PRICING = {
    "gpt-4": {"input": 0.03 / 1000, "output": 0.06 / 1000},  # per token
    "gpt-4o-mini": {"input": 0.00015 / 1000, "output": 0.0006 / 1000}
}
```

#### 3.2 Add Structured Logging Integration
**File**: `backend/app/services/autogen_service.py` (modify)

```python
# Add to __init__:
self.usage_tracker = LLMUsageTracker()

# Add to run_single_agent_conversation:
async def run_single_agent_conversation(self, agent, message, task) -> str:
    start_time = time.time()
    
    try:
        # Existing conversation logic with retry...
        response = await self.retry_handler.execute_with_retry(
            lambda: agent.on_messages([user_message], cancellation_token=None)
        )
        
        # NEW: Track successful request
        response_time = (time.time() - start_time) * 1000  # ms
        await self.usage_tracker.track_request(
            agent_type=task.agent_type,
            tokens_used=self._estimate_tokens(message, response),
            response_time=response_time,
            cost=self._calculate_cost(message, response),
            success=True
        )
        
        # Structured logging
        logger.info("LLM request completed",
                   agent_type=task.agent_type,
                   project_id=str(task.project_id),
                   tokens_used=tokens_used,
                   response_time_ms=response_time,
                   estimated_cost=cost,
                   success=True)
        
        return response
        
    except Exception as e:
        # NEW: Track failed request
        await self.usage_tracker.track_request(
            agent_type=task.agent_type,
            tokens_used=0,
            response_time=(time.time() - start_time) * 1000,
            cost=0.0,
            success=False
        )
        
        logger.error("LLM request failed",
                    agent_type=task.agent_type,
                    project_id=str(task.project_id),
                    error=str(e),
                    response_time_ms=(time.time() - start_time) * 1000)
        
        raise
```

### Phase 4: Health Check Integration (1-2 hours)

#### 4.1 Add LLM Health Monitoring
**File**: `backend/app/api/health.py` (modify)

```python
# Add LLM provider health check
async def check_llm_providers():
    """Check OpenAI API connectivity and performance."""
    try:
        # Simple API test call
        test_client = OpenAIChatCompletionClient(
            model="gpt-4o-mini",
            api_key=settings.openai_api_key
        )
        
        start_time = time.time()
        # Make minimal test request
        test_response = await test_client.simple_test_call()
        response_time = (time.time() - start_time) * 1000
        
        return {
            "openai": {
                "status": "healthy",
                "response_time_ms": response_time,
                "model": "gpt-4o-mini"
            }
        }
    except Exception as e:
        return {
            "openai": {
                "status": "unhealthy", 
                "error": str(e)
            }
        }

# Update health endpoint to include LLM status
@router.get("/healthz")
async def health_check():
    # Existing health checks...
    llm_status = await check_llm_providers()
    
    return {
        "status": "healthy",
        "components": {
            "database": db_status,
            "redis": redis_status,
            "celery": celery_status,
            "llm_providers": llm_status  # NEW
        }
    }
```

## Testing Strategy

### Unit Tests
**File**: `backend/tests/unit/test_llm_reliability.py` (new)

```python
# Test Coverage Areas:
- Response validation with various input types
- Sanitization of malicious content
- Retry logic with different exception types
- Usage tracking accuracy
- Cost calculation correctness
- Health check functionality

# Key Test Cases:
def test_response_validation_valid_json()
def test_response_validation_invalid_json()
def test_content_sanitization()
def test_retry_exponential_backoff()
def test_retry_max_attempts()
def test_usage_tracking_metrics()
def test_cost_calculation()
```

### Integration Tests
**File**: `backend/tests/integration/test_autogen_reliability.py` (new)

```python
# Integration Test Areas:
- AutoGen service with reliability features
- End-to-end agent conversation with monitoring
- Error scenarios and recovery
- Performance under load

# Key Test Cases:
def test_autogen_with_validation()
def test_autogen_with_retry_logic()
def test_autogen_with_usage_tracking()
def test_error_recovery_workflow()
```

## Configuration Requirements

### Environment Variables
```bash
# Existing
OPENAI_API_KEY=your_openai_key

# New Configuration Options
LLM_RETRY_MAX_ATTEMPTS=3
LLM_RETRY_BASE_DELAY=1.0
LLM_RESPONSE_TIMEOUT=30
LLM_MAX_RESPONSE_SIZE=50000
LLM_ENABLE_USAGE_TRACKING=true
```

### Config.py Updates
**File**: `backend/app/config.py` (modify)

```python
# Add LLM reliability settings
class Settings(BaseSettings):
    # Existing settings...
    
    # LLM Reliability Configuration
    llm_retry_max_attempts: int = Field(default=3, env="LLM_RETRY_MAX_ATTEMPTS")
    llm_retry_base_delay: float = Field(default=1.0, env="LLM_RETRY_BASE_DELAY")
    llm_response_timeout: int = Field(default=30, env="LLM_RESPONSE_TIMEOUT")
    llm_max_response_size: int = Field(default=50000, env="LLM_MAX_RESPONSE_SIZE")
    llm_enable_usage_tracking: bool = Field(default=True, env="LLM_ENABLE_USAGE_TRACKING")
```

## Success Criteria

### Functional Requirements
✅ **Response Validation**: All LLM responses validated before Context Store persistence
✅ **Retry Logic**: Exponential backoff (1s, 2s, 4s) implemented for API failures  
✅ **Usage Tracking**: Comprehensive monitoring with structured logging
✅ **Cost Monitoring**: Real-time cost calculation and reporting
✅ **Health Monitoring**: LLM provider status in health endpoint

### Performance Requirements
✅ **Minimal Latency Impact**: < 50ms overhead for reliability features
✅ **Error Recovery**: 95%+ success rate after retry logic
✅ **Monitoring Accuracy**: 100% request tracking for usage and costs
✅ **Resource Usage**: < 5% additional memory/CPU overhead

### Integration Requirements
✅ **Backward Compatibility**: No breaking changes to existing AutoGen API
✅ **Transparent Enhancement**: Existing agent conversations enhanced seamlessly  
✅ **Graceful Degradation**: System remains functional during LLM service issues
✅ **Complete Monitoring**: All LLM interactions logged and tracked

## Implementation Timeline

**Day 1 (6-8 hours):**
- Phase 1: Response Validation & Sanitization (4-5 hours)
- Phase 2: Exponential Backoff Retry System (3-4 hours)

**Day 2 (6-7 hours):**
- Phase 3: Usage Tracking & Cost Monitoring (4-5 hours)
- Phase 4: Health Check Integration (1-2 hours)
- Testing & Validation (1-2 hours)

**Total Estimated Time**: 12-15 hours over 2 days

This implementation plan provides a **production-ready reliability layer** for the existing OpenAI integration while maintaining full backward compatibility and adding comprehensive monitoring capabilities.