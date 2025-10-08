# HITL Alert System - Comprehensive Fix Plan

## Issues Identified

### 1. HITL Alerts Not Appearing in Alert Bar
**Root Cause:** WebSocket events are being processed and requests added to store, but alerts bar not updating
**Evidence:** Console shows "HITL request added to store" but alert bar remains empty

### 2. No Action Buttons on HITL Chat Messages  
**Root Cause:** Chat component looking for hitlRequest but matching logic broken
**Evidence:** HITL messages render but without InlineHITLApproval component

### 3. Navigation Not Working
**Root Cause:** Alert bar click doesn't navigate to correct project workspace + specific chat message
**Evidence:** handleHITLClick has basic scroll logic but no project/route navigation

## Solution Plan

### Fix 1: Ensure Store Updates Trigger UI Re-renders
- Verify useHITLStore subscription in HITLAlertsBar
- Add console logs to track store updates
- Check if `isClient` check is blocking server-side rendering

### Fix 2: Fix HITL Message Matching Logic
- Update copilot-chat.tsx message matching to use correct approval ID
- Ensure InlineHITLApproval receives proper request data
- Add fallback UI if request not found in store

### Fix 3: Implement Project Navigation
- Add router navigation to project workspace
- Scroll to specific HITL message using data attributes
- Highlight targeted message temporarily

### Fix 4: Add HITL Approval Button Component
- Create inline approval UI with approve/reject buttons
- Connect to resolveRequest action from HITL store
- Show loading/success/error states

## Implementation Order

1. Add debugging to understand current data flow
2. Fix store subscription and re-render issues
3. Implement proper message matching
4. Add navigation logic
5. Create inline approval component if missing
