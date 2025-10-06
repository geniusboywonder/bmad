/**
 * Next.js API Route Proxy for AG-UI CopilotKit
 *
 * Proxies requests from frontend CopilotKit to backend AG-UI endpoints
 */

import { NextRequest } from 'next/server';

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ agent: string }> }
) {
  const { agent } = await params;

  // Backend AG-UI endpoint
  const backendUrl = `http://localhost:8000/api/copilotkit/${agent}`;

  try {
    const body = await request.text();

    // Forward request to backend
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: body,
    });

    // Return backend response
    const data = await response.text();

    return new Response(data, {
      status: response.status,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  } catch (error) {
    console.error(`[CopilotKit Proxy] Error forwarding to ${backendUrl}:`, error);

    return new Response(
      JSON.stringify({
        error: 'Backend AG-UI endpoint unavailable',
        message: error instanceof Error ? error.message : 'Unknown error'
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ agent: string }> }
) {
  const { agent } = await params;

  return new Response(
    JSON.stringify({
      status: 'ready',
      agent: agent,
      endpoint: `/api/copilotkit/${agent}`,
      backend: `http://localhost:8000/api/copilotkit/${agent}`
    }),
    {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    }
  );
}
