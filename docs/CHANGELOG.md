# Changelog

All notable changes to this project will be captured here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and semantic versioning when applicable.

## [Unreleased]

### Added
- Restored the `reconfigureHITL` CopilotKit action in `frontend/app/copilot-demo/page.tsx`, providing a native tool flow with toast navigation and inline prompt focus.

### Changed
- Upgraded CopilotKit packages to `@copilotkit/react-core@1.10.6`, `@copilotkit/react-ui@1.10.6`, `@copilotkit/runtime@1.10.6`.
- Upgraded backend agent dependencies to `google-adk==1.16.0` and `litellm==1.77.7`.
- Updated `HITLReconfigurePrompt` so the selected decision locks the UI and prevents further edits.
- Adjusted toast copy (“{agent} requires your attention for a human-in-the-loop action.”) and added a “Review” action that scrolls to the current prompt.
- Refreshed architecture documentation to describe the tool-based HITL flow and current code structure.
- Replaced the deprecated `useCopilotAction` hook with `useHumanInTheLoop` for the HITL prompt so future CopilotKit releases remain compatible.

### Fixed
- Resolved race conditions that allowed multiple HITL submissions by ensuring the prompt disables after an action and the Copilot tool call only resolves once.
- Prevented lingering markdown-specific logic by removing the `<hitl-approval>` renderer and corresponding duplicate toast heuristics.
- Applied phase policy enforcement to CopilotKit sessions by intercepting violations inside `HITLAwareLlmAgent`, returning a violation message, and broadcasting the event to the UI.

## [2.24.0] - 2025-10-04

### Added
- Phase policy enforcement with `PhasePolicyService` and frontend gating.

### Changed
- Initial migration to a CopilotKit-native HITL flow (predecessor to the current tool-based implementation).

### Fixed
- Consolidated HITL safety services and counter handling.

## [2.23.0] - 2025-10-04

- Switched agent execution to Google ADK (AutoGen remains archived).  
- Added ADK executor, workflow integration, and Celery task wiring.
