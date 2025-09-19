#!/usr/bin/env node

/**
 * BotArmy Frontend Kill Script
 * Stops frontend processes and calls backend kill script
 */

const { exec } = require('child_process');
const path = require('path');

console.log('🔪 Killing BotArmy processes...\n');

// Kill Next.js dev server (port 3000)
console.log('  - Killing Next.js processes on port 3000...');
exec('lsof -ti:3000 | xargs kill -9', (error) => {
  if (error) {
    console.log('    No processes found on port 3000');
  } else {
    console.log('    ✅ Next.js processes killed');
  }
});

// Kill any remaining Next.js processes
exec('pkill -f "next-server"', (error) => {
  if (error) {
    console.log('    No next-server processes found');
  } else {
    console.log('    ✅ Next.js server processes killed');
  }
});

// Call backend kill script
const backendKillScript = path.join(__dirname, '../backend/scripts/kill_processes.sh');
console.log('\n  - Calling backend kill script...');

exec(`bash "${backendKillScript}"`, (error, stdout, stderr) => {
  if (error) {
    console.log(`    ⚠️  Backend kill script error: ${error.message}`);
  } else {
    console.log('    ✅ Backend processes cleaned up');
  }

  if (stdout) {
    console.log(stdout);
  }

  if (stderr) {
    console.log(`    Warnings: ${stderr}`);
  }

  console.log('\n🎯 Frontend and backend cleanup complete!');
  console.log('   You can now run: npm run dev');
});