"use client";

import React, { useState, useEffect } from 'react';
import { useHITLStore } from '@/lib/stores/hitl-store';
import { useAgentStore } from '@/lib/stores/agent-store';
import { useProjectStore } from '@/lib/stores/project-store';
import { useNavigationStore } from '@/lib/stores/navigation-store';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { AlertTriangle, ChevronDown, X, DollarSign, Zap, StopCircle, Shield } from 'lucide-react';
import { safetyEventHandler } from '@/lib/services/safety/safety-event-handler';

interface SystemAlert {
  id: string;
  message: string;
  stage?: string;
}

interface HITLAlertsBarProps {
  systemAlerts: SystemAlert[];
  expandedAlerts: string[];
  toggleExpanded: (id: string) => void;
  dismissAlert: (id: string) => void;
  isClient: boolean;
}

export const HITLAlertsBar: React.FC<HITLAlertsBarProps> = ({
  systemAlerts,
  expandedAlerts,
  toggleExpanded,
  dismissAlert,
  isClient
}) => {
  const { requests, navigateToRequest, resolveRequest, safetyAlerts } = useHITLStore();
  const { setAgentFilter } = useAgentStore();
  const { currentProject } = useProjectStore();
  const { navigateToProject, currentView } = useNavigationStore();

  // Debug: Log requests changes
  useEffect(() => {
    console.log('[HITLAlertsBar] Requests updated:', requests.length, 'pending:', requests.filter(r => r.status === 'pending').length);
  }, [requests]);
  const [budgetUsage, setBudgetUsage] = useState({ used: 0, limit: 100, percentage: 0 });
  const [showEmergencyStop, setShowEmergencyStop] = useState(false);

  const pendingHITLRequests = isClient ? requests.filter(r => r.status === 'pending') : [];

  // Debug: Log alert bar state
  useEffect(() => {
    console.log('[HITLAlertsBar] State:', {
      isClient,
      totalRequests: requests.length,
      pendingRequests: pendingHITLRequests.length,
      systemAlerts: systemAlerts.length,
      hasAlerts: pendingHITLRequests.length > 0 || systemAlerts.length > 0
    });
  }, [isClient, requests, pendingHITLRequests.length, systemAlerts.length]);

  // Mock budget calculation - in real app, this would come from backend
  useEffect(() => {
    if (currentProject && currentProject.budget_limit) {
      const mockUsed = Math.random() * currentProject.budget_limit * 0.7; // Mock current usage
      const percentage = (mockUsed / currentProject.budget_limit) * 100;
      setBudgetUsage({
        used: mockUsed,
        limit: currentProject.budget_limit,
        percentage
      });
    }
  }, [currentProject]);

  // Check for critical budget threshold
  const isBudgetCritical = budgetUsage.percentage > 85;
  const isBudgetWarning = budgetUsage.percentage > 70;

  // Show alerts bar if there are any alerts, budget warnings, or HITL requests
  const hasAlerts = systemAlerts.length > 0 ||
                    pendingHITLRequests.length > 0 ||
                    isBudgetWarning ||
                    safetyAlerts.some(alert => !alert.acknowledged);

  if (!hasAlerts) {
    return null;
  }

  const handleHITLClick = (requestId: string) => {
    const request = requests.find(r => r.id === requestId);
    if (!request) {
      console.warn('[HITLAlertsBar] Request not found:', requestId);
      return;
    }

    // Check if request has expired (30 minute expiration)
    const requestAge = new Date().getTime() - new Date(request.timestamp).getTime();
    const THIRTY_MINUTES = 30 * 60 * 1000;
    
    if (requestAge > THIRTY_MINUTES) {
      console.warn('[HITLAlertsBar] Request has expired, removing from store');
      resolveRequest(requestId, 'rejected', 'Request expired').catch(() => {
        // Already handled in resolveRequest
      });
      return;
    }

    // Get project ID from context
    const projectId = request.context?.projectId;
    
    if (projectId) {
      console.log('[HITLAlertsBar] Navigating to project:', projectId);
      
      // Navigate to project workspace if not already there
      if (currentView !== 'project-workspace' || currentProject?.id !== projectId) {
        navigateToProject(projectId);
      }

      // Wait for navigation and DOM updates, then scroll to message
      setTimeout(() => {
        const approvalId = request.context?.approvalId;
        
        // Try multiple selectors to find the HITL message
        const selectors = [
          `[data-approval-id="${approvalId}"]`,
          `[data-request-id="${requestId}"]`,
          `[data-task-id="${request.context?.taskId}"]`
        ];

        let targetElement = null;
        for (const selector of selectors) {
          targetElement = document.querySelector(selector);
          if (targetElement) {
            console.log('[HITLAlertsBar] Found HITL message with selector:', selector);
            break;
          }
        }

        if (targetElement) {
          targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
          // Add a temporary highlight
          targetElement.classList.add('bg-yellow-100', 'ring-2', 'ring-yellow-300', 'dark:bg-yellow-900/20');
          setTimeout(() => {
            targetElement?.classList.remove('bg-yellow-100', 'ring-2', 'ring-yellow-300', 'dark:bg-yellow-900/20');
          }, 3000);
        } else {
          console.warn('[HITLAlertsBar] Could not find HITL message element. Tried selectors:', selectors);
          // Fallback: just scroll to chat section
          const chatElement = document.querySelector('[data-testid="chat-section"]');
          if (chatElement) {
            chatElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }
      }, currentView !== 'project-workspace' ? 800 : 300); // Longer delay if navigating
    } else {
      console.warn('[HITLAlertsBar] No project ID found in HITL request context');
    }

    // Set the agent filter to show HITL for the specific agent
    setAgentFilter(request.agentName);
    // Navigate to the request to make it active
    navigateToRequest(requestId);
  };

  const handleHITLDismiss = async (requestId: string) => {
    try {
      await resolveRequest(requestId, 'rejected', 'Dismissed from alerts bar');
    } catch (error) {
      console.error('[HITLAlertsBar] Error dismissing HITL request:', error);
      // Request was already removed from store by resolveRequest error handling
    }
  };

  const handleEmergencyStop = async () => {
    if (!currentProject) return;

    setShowEmergencyStop(true);
    try {
      await safetyEventHandler.triggerEmergencyStop(
        currentProject.id,
        'Emergency stop triggered from alert bar'
      );
    } catch (error) {
      console.error('Failed to trigger emergency stop:', error);
    } finally {
      setShowEmergencyStop(false);
    }
  };

  return (
    <div className="border-b border-border px-6 py-2 bg-card">
      <div className="flex items-center space-x-3 overflow-x-auto overflow-y-hidden h-12">
        {/* System Alerts */}
        {systemAlerts.map((alert) => {
          const isExpanded = expandedAlerts.includes(alert.id);
          const shortMessage = `${alert.stage || 'General'}`;

          return (
            <div key={alert.id} className="flex items-center space-x-2 bg-amber-50 border border-amber-200 text-amber-800 px-3 py-1 rounded-full flex-shrink-0 whitespace-nowrap">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <button
                onClick={() => toggleExpanded(alert.id)}
                className="flex items-center space-x-1 hover:bg-amber-100 rounded transition-colors"
              >
                <span className="text-sm font-medium">
                  {isExpanded ? alert.message : shortMessage}
                </span>
                <ChevronDown className={`w-3 h-3 text-amber-600 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
              </button>
              <Button 
                size="icon" 
                variant="ghost" 
                className="h-5 w-5 text-amber-600 hover:bg-amber-100" 
                onClick={() => dismissAlert(alert.id)}
                title="Dismiss alert"
              >
                <X className="w-3 h-3" />
              </Button>
            </div>
          );
        })}

        {/* HITL Alerts */}
        {pendingHITLRequests.slice(0, 3).map((request) => {
          const message = `${request.agentName} needs approval`;

          return (
            <div key={request.id} className="flex items-center space-x-2 bg-orange-50 border border-orange-200 text-orange-800 px-3 py-1 rounded-full flex-shrink-0 whitespace-nowrap">
              <AlertTriangle className="w-4 h-4 text-orange-600" />
              <button
                onClick={() => handleHITLClick(request.id)}
                className="flex items-center space-x-1 hover:bg-orange-100 rounded transition-colors cursor-pointer"
                title="Click to navigate to HITL chat"
              >
                <span className="text-sm font-medium">
                  {message}
                </span>
              </button>
              <Button 
                size="icon" 
                variant="ghost" 
                className="h-5 w-5 text-orange-600 hover:bg-orange-100" 
                onClick={() => handleHITLDismiss(request.id)}
                title="Dismiss HITL request"
              >
                <X className="w-3 h-3" />
              </Button>
            </div>
          )
        })}

        {/* Show count if there are more HITL requests */}
        {pendingHITLRequests.length > 3 && (
          <div className="flex items-center space-x-2 bg-blue-50 border border-blue-200 text-blue-800 px-3 py-1 rounded-full flex-shrink-0 whitespace-nowrap">
            <span className="text-sm font-medium">
              +{pendingHITLRequests.length - 3} more HITL requests
            </span>
          </div>
        )}

        {/* Budget Control Monitoring */}
        {currentProject && currentProject.budget_limit && isBudgetWarning && (
          <div className={`flex items-center space-x-2 px-3 py-1 rounded-full border ${
            isBudgetCritical
              ? 'bg-red-50 border-red-200 text-red-800'
              : 'bg-yellow-50 border-yellow-200 text-yellow-800'
          }`}>
            <DollarSign className={`w-4 h-4 ${isBudgetCritical ? 'text-red-600' : 'text-yellow-600'}`} />
            <div className="flex items-center space-x-1">
              <span className="text-sm font-medium">
                Budget: ${budgetUsage.used.toFixed(2)}/${budgetUsage.limit}
              </span>
              <Badge variant="outline" className="text-xs">
                {budgetUsage.percentage.toFixed(0)}%
              </Badge>
            </div>
            <div className="w-16">
              <Progress
                value={budgetUsage.percentage}
                className={`h-2 ${isBudgetCritical ? 'bg-red-100' : 'bg-yellow-100'}`}
              />
            </div>
          </div>
        )}

        {/* Safety Alerts */}
        {safetyAlerts.filter(alert => !alert.acknowledged).slice(0, 2).map((alert) => (
          <div key={alert.id} className={`flex items-center space-x-2 px-3 py-1 rounded-full border ${
            alert.severity === 'critical' ? 'bg-red-50 border-red-200 text-red-800' :
            alert.severity === 'high' ? 'bg-orange-50 border-orange-200 text-orange-800' :
            'bg-yellow-50 border-yellow-200 text-yellow-800'
          }`}>
            <Shield className={`w-4 h-4 ${
              alert.severity === 'critical' ? 'text-red-600' :
              alert.severity === 'high' ? 'text-orange-600' : 'text-yellow-600'
            }`} />
            <span className="text-sm font-medium">
              {alert.title}
            </span>
            <Badge variant="outline" className="text-xs">
              {alert.severity.toUpperCase()}
            </Badge>
          </div>
        ))}

        {/* Emergency Stop Control */}
        {currentProject && (
          <div className="flex items-center space-x-2">
            <Button
              size="sm"
              variant="destructive"
              onClick={handleEmergencyStop}
              disabled={showEmergencyStop}
              className="bg-red-600 hover:bg-red-700 text-white"
              title="Emergency Stop - Immediately halt all agents"
            >
              <StopCircle className="w-3 h-3 mr-1" />
              {showEmergencyStop ? 'Stopping...' : 'Emergency Stop'}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};