#!/usr/bin/env node

/**
 * TypeScript Type Checking Hook (PostToolUse)
 *
 * Runs after Write/Edit operations on .ts/.tsx files
 * Executes `npx tsc --noEmit` to check for type errors
 *
 * Behavior:
 * - Success: Silent (suppressOutput: true)
 * - Errors: Provides detailed type errors to Claude via additionalContext
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Read JSON from stdin
let inputData = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => inputData += chunk);
process.stdin.on('end', async () => {
  try {
    const input = JSON.parse(inputData);

    // Get file path from input
    const filePath = input.parameters?.file_path;

    // Only process TypeScript files
    if (!filePath || (!filePath.endsWith('.ts') && !filePath.endsWith('.tsx'))) {
      console.log(JSON.stringify({
        continue: true,
        suppressOutput: true
      }));
      return;
    }

    // Only process files in frontend directory
    if (!filePath.includes('/frontend/')) {
      console.log(JSON.stringify({
        continue: true,
        suppressOutput: true
      }));
      return;
    }

    // Find project root (where frontend/tsconfig.json is)
    const projectRoot = process.env.CLAUDE_PROJECT_DIR || process.cwd();
    const frontendDir = path.join(projectRoot, 'frontend');
    const tsconfigPath = path.join(frontendDir, 'tsconfig.json');

    // Verify tsconfig.json exists
    if (!fs.existsSync(tsconfigPath)) {
      console.log(JSON.stringify({
        continue: true,
        suppressOutput: true
      }));
      return;
    }

    // Run TypeScript compiler
    const tsc = spawn('npx', ['tsc', '--noEmit', '--pretty', 'false'], {
      cwd: frontendDir,
      env: { ...process.env, FORCE_COLOR: '0' }
    });

    let stdout = '';
    let stderr = '';

    tsc.stdout.on('data', data => stdout += data.toString());
    tsc.stderr.on('data', data => stderr += data.toString());

    tsc.on('close', code => {
      if (code === 0) {
        // No type errors - silent success
        console.log(JSON.stringify({
          continue: true,
          suppressOutput: true
        }));
      } else {
        // Type errors found
        const output = stdout + stderr;
        const errorLines = output.trim().split('\n');

        // Parse error count
        const errorCountMatch = output.match(/Found (\d+) errors?/);
        const errorCount = errorCountMatch ? errorCountMatch[1] : 'some';

        // Filter for errors in the edited file
        const fileErrors = errorLines.filter(line =>
          line.includes(path.basename(filePath))
        );

        const relevantErrors = fileErrors.length > 0 ? fileErrors : errorLines;

        console.log(JSON.stringify({
          continue: true,
          additionalContext: `TypeScript found ${errorCount} type error(s):\n\n${relevantErrors.slice(0, 20).join('\n')}\n\nPlease fix these type errors.`
        }));
      }
    });

  } catch (error) {
    // Hook error - don't block, but report
    console.log(JSON.stringify({
      continue: true,
      additionalContext: `TypeScript check hook error: ${error.message}`
    }));
  }
});
