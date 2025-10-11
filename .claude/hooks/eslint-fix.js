#!/usr/bin/env node

/**
 * ESLint Auto-Fix Hook (PostToolUse)
 *
 * Runs after Write/Edit operations to lint and auto-fix files
 * Executes `npx eslint --fix` on supported file types
 *
 * Behavior:
 * - Auto-fixable issues: Fixed silently (suppressOutput: true)
 * - Non-fixable issues: Reports errors to Claude via additionalContext
 */

const { spawn } = require('child_process');
const path = require('path');

// Supported file extensions for ESLint
const SUPPORTED_EXTENSIONS = [
  '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs'
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

    // Run ESLint with --fix
    const eslint = spawn('npx', ['eslint', '--fix', '--format', 'json', filePath], {
      cwd: frontendDir,
      env: { ...process.env }
    });

    let stdout = '';
    let stderr = '';

    eslint.stdout.on('data', data => stdout += data.toString());
    eslint.stderr.on('data', data => stderr += data.toString());

    eslint.on('close', code => {
      try {
        // Parse JSON output
        const results = JSON.parse(stdout || '[]');

        if (results.length === 0 || !results[0]) {
          // No results or empty results - success
          console.log(JSON.stringify({
            continue: true,
            suppressOutput: true
          }));
          return;
        }

        const fileResult = results[0];
        const { errorCount, warningCount, messages } = fileResult;

        // If all issues were auto-fixed (errorCount and warningCount are 0)
        if (errorCount === 0 && warningCount === 0) {
          console.log(JSON.stringify({
            continue: true,
            suppressOutput: true
          }));
          return;
        }

        // There are unfixable errors or warnings
        const unfixableIssues = messages.filter(msg => !msg.fix);

        if (unfixableIssues.length === 0) {
          // All issues were auto-fixed
          console.log(JSON.stringify({
            continue: true,
            suppressOutput: true
          }));
          return;
        }

        // Format error messages
        const errorMessages = unfixableIssues.map(msg => {
          const severity = msg.severity === 2 ? 'error' : 'warning';
          return `  Line ${msg.line}:${msg.column} - ${msg.message} (${msg.ruleId})`;
        }).join('\n');

        console.log(JSON.stringify({
          continue: true,
          additionalContext: `ESLint found ${errorCount} error(s) and ${warningCount} warning(s) that cannot be auto-fixed:\n\n${errorMessages}\n\nPlease fix these issues manually.`
        }));

      } catch (parseError) {
        // If JSON parsing fails, check stderr
        if (stderr) {
          console.log(JSON.stringify({
            continue: true,
            additionalContext: `ESLint error:\n${stderr}`
          }));
        } else {
          // Silent success if no stderr
          console.log(JSON.stringify({
            continue: true,
            suppressOutput: true
          }));
        }
      }
    });

  } catch (error) {
    // Hook error - don't block, but report
    console.log(JSON.stringify({
      continue: true,
      additionalContext: `ESLint hook error: ${error.message}`
    }));
  }
});
