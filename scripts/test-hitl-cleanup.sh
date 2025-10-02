#!/bin/bash
# Test HITL Alert Bar - Clear localStorage and verify clean state

echo "Opening Chrome DevTools Console to test HITL alerts..."
echo ""
echo "Run these commands in the browser console:"
echo ""
echo "// Clear all HITL requests from localStorage"
echo "localStorage.removeItem('hitl-store')"
echo ""
echo "// Verify cleanup"
echo "console.log('HITL Store:', JSON.parse(localStorage.getItem('hitl-store') || '{}'))"
echo ""
echo "// Force refresh"
echo "window.location.reload()"
