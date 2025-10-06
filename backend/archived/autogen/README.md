# AutoGen Archived Code

**Archive Date:** October 4, 2025
**Reason:** Migrated to Microsoft Agent Framework (MAF)
**Status:** Preserved for reference, not used in production

## What Was Archived

This directory contains:
1. **AutoGen-based code** - Replaced with ADK (Phase 4)
2. **MAF migration attempt** - Abandoned due to dependency issues

### Archived Files

**AutoGen Framework (Replaced by ADK):**

**Services (app/services/):**
- `autogen_service.py` - Main AutoGen service wrapper
- `autogen/` - AutoGen framework integration directory
  - `__init__.py`
  - `agent_factory.py` - AutoGen agent creation
  - `autogen_core.py` - Core AutoGen functionality
  - `conversation_manager.py` - Multi-agent conversation management
  - `group_chat_manager.py` - Group chat orchestration
- `llm_providers/autogen_model_client_adapter.py` - LLM provider adapter

**Interfaces (app/interfaces/):**
- `autogen_interface.py` - AutoGen interface definitions

**Tests (tests/):**
- `test_autogen_conversation.py` - AutoGen conversation tests
- `test_autogen_simple.py` - Simple AutoGen tests

**MAF Migration Attempt (Abandoned):**

**Agents (app/agents/):**
- `maf_agent_wrapper.py` - BMADMAFWrapper (never tested, removed due to MAF dependency issues)

**CopilotKit Runtime (app/copilot/):**
- `maf_agui_runtime.py` - Hybrid MAF+ADK runtime (superseded by pure ADK approach)

## Replacement

All AutoGen functionality has been replaced by:

1. **Google ADK (Agent Development Kit)** - Production agent framework
   - `app/copilot/adk_runtime.py` - ADK runtime for CopilotKit integration
   - ADK LlmAgent for agent execution
   - Native AG-UI protocol support (CopilotKit compatible)
   - LiteLlm for provider-agnostic LLM access (OpenAI, Anthropic, Google)

2. **BMAD Enterprise Controls** - Fully Preserved
   - HITL pre-execution approval (agent_tasks.py)
   - Budget tracking and limits
   - Audit trails and safety controls
   - Real-time WebSocket monitoring

## Why Not MAF?

Microsoft Agent Framework (MAF) was initially planned as AutoGen's successor, but was abandoned due to:
- **Dependency Hell**: Complex Azure dependencies causing `resolution-too-deep` pip errors
- **Beta Status**: Still in beta (1.0.0b251001), not production-ready
- **ADK Superiority**: Google ADK has proven stability, simpler dependencies, native AG-UI support

## Migration Details

See documentation:
- `docs/CHANGELOG.md` - Version 2.21.0 (MAF Migration)
- `docs/AUTOGEN_DEPENDENCY_ANALYSIS.md` - Dependency analysis
- `docs/ONEPLAN.md` - Phase 4 & 5 completion

## Files Using AutoGen (Before Migration)

**Production Files (migrated to MAF):**
1. `app/tasks/agent_tasks.py` - ✅ Now uses BMADMAFWrapper
2. `app/services/orchestrator/orchestrator_core.py` - ✅ Removed AutoGen DI
3. `app/services/orchestrator/handoff_manager.py` - ✅ Uses MAF wrapper
4. `app/services/workflow_step_processor.py` - ✅ Uses MAF wrapper
5. `app/services/conflict_resolver.py` - ✅ Removed AutoGen dependency

## Why MAF?

1. **Official Microsoft Framework** - AutoGen's successor
2. **Production-Ready** - Built for enterprise use
3. **Better Architecture** - Cleaner abstraction layers
4. **Active Development** - Ongoing Microsoft support
5. **Standards Compliance** - MCP, A2A, OpenAPI support

## Restoration (If Needed)

To restore AutoGen functionality (not recommended):

```bash
# Copy files back from archive
cp -r archived/autogen/services/* app/services/
cp archived/autogen/interfaces/* app/interfaces/
cp archived/autogen/tests/* tests/

# Revert agent_tasks.py and other files to use AutoGenService
git checkout <commit-before-maf-migration> -- app/tasks/agent_tasks.py
# ... etc for other files

# Reinstall AutoGen packages
pip install autogen-agentchat autogen-core autogen-ext
```

## Archive Retention

- **Retention Period:** 6 months (until April 2026)
- **Review Date:** March 2026
- **Action After Retention:** Delete if MAF migration is stable

---

**Note:** This code is preserved for reference only. All production systems use MAF.
