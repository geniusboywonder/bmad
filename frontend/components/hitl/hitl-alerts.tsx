"use client";

import React from 'react';
import { useHITLStore } from '@/lib/stores/hitl-store';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, ChevronRight } from 'lucide-react';

export const HITLAlerts = () => {
  const { requests, navigateToRequest } = useHITLStore();
  const pendingRequests = requests.filter(r => r.status === 'pending');

  if (pendingRequests.length === 0) {
    return null;
  }

  return (
    <div className="flex items-center gap-2">
      {pendingRequests.slice(0, 2).map((request) => (
        <Alert
          key={request.id}
          className="bg-amber-50 border-amber-200 cursor-pointer hover:bg-amber-100"
          onClick={() => navigateToRequest(request.id)}
        >
          <AlertTriangle className="h-4 w-4 text-amber-600" />
          <AlertDescription className="text-amber-800">
            {request.agentName} needs approval
            <ChevronRight className="h-3 w-3 ml-1 inline" />
          </AlertDescription>
        </Alert>
      ))}

      {pendingRequests.length > 2 && (
        <Badge variant="outline" className="cursor-pointer">
          +{pendingRequests.length - 2} more
        </Badge>
      )}
    </div>
  );
};
