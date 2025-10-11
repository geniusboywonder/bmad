#!/usr/bin/env node

/**
 * Prettier Auto-Formatting Hook (PostToolUse)
 *
 * Runs after Write/Edit operations to auto-format files
 * Executes `npx prettier --write` on supported file types
 *
 * Behavior:
 * - Success: Silent (suppressOutput: true)
 * - Errors: Reports formatting issues to Claude via additionalContext
 */

const { spawn } = require('child_process');
const path = require('path');

// Supported file extensions for Prettier
const SUPPORTED_EXTENSIONS = [
  '.js', '.jsx', '.ts', '.tsx',
  '.json', '.css', '.scss', '.html',
  '.md', '.yaml', '.yml'
];

// Read JSON from stdin
let inputData = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => inputData += chunk);
process.stdin.on('end', async () => {
  try {
    const input = JSON.parse(inputData);

    // Get file path from input
    const filePath = input.parameters?.file_path;

    if (!filePath) {
      console.log(JSON.stringify({
        continue: true,
        suppressOutput: true
      }));
      return;
    }

    // Check if file extension is supported
    const ext = path.extname(filePath);
    if (!SUPPORTED_EXTENSIONS.includes(ext)) {
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

    // Skip node_modules and build directories
    if (filePath.includes('node_modules') ||
        filePath.includes('.next') ||
        filePath.includes('dist') ||
        filePath.includes('build')) {
      console.log(JSON.stringify({
        continue: true,
        suppressOutput: true
      }));
      return;
    }

    // Find project root
    const projectRoot = process.env.CLAUDE_PROJECT_DIR || process.cwd();
    const frontendDir = path.join(projectRoot, 'frontend');

    // Run Prettier
    const prettier = spawn('npx', ['prettier', '--write', filePath], {
      cwd: frontendDir,
      env: { ...process.env }
    });

    let stdout = '';
    let stderr = '';

    prettier.stdout.on('data', data => stdout += data.toString());
    prettier.stderr.on('data', data => stderr += data.toString());

    prettier.on('close', code => {
      if (code === 0) {
        // Successfully formatted - silent success
        console.log(JSON.stringify({
          continue: true,
          suppressOutput: true
        }));
      } else {
        // Formatting failed
        const error = stderr || stdout || 'Unknown error';
        console.log(JSON.stringify({
          continue: true,
          additionalContext: `Prettier formatting failed:\n${error}\n\nPlease check the file syntax.`
        }));
      }
    });

  } catch (error) {
    // Hook error - don't block, but report
    console.log(JSON.stringify({
      continue: true,
      additionalContext: `Prettier hook error: ${error.message}`
    }));
  }
});
