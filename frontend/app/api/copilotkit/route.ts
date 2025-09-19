import { webSocketBridge } from "@/lib/websocket/websocket-bridge";

export async function POST(req: Request): Promise<Response> {
  const transformStream = new TransformStream();
  const writer = transformStream.writable.getWriter();
  const encoder = new TextEncoder();

  const listener = (message: any) => {
    console.log("Writing to stream:", message);
    writer.write(encoder.encode("data: " + JSON.stringify(message) + "\n\n"));
  };
  webSocketBridge.addMessageListener(listener);

  req.signal.onabort = () => {
    webSocketBridge.removeMessageListener(listener);
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
        webSocketBridge.sendMessage(backendMessage)
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
