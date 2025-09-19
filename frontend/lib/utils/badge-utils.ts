/**
 * Centralized Badge Color Management System
 * 
 * This utility provides consistent badge styling across the entire application.
 * All badge colors and styles should be managed through these functions.
 */

export type BadgeStatus = 'done' | 'wip' | 'waiting' | 'queued' | 'planned' | 'error' | 'blocked';
export type AgentType = 'analyst' | 'architect' | 'developer' | 'tester' | 'deployer' | 'pm' | 'hitl';

/**
 * Get status badge color classes for the muted variant
 * Returns color and border classes to be applied via className
 */
export const getStatusBadgeClasses = (status: BadgeStatus | string): string => {
  switch (status.toLowerCase()) {
    case 'done':
    case 'completed':
    case 'finished':
      return 'text-tester border-tester/20';
      
    case 'wip':
    case 'in-progress':
    case 'active':
      return 'text-analyst border-analyst/20';
      
    case 'waiting':
    case 'pending':
      return 'text-amber border-amber/20';
      
    case 'queued':
    case 'ready':
      return 'text-purple-600 border-purple-600/20';
      
    case 'planned':
    case 'scheduled':
      return 'text-slate-600 border-slate-600/20';
      
    case 'error':
    case 'failed':
    case 'blocked':
      return 'text-destructive border-destructive/20';
      
    default:
      return 'text-muted-foreground border-muted-foreground/20';
  }
};

/**
 * Get agent badge color classes for the muted variant
 * Returns background, text, and border classes for agent role indicators
 * NEW STAGE COLOR SYSTEM (2025) - Separated from status colors
 */
export const getAgentBadgeClasses = (agent: AgentType | string): string => {
  const agentLower = agent.toLowerCase();
  
  // NEW STAGE COLORS - No overlap with status colors
  if (agentLower.includes('analyst')) {
    return 'bg-slate-500/5 text-slate-500 border-slate-500/20';
  }
  
  if (agentLower.includes('architect')) {
    return 'bg-pink-500/5 text-pink-500 border-pink-500/20';
  }
  
  if (agentLower.includes('developer') || agentLower.includes('dev')) {
    return 'bg-lime-600/5 text-lime-600 border-lime-600/20';
  }
  
  if (agentLower.includes('tester') || agentLower.includes('test')) {
    return 'bg-sky-500/5 text-sky-500 border-sky-500/20';
  }
  
  if (agentLower.includes('deployer') || agentLower.includes('deploy')) {
    return 'bg-rose-600/5 text-rose-600 border-rose-600/20';
  }
  
  if (agentLower.includes('pm') || agentLower.includes('manager')) {
    return 'bg-lime-600/5 text-lime-600 border-lime-600/20'; // PM uses developer colors
  }
  
  if (agentLower.includes('hitl') || agentLower.includes('human')) {
    return 'bg-amber/5 text-amber border-amber/20'; // Keep amber for HITL alerts
  }
  
  return 'bg-muted/5 text-muted-foreground border-muted-foreground/20';
};

/**
 * Get severity badge classes for critical states
 * These use the destructive variant for high visibility
 */
export const getSeverityBadgeClasses = (severity: 'critical' | 'warning' | 'info' | string): string => {
  switch (severity.toLowerCase()) {
    case 'critical':
    case 'error':
      return 'bg-destructive text-destructive-foreground';
      
    case 'warning':
    case 'alert':
      return 'bg-amber text-amber-foreground';
      
    case 'info':
    case 'notice':
      return 'bg-analyst text-analyst-foreground';
      
    default:
      return 'bg-muted text-muted-foreground';
  }
};

/**
 * Badge component props for consistent usage
 */
export interface BadgeProps {
  status?: BadgeStatus | string;
  agent?: AgentType | string;
  severity?: 'critical' | 'warning' | 'info' | string;
  children: React.ReactNode;
  className?: string;
}

/**
 * Utility to combine badge classes
 */
export const combineBadgeClasses = (...classes: string[]): string => {
  return classes.filter(Boolean).join(' ');
};