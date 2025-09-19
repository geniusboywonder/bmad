import { 
  Bot, 
  User, 
  Search, 
  Building2, 
  Code, 
  TestTube, 
  Rocket, 
  Activity,
  UserCog,
  type LucideIcon 
} from 'lucide-react';

export interface AgentDefinition {
  name: string;
  description: string;
  role: string;
  icon: LucideIcon;
  color: string;
  capabilities: string[];
  status: 'idle' | 'busy' | 'error' | 'offline';
}

export const AGENT_DEFINITIONS: AgentDefinition[] = [
  {
    name: 'Analyst',
    description: 'Requirements analysis agent',
    role: 'analyst',
    icon: Search,
    color: 'text-slate-500',
    capabilities: ['requirements_gathering', 'stakeholder_analysis', 'business_analysis'],
    status: 'idle'
  },
  {
    name: 'Architect',
    description: 'System design agent',
    role: 'architect',
    icon: Building2,
    color: 'text-pink-500',
    capabilities: ['system_design', 'architecture_planning', 'technical_specifications'],
    status: 'idle'
  },
  {
    name: 'Developer',
    description: 'Code generation agent',
    role: 'developer',
    icon: Code,
    color: 'text-lime-600',
    capabilities: ['code_generation', 'implementation', 'debugging'],
    status: 'idle'
  },
  {
    name: 'Tester',
    description: 'Quality assurance agent',
    role: 'tester',
    icon: TestTube,
    color: 'text-sky-500',
    capabilities: ['quality_assurance', 'testing', 'validation'],
    status: 'idle'
  },
  {
    name: 'Deployer',
    description: 'Deployment management agent',
    role: 'deployer',
    icon: Rocket,
    color: 'text-rose-600',
    capabilities: ['deployment', 'infrastructure', 'monitoring'],
    status: 'idle'
  },
  {
    name: 'Project Manager',
    description: 'Project management agent',
    role: 'project_manager',
    icon: UserCog,
    color: 'text-muted-foreground',
    capabilities: ['project_planning', 'coordination', 'resource_management'],
    status: 'idle'
  }
];

// Helper function to get agent by name
export const getAgentByName = (name: string): AgentDefinition | undefined => {
  return AGENT_DEFINITIONS.find(agent => agent.name === name);
};

// Helper function to get agents by role
export const getAgentsByRole = (role: string): AgentDefinition[] => {
  return AGENT_DEFINITIONS.filter(agent => agent.role === role);
};
