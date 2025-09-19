import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

const ENV_FILE_PATH = path.join(process.cwd(), '.env')

// Environment variables we want to expose for editing
const EDITABLE_VARS = [
  'AGENT_TEST_MODE',
  'ROLE_TEST_MODE', 
  'TEST_MODE',
  'ENABLE_HITL',
  'AUTO_ACTION',
  'HITL_TIMEOUT',
  'HITL_APPROVAL_THRESHOLD',
  'HITL_NOTIFICATION_EMAIL',
  'HITL_QUEUE_SIZE',
  'HITL_RETRY_ATTEMPTS',
  'HITL_AUTO_ESCALATION'
]

interface EnvVariable {
  key: string
  value: string | boolean
  description: string
  type: 'string' | 'boolean'
}

const getVariableDescription = (key: string): string => {
  const descriptions: Record<string, string> = {
    'AGENT_TEST_MODE': 'Enable agent test mode to return static confirmations',
    'ROLE_TEST_MODE': 'Enable role test mode for LLM role confirmation', 
    'TEST_MODE': 'Enable overall test mode for mock LLM responses',
    'ENABLE_HITL': 'Enable Human-in-the-Loop functionality',
    'AUTO_ACTION': 'Default auto action (approve/reject/none)',
    'HITL_TIMEOUT': 'Timeout in seconds for HITL decisions',
    'HITL_APPROVAL_THRESHOLD': 'Confidence threshold for automatic approval (0.0-1.0)',
    'HITL_NOTIFICATION_EMAIL': 'Email address for HITL notifications',
    'HITL_QUEUE_SIZE': 'Maximum size of HITL decision queue',
    'HITL_RETRY_ATTEMPTS': 'Number of retry attempts for failed HITL operations',
    'HITL_AUTO_ESCALATION': 'Enable automatic escalation of timed-out HITL requests'
  }
  return descriptions[key] || 'Configuration setting'
}

const parseEnvFile = (): Record<string, string> => {
  try {
    if (!fs.existsSync(ENV_FILE_PATH)) {
      return {}
    }
    
    const content = fs.readFileSync(ENV_FILE_PATH, 'utf8')
    const env: Record<string, string> = {}
    
    content.split('\n').forEach(line => {
      const trimmed = line.trim()
      if (trimmed && !trimmed.startsWith('#') && trimmed.includes('=')) {
        const [key, ...valueParts] = trimmed.split('=')
        const value = valueParts.join('=').trim()
        env[key.trim()] = value
      }
    })
    
    return env
  } catch (error) {
    console.error('Error reading .env file:', error)
    return {}
  }
}

const updateEnvFile = (updates: Record<string, string>): boolean => {
  try {
    if (!fs.existsSync(ENV_FILE_PATH)) {
      console.error('.env file not found')
      return false
    }
    
    let content = fs.readFileSync(ENV_FILE_PATH, 'utf8')
    
    // Update each variable
    Object.entries(updates).forEach(([key, value]) => {
      if (EDITABLE_VARS.includes(key)) {
        const regex = new RegExp(`^${key}=.*$`, 'm')
        const newLine = `${key}=${value}`
        
        if (regex.test(content)) {
          content = content.replace(regex, newLine)
        } else {
          // If variable doesn't exist, add it to the end
          content += `\n${newLine}`
        }
      }
    })
    
    fs.writeFileSync(ENV_FILE_PATH, content, 'utf8')
    return true
  } catch (error) {
    console.error('Error updating .env file:', error)
    return false
  }
}

const convertValue = (key: string, value: string): string | boolean => {
  if (['AGENT_TEST_MODE', 'ROLE_TEST_MODE', 'TEST_MODE', 'ENABLE_HITL', 'HITL_AUTO_ESCALATION'].includes(key)) {
    return value.toLowerCase() === 'true'
  }
  return value
}

const getVariableType = (key: string): 'string' | 'boolean' => {
  return ['AGENT_TEST_MODE', 'ROLE_TEST_MODE', 'TEST_MODE', 'ENABLE_HITL', 'HITL_AUTO_ESCALATION'].includes(key) ? 'boolean' : 'string'
}

export async function GET() {
  try {
    const envData = parseEnvFile()
    
    const variables: EnvVariable[] = EDITABLE_VARS.map(key => ({
      key,
      value: convertValue(key, envData[key] || ''),
      description: getVariableDescription(key),
      type: getVariableType(key)
    }))
    
    return NextResponse.json({ success: true, variables })
  } catch (error) {
    console.error('Error reading environment variables:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to read environment variables' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { variables } = body
    
    if (!variables || !Array.isArray(variables)) {
      return NextResponse.json(
        { success: false, error: 'Invalid request format' },
        { status: 400 }
      )
    }
    
    // Convert variables array to updates object
    const updates: Record<string, string> = {}
    variables.forEach((variable: EnvVariable) => {
      if (EDITABLE_VARS.includes(variable.key)) {
        updates[variable.key] = String(variable.value)
      }
    })
    
    const success = updateEnvFile(updates)
    
    if (success) {
      return NextResponse.json({ success: true, message: 'Environment variables updated successfully' })
    } else {
      return NextResponse.json(
        { success: false, error: 'Failed to update .env file' },
        { status: 500 }
      )
    }
  } catch (error) {
    console.error('Error updating environment variables:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to update environment variables' },
      { status: 500 }
    )
  }
}