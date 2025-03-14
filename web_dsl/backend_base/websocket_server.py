import websockets
import asyncio


class WebSocketServer:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.connected_websockets = set()

    async def send_message(self, message: str):
        """Send a message to all connected WebSocket clients."""
        if self.connected_websockets:
            await asyncio.gather(
                *[ws.send(message) for ws in self.connected_websockets]
            )

    async def websocket_handler(self, websocket):
        """Handle new WebSocket connections."""
        self.connected_websockets.add(websocket)
        try:
            async for _ in websocket:
                pass  # Keep the connection alive
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            self.connected_websockets.remove(websocket)

    async def start_server(self):
        """Start the WebSocket server."""
        async with websockets.serve(
            self.websocket_handler, self.host, self.port, origins=None
        ):
            print(f"WebSocket server started on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever
