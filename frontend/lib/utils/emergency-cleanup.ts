// Emergency storage cleanup utility
// This will be called if the app detects corrupted data

export function emergencyStorageCleanup() {
  console.log('🚨 EMERGENCY: Clearing corrupted storage data...');
  
  try {
    // Clear all known store keys
    const storeKeys = [
      'conversation-store',
      'agent-store', 
      'task-store',
      'artifact-store',
      'log-store'
    ];

    storeKeys.forEach(key => {
      try {
        localStorage.removeItem(key);
        console.log(`✅ Cleared: ${key}`);
      } catch (error) {
        console.error(`❌ Failed to clear ${key}:`, error);
      }
    });

    // Clear any other keys that might be related
    Object.keys(localStorage).forEach(key => {
      if (key.includes('conversation') || 
          key.includes('botarmy') || 
          key.includes('store') ||
          key.includes('zustand')) {
        try {
          localStorage.removeItem(key);
          console.log(`✅ Cleared additional key: ${key}`);
        } catch (error) {
          console.error(`❌ Failed to clear ${key}:`, error);
        }
      }
    });

    console.log('✅ Emergency cleanup completed');
    return true;
  } catch (error) {
    console.error('❌ Emergency cleanup failed:', error);
    return false;
  }
}

// Auto-run if this file is loaded directly in browser console
if (typeof window !== 'undefined' && window.localStorage) {
  // Only run if explicitly called
  (window as any).emergencyStorageCleanup = emergencyStorageCleanup;
  console.log('Emergency storage cleanup utility loaded. Call emergencyStorageCleanup() if needed.');
}
