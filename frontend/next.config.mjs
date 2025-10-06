/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  outputFileTracingRoot: '/Users/neill/Documents/AI Code/Projects/bmad/frontend',
  outputFileTracingExcludes: {
    '*': [
      'venv/**/*',
      'backend/__pycache__/**/*',
      'backend/agents/__pycache__/**/*',
      'backend/services/__pycache__/**/*',
      'backend/agui/**/*',
      '**/*.pyc',
      'test_*.py',
      'conftest.py',
      'docker-compose.yml',
      'Dockerfile',
      '*.md',
      'debug_*.sh',
      'verify*.sh'
    ],
  },
}

export default nextConfig
