"use client";

import React, { useState } from 'react';
import { MainLayout } from '@/components/main-layout';
import { useHITLStore } from '@/lib/stores/hitl-store';
import { HITLApprovalComponent } from '@/components/hitl/hitl-approval';
import { HITLAlerts } from '@/components/hitl/hitl-alerts';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Trash2, RefreshCw } from 'lucide-react';

const DEMO_REQUESTS = [
  {
    agentName: 'Analyst',
    decision: 'Should I proceed with the database schema analysis for the e-commerce platform?',
    context: { 
      artifactName: 'Execution Plan',
      tables: ['users', 'products', 'orders'], 
      complexity: 'medium',
      estimated_time: '2 hours' 
    },
    priority: 'high' as const,
  },
  {
    agentName: 'Developer',
    decision: 'Deploy the new authentication system to production?',
    context: { 
      artifactName: 'User Stories',
      version: 'v2.1.0', 
      tests_passed: true, 
      breaking_changes: false 
    },
    priority: 'urgent' as const,
  },
  {
    agentName: 'Architect',
    decision: 'Switch from REST to GraphQL for the new API endpoints?',
    context: { 
      artifactName: 'Acceptance Criteria',
      endpoints: 12, 
      migration_effort: 'medium',
      benefits: ['better caching', 'reduced over-fetching']
    },
    priority: 'medium' as const,
  },
  {
    agentName: 'Tester',
    decision: 'Skip integration tests for this minor bug fix?',
    context: { 
      artifactName: 'Example of Artifacts',
      bug_severity: 'low', 
      affected_users: '< 5%',
      time_saved: '30 minutes'
    },
    priority: 'low' as const,
  },
];

export default function HITLTestPage() {
  const { 
    requests, 
    addRequest, 
    resolveRequest, 
    getPendingCount, 
    getRequestsByAgent,
    navigateToRequest,
    activeRequest 
  } = useHITLStore();
  
  const [selectedAgent, setSelectedAgent] = useState<string>('');

  const handleAddDemoRequest = (demoRequest: typeof DEMO_REQUESTS[0]) => {
    addRequest(demoRequest);
  };

  const handleAddAllDemoRequests = () => {
    DEMO_REQUESTS.forEach(request => addRequest(request));
  };

  const handleClearAllRequests = () => {
    useHITLStore.setState({ requests: [], activeRequest: null });
  };

  const handleApprove = (requestId: string) => {
    resolveRequest(requestId, 'approved', 'Approved via test interface');
  };

  const handleReject = (requestId: string) => {
    resolveRequest(requestId, 'rejected', 'Rejected via test interface');
  };

  const handleModify = (requestId: string, feedback: string) => {
    resolveRequest(requestId, 'modified', feedback);
  };

  const pendingRequests = requests.filter(r => r.status === 'pending');
  const agentNames = [...new Set(requests.map(r => r.agentName))];

  return (
    <MainLayout>
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">HITL Testing Interface</h1>
          <div className="flex items-center gap-2">
            <Badge variant="outline">
              {getPendingCount()} Pending
            </Badge>
            <Badge variant="secondary">
              {requests.length} Total
            </Badge>
          </div>
        </div>

        {/* HITL Alerts Demo */}
        <Card>
          <CardHeader>
            <CardTitle>Header Alerts Demo</CardTitle>
          </CardHeader>
          <CardContent>
            <HITLAlerts />
            {pendingRequests.length === 0 && (
              <p className="text-muted-foreground">No pending requests to show</p>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Test Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <Button onClick={handleAddAllDemoRequests}>
                Add All Demo Requests
              </Button>
              <Button variant="outline" onClick={handleClearAllRequests}>
                <Trash2 className="w-4 h-4 mr-2" />
                Clear All
              </Button>
              <Button variant="outline" onClick={() => window.location.reload()}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh Page
              </Button>
            </div>
            
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">Add individual demo requests:</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {DEMO_REQUESTS.map((request, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    size="sm"
                    onClick={() => handleAddDemoRequest(request)}
                  >
                    Add {request.agentName} Request
                    <Badge variant={request.priority === 'urgent' ? 'destructive' : 'secondary'} className="ml-2">
                      {request.priority}
                    </Badge>
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Active Request Details */}
        {activeRequest && (
          <Card className="border-amber-200 bg-amber-50">
            <CardHeader>
              <CardTitle className="text-amber-800">Active HITL Request</CardTitle>
            </CardHeader>
            <CardContent>
              <HITLApprovalComponent
                agentName={activeRequest.agentName}
                decision={activeRequest.decision}
                context={activeRequest.context}
                priority={activeRequest.priority}
                onApprove={() => handleApprove(activeRequest.id)}
                onReject={() => handleReject(activeRequest.id)}
                onModify={(feedback) => handleModify(activeRequest.id, feedback)}
              />
            </CardContent>
          </Card>
        )}

        {/* Pending Requests */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Pending HITL Requests ({pendingRequests.length})</CardTitle>
              <div className="flex items-center gap-2">
                <select
                  value={selectedAgent}
                  onChange={(e) => setSelectedAgent(e.target.value)}
                  className="px-3 py-1 border rounded text-sm"
                >
                  <option value="">All Agents</option>
                  {agentNames.map(agent => (
                    <option key={agent} value={agent}>{agent}</option>
                  ))}
                </select>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {pendingRequests
              .filter(req => !selectedAgent || req.agentName === selectedAgent)
              .map((request) => (
                <div key={request.id} className="space-y-2">
                  <HITLApprovalComponent
                    agentName={request.agentName}
                    decision={request.decision}
                    context={request.context}
                    priority={request.priority}
                    onApprove={() => handleApprove(request.id)}
                    onReject={() => handleReject(request.id)}
                    onModify={(feedback) => handleModify(request.id, feedback)}
                  />
                  <div className="flex justify-end gap-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => navigateToRequest(request.id)}
                    >
                      Set as Active
                    </Button>
                  </div>
                </div>
              ))}
            {pendingRequests.length === 0 && (
              <p className="text-center text-muted-foreground py-8">
                No pending requests. Add some demo requests to test the interface.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Completed Requests */}
        <Card>
          <CardHeader>
            <CardTitle>Request History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {requests
                .filter(r => r.status !== 'pending')
                .map((request) => (
                  <div
                    key={request.id}
                    className="flex items-center justify-between p-3 border rounded"
                  >
                    <div className="flex-1">
                      <div className="font-medium">{request.agentName}</div>
                      <div className="text-sm text-muted-foreground truncate max-w-md">
                        {request.decision}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {request.timestamp.toLocaleString()}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={
                          request.status === 'approved' ? 'default' :
                          request.status === 'rejected' ? 'destructive' : 'secondary'
                        }
                      >
                        {request.status}
                      </Badge>
                      {request.response && (
                        <div className="text-xs bg-muted p-1 rounded max-w-xs truncate">
                          {request.response}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              {requests.filter(r => r.status !== 'pending').length === 0 && (
                <p className="text-center text-muted-foreground py-4">
                  No completed requests yet.
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
}