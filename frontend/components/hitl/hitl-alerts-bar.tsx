"use client";

import React from 'react';
import { useHITLStore } from '@/lib/stores/hitl-store';
import { useAgentStore } from '@/lib/stores/agent-store';
import { Button } from '@/components/ui/button';
import { AlertTriangle, ChevronDown, X } from 'lucide-react';

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
  const { requests, navigateToRequest, resolveRequest } = useHITLStore();
  const { setAgentFilter } = useAgentStore();
  const pendingHITLRequests = isClient ? requests.filter(r => r.status === 'pending') : [];

  // Show alerts bar only if there are system alerts or HITL requests
  const hasAlerts = systemAlerts.length > 0 || pendingHITLRequests.length > 0;

  if (!hasAlerts) {
    return null;
  }

  const handleHITLClick = (requestId: string) => {
    const request = requests.find(r => r.id === requestId);
    if (request) {
      // Set the agent filter to show HITL for the specific agent
      setAgentFilter(request.agentName);
      // Navigate to the request to make it active
      navigateToRequest(requestId);
      // Scroll to chat section if it exists
      const chatElement = document.querySelector('[data-testid="copilot-chat"], .copilot-chat, #chat-container');
      if (chatElement) {
        chatElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  };

  const handleHITLDismiss = (requestId: string) => {
    resolveRequest(requestId, 'rejected', 'Dismissed from alerts bar');
  };

  return (
    <div className="border-b border-border px-6 py-2 bg-card">
      <div className="flex items-center space-x-3">
        {/* System Alerts */}
        {systemAlerts.map((alert) => {
          const isExpanded = expandedAlerts.includes(alert.id);
          const shortMessage = `${alert.stage || 'General'}`;
          
          return (
            <div key={alert.id} className="flex items-center space-x-2 bg-amber-50 border border-amber-200 text-amber-800 px-3 py-1 rounded-full">
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
            <div key={request.id} className="flex items-center space-x-2 bg-orange-50 border border-orange-200 text-orange-800 px-3 py-1 rounded-full">
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
          <div className="flex items-center space-x-2 bg-blue-50 border border-blue-200 text-blue-800 px-3 py-1 rounded-full">
            <span className="text-sm font-medium">
              +{pendingHITLRequests.length - 3} more HITL requests
            </span>
          </div>
        )}
      </div>
    </div>
  );
};