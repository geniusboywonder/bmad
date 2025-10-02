// Manual HITL Alert Test Script
// Run this in browser console at http://localhost:3000

// 1. Check current HITL store state
console.log('=== HITL Store State ===');
const hitlStore = JSON.parse(localStorage.getItem('hitl-store') || '{}');
console.log('Requests:', hitlStore.state?.requests || []);

// 2. Check for stale requests
if (hitlStore.state?.requests?.length > 0) {
  console.log('\n=== Checking for Stale Requests ===');
  hitlStore.state.requests.forEach(async (req) => {
    const approvalId = req.context?.approvalId;
    if (!approvalId) {
      console.warn(`Request ${req.id} has no approval ID`);
      return;
    }
    
    try {
      const response = await fetch(`http://localhost:8000/api/v1/hitl-safety/approvals/${approvalId}`);
      if (response.ok) {
        const data = await response.json();
        console.log(`✓ Approval ${approvalId}: ${data.status}`);
      } else {
        console.error(`✗ Approval ${approvalId}: ${response.status} ${response.statusText}`);
      }
    } catch (error) {
      console.error(`✗ Approval ${approvalId}: ${error.message}`);
    }
  });
}

// 3. Clean up stale requests
console.log('\n=== Cleanup Command ===');
console.log('Run: useHITLStore.getState().clearAllRequests()');
