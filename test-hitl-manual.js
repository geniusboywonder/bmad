/**
 * Manual HITL Testing Script
 * Tests all 5 required HITL features using curl and basic DOM parsing
 */

const { execSync } = require('child_process');

function testHITLFeatures() {
  console.log('🧪 Starting HITL Integration Tests...\n');

  // Test 1: Check if page loads with HITL controls
  console.log('1️⃣ Testing page load and HITL controls...');
  try {
    const pageContent = execSync('curl -s "http://localhost:3000/copilot-demo"', { encoding: 'utf8' });
    
    if (pageContent.includes('HITL Controls')) {
      console.log('✅ HITL Controls section found');
    } else {
      console.log('❌ HITL Controls section not found');
    }

    if (pageContent.includes('Trigger HITL Request')) {
      console.log('✅ Trigger HITL Request button found');
    } else {
      console.log('❌ Trigger HITL Request button not found');
    }

    if (pageContent.includes('data-testid="hitl-controls"')) {
      console.log('✅ HITL controls test ID found');
    } else {
      console.log('❌ HITL controls test ID not found');
    }
  } catch (error) {
    console.log('❌ Failed to load page:', error.message);
  }

  // Test 2: Check backend HITL API endpoints
  console.log('\n2️⃣ Testing backend HITL API endpoints...');
  
  const endpoints = [
    '/api/v1/hitl/pending',
    '/api/v1/hitl/health',
    '/api/v1/hitl/approvals'
  ];

  endpoints.forEach(endpoint => {
    try {
      const response = execSync(`curl -s -w "%{http_code}" "http://localhost:8000${endpoint}"`, { encoding: 'utf8' });
      const statusCode = response.slice(-3);
      
      if (statusCode === '200') {
        console.log(`✅ ${endpoint} - Status: ${statusCode}`);
      } else {
        console.log(`⚠️ ${endpoint} - Status: ${statusCode}`);
      }
    } catch (error) {
      console.log(`❌ ${endpoint} - Error: ${error.message}`);
    }
  });

  // Test 3: Check HITL store functionality
  console.log('\n3️⃣ Testing HITL store components...');
  
  const storeFiles = [
    'frontend/lib/stores/hitl-store.ts',
    'frontend/components/hitl/hitl-alerts-bar.tsx',
    'frontend/components/hitl/inline-hitl-approval.tsx'
  ];

  storeFiles.forEach(file => {
    try {
      const content = execSync(`cat "${file}"`, { encoding: 'utf8' });
      
      if (content.includes('addRequest') && content.includes('resolveRequest')) {
        console.log(`✅ ${file} - Core HITL methods found`);
      } else {
        console.log(`❌ ${file} - Missing core HITL methods`);
      }
    } catch (error) {
      console.log(`❌ ${file} - File not found or error: ${error.message}`);
    }
  });

  // Test 4: Check agent context integration
  console.log('\n4️⃣ Testing agent context integration...');
  
  try {
    const agentContext = execSync('cat "frontend/lib/context/agent-context.tsx"', { encoding: 'utf8' });
    
    if (agentContext.includes('selectedAgent') && agentContext.includes('setSelectedAgent')) {
      console.log('✅ Agent context with selectedAgent found');
    } else {
      console.log('❌ Agent context missing selectedAgent functionality');
    }
  } catch (error) {
    console.log('❌ Agent context file not found:', error.message);
  }

  // Test 5: Check WebSocket integration
  console.log('\n5️⃣ Testing WebSocket integration...');
  
  try {
    const wsService = execSync('cat "frontend/lib/services/websocket/websocket-service.ts"', { encoding: 'utf8' });
    
    if (wsService.includes('HITL') || wsService.includes('hitl')) {
      console.log('✅ WebSocket service includes HITL functionality');
    } else {
      console.log('⚠️ WebSocket service may not include HITL functionality');
    }
  } catch (error) {
    console.log('❌ WebSocket service file not found:', error.message);
  }

  console.log('\n🏁 HITL Integration Test Summary Complete');
  console.log('\n📋 Manual Testing Checklist:');
  console.log('□ 1. Navigate to http://localhost:3000/copilot-demo');
  console.log('□ 2. Click "Trigger HITL Request" button');
  console.log('□ 3. Verify HITL approval component appears with Approve/Reject/Modify buttons');
  console.log('□ 4. Verify HITL alert appears in alerts bar at top');
  console.log('□ 5. Click on HITL alert to navigate to chat message');
  console.log('□ 6. Click Approve button and verify request is processed');
  console.log('□ 7. Set counter to 1, force to zero, verify threshold behavior');
  console.log('□ 8. Toggle HITL on/off and verify state changes');
  console.log('□ 9. Test counter reset functionality');
  console.log('□ 10. Verify multiple HITL requests can be handled');
}

// Run the tests
testHITLFeatures();