import websockets
import asyncio


class WebSocketServer:
    def __init__(self, secret_key: str, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.secret_key = secret_key  # Expected secret key for authentication.
        self.connected_websockets = set()

    async def send_message(self, message: str):
        """Send a message to all connected and authenticated WebSocket clients."""
        if self.connected_websockets:
            await asyncio.gather(
                *[ws.send(message) for ws in self.connected_websockets]
            )

    async def websocket_handler(self, websocket):
        """Handle new WebSocket connections with authentication.
        Expects the client to send the secret key as its first message.
        """
        try:
            # Wait for the client to send the secret key as the first message.
            received_key = await asyncio.wait_for(websocket.recv(), timeout=10)
            if received_key != self.secret_key:
                await websocket.send("Authentication failed. Disconnecting.")
                await websocket.close()
                return

            # Authentication successful.
            await websocket.send("Authentication successful. You are now connected.")
            self.connected_websockets.add(websocket)
            print(f"Client authenticated: {websocket.remote_address}")

            # Process further messages from the client.
            async for message in websocket:
                # Here, process the messages from the authenticated client.
                pass

        except asyncio.TimeoutError:
            # Client did not send the secret key in time.
            await websocket.send("Authentication timeout. Disconnecting.")
            await websocket.close()

        except Exception as e:
            print(f"WebSocket error: {e}")

        finally:
            if websocket in self.connected_websockets:
                self.connected_websockets.remove(websocket)

    async def start_server(self):
        """Start the authenticated WebSocket server."""
        async with websockets.serve(
            self.websocket_handler, self.host, self.port, origins=None
        ):
            print(f"WebSocket server started on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever
