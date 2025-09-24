import { websocketManager } from "@/lib/services/websocket/enhanced-websocket-client";

export async function POST(req: Request): Promise<Response> {
  const transformStream = new TransformStream();
  const writer = transformStream.writable.getWriter();
  const encoder = new TextEncoder();

  // Get the global WebSocket connection
  const globalConnection = websocketManager.getGlobalConnection();

  const listener = (message: any) => {
    console.log("Writing to stream:", message);
    writer.write(encoder.encode("data: " + JSON.stringify(message) + "\n\n"));
  };

  // Subscribe to all message events from the WebSocket
  globalConnection.on('message', listener);

  req.signal.onabort = () => {
    globalConnection.off('message', listener);
    writer.close();
  };

  const forwardRequestToSocket = async () => {
    try {
      const body = await req.json();
      if (body.message) {
        const backendMessage = {
            type: 'user_command',
            data: {
              command: 'chat_message',
              text: body.message,
            },
          };
        globalConnection.send(JSON.stringify(backendMessage));
      }
    } catch (error) {
        // Ignore errors from reading the body, as it might have been already read.
    }
  }

  forwardRequestToSocket();

  return new Response(transformStream.readable, {
    headers: {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}
