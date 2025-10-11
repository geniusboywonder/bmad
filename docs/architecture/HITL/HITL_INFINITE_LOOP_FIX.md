# HITL Infinite Loop & Toast Alert Fixes

**Date:** October 9, 2025
**Status:** ✅ COMPLETE

---

## Issues Fixed

### 1. ✅ Infinite HITL Request Creation

**Problem:**
- Markdown renderer for `<hitl-approval>` tags re-rendered on every React update
- Each re-render called `addRequest()` creating hundreds of duplicate HITL requests
- Console flooded with "Loading approval request..." messages
- HITL store overwhelmed with duplicate entries

**Root Cause:**
```typescript
// OLD CODE - BROKEN
markdownTagRenderers={{
  "hitl-approval": ({ requestId, children }) => {
    const request = requests.find(...);

    if (!request) {
      addRequest({...});  // ❌ Called on EVERY re-render!
      return null;  // ❌ Returning null causes re-render loop
    }

    return <InlineHITLApproval />;
  }
}}
```

**The Problem:**
1. Renderer returns `null` when request not found
2. React re-renders the markdown
3. Renderer called again, creates another request
4. Loop continues infinitely

**Solution:**
```typescript
// NEW CODE - FIXED
const createdApprovalIds = useRef<Set<string>>(new Set());

useEffect(() => {
  // Clear tracking on agent change
  createdApprovalIds.current.clear();
}, [selectedAgent]);

markdownTagRenderers={{
  "hitl-approval": ({ requestId, children }) => {
    const actualRequestId = requestId || `hitl-${selectedAgent}-${Date.now()}`;

    // ✅ Check if already created BEFORE calling addRequest
    if (!createdApprovalIds.current.has(actualRequestId)) {
      // ✅ Mark as created IMMEDIATELY to prevent re-entry
      createdApprovalIds.current.add(actualRequestId);

      // Create request ONCE
      addRequest({...});
    }

    const request = requests.find(...);

    // ✅ ALWAYS return a component, never null
    if (!request) {
      return <div>Loading approval request...</div>;
    }

    return <InlineHITLApproval request={request} />;
  }
}}
```

**Key Changes:**
1. **useRef tracking** - Tracks created approval IDs across renders
2. **Check before create** - Only create if not already tracked
3. **Mark immediately** - Add to Set BEFORE calling addRequest
4. **Always return component** - Never return null to prevent re-render loops
5. **Clear on agent change** - Reset tracking when switching agents

**Files Modified:**
- `frontend/app/copilot-demo/page.tsx` (lines 48-54, 257-297)

---

### 2. ✅ Toast Alerts Not Showing

**Problem:**
- Policy violation `toast.error()` calls had no visible effect
- No Toaster component rendered on copilot-demo page
- Sonner toast system not initialized

**Root Cause:**
```typescript
// copilot-demo/page.tsx
import { toast } from "sonner";  // ✅ Import present

toast.error("Action Blocked", {...});  // ✅ Call present

// ❌ BUT NO <Toaster /> component rendered!
return <div>...</div>;  // No toast container
```

**Solution:**
```typescript
// Add Toaster import
import { Toaster } from "@/components/ui/sonner";

// Render Toaster at top level
return (
  <>
    <Toaster />  {/* ✅ Toast container added */}
    <div className="min-h-screen flex flex-col">
      {/* ...rest of page */}
    </div>
  </>
);
```

**Why This Happened:**
- `copilot-demo/page.tsx` doesn't use the root layout's ClientProvider
- ClientProvider has a Toaster, but it's not in the copilot-demo render tree
- Sonner requires explicit `<Toaster />` component to render toasts

**Files Modified:**
- `frontend/app/copilot-demo/page.tsx` (lines 19, 148-149, 308)

---

### 3. ✅ "Force-closing unterminated streaming message" Warning

**Problem:**
```
Force-closing unterminated streaming message: afbaa480-ee9f-41cd-ace3-9cbb9bfe7bd4
```

**Analysis:**
- This is a **benign CopilotKit warning**, not an error
- Occurs when agent returns synchronous response instead of streaming
- Policy violation returns immediate `Message` object without streaming
- CopilotKit expects all responses to be streams

**Why It's Safe:**
1. Agent properly returns `Message` object with complete content
2. Frontend receives and displays the message correctly
3. No data loss or functionality impact
4. Just CopilotKit logging its internal stream cleanup

**Code:**
```python
# backend/app/copilot/hitl_aware_agent.py
if policy_decision.status == "denied":
    # Return policy violation message
    return Message(  # ✅ Valid synchronous return
        role="assistant",
        content=f"❌ **Policy Violation**\n\n{policy_decision.message}..."
    )
```

**Status:** No fix needed - expected behavior for synchronous responses

---

## Testing Checklist

- [x] No infinite HITL request creation
- [x] Only one approval request created per tag
- [x] Toast notifications visible for policy violations
- [x] HITL approval UI renders correctly
- [x] Agent switching clears approval tracking
- [x] Loading state shows while request being created
- [x] InlineHITLApproval component displays when request ready

---

## Files Modified

### Frontend
1. `frontend/app/copilot-demo/page.tsx`
   - Added `useRef` import (line 12)
   - Added `createdApprovalIds` tracking (lines 48-54)
   - Fixed markdown renderer to prevent infinite loop (lines 257-297)
   - Added `Toaster` import (line 19)
   - Rendered `Toaster` component (lines 148-149, 308)

---

## Related Documentation

- `docs/architecture/HITL/hitl-messaging-fix.md` - HITL markdown tag protocol
- `docs/architecture/HITL-UI-FIXES-SUMMARY.md` - Previous HITL UI fixes
- `docs/CHANGELOG.md` (lines 40-46) - Copilot Sidebar HITL Flow

---

## Future Improvements

1. **Persistent Request IDs** - Use backend-generated UUIDs instead of timestamp-based IDs
2. **Request Deduplication** - Backend should check for existing requests before creating
3. **Stream Completion** - Implement proper streaming for policy violations to avoid warning
4. **Loading State Enhancement** - Add skeleton loader instead of plain text
5. **Error Boundaries** - Wrap markdown renderers in error boundaries for better resilience

---

**Status:** ✅ All issues resolved and tested
