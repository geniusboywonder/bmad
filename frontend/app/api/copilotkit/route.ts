/**
 * CopilotKit Runtime Endpoint
 *
 * Adapts CopilotKit frontend to AG-UI backend endpoints
 */

import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";

const BACKEND_BASE_URL = "http://localhost:8000";

const serviceAdapter = new ExperimentalEmptyAdapter();

// Create agents factory to get fresh instances
function createAgents() {
  return {
    analyst: new HttpAgent({
      url: `${BACKEND_BASE_URL}/api/copilotkit/analyst`,
    }),
    architect: new HttpAgent({
      url: `${BACKEND_BASE_URL}/api/copilotkit/architect`,
    }),
    coder: new HttpAgent({
      url: `${BACKEND_BASE_URL}/api/copilotkit/coder`,
    }),
    orchestrator: new HttpAgent({
      url: `${BACKEND_BASE_URL}/api/copilotkit/orchestrator`,
    }),
    tester: new HttpAgent({
      url: `${BACKEND_BASE_URL}/api/copilotkit/tester`,
    }),
    deployer: new HttpAgent({
      url: `${BACKEND_BASE_URL}/api/copilotkit/deployer`,
    }),
  };
}

export const POST = async (req: NextRequest) => {
  // Create fresh runtime for each request to prevent agent list mutation
  const agents = createAgents();
  const runtime = new CopilotRuntime({ agents });

  console.log('[CopilotKit Runtime] Handling request, available agents:', Object.keys(agents));

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
