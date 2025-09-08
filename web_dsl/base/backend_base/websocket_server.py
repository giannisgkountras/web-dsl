import websockets
import asyncio
import jwt
from websockets.server import WebSocketServerProtocol


class WebSocketServer:
    def __init__(
        self, secret_key: str, user_roles: dict, host: str = "0.0.0.0", port: int = 8765
    ):
        """
        Initializes the WebSocket server.
        Args:
            secret_key (str): The secret key for decoding JWTs.
            user_roles (dict): A dictionary mapping user emails to their roles. E.g., {"user@a.com": "admin"}.
            host (str): The host to bind the server to.
            port (int): The port to listen on.
        """
        self.host = host
        self.port = port
        self.secret_key = secret_key
        self.user_roles = user_roles

        # e.g., {"admin": {<connection1>, <connection2>}}
        self.connected_clients_by_role: dict[str, set[WebSocketServerProtocol]] = {}

    async def send_to_role(self, role: str, message: str):
        """Send a message to all connections belonging to a specific role."""
        if role in self.connected_clients_by_role:
            role_connections = self.connected_clients_by_role[role]
            if role_connections:
                print(
                    f"Sending message to role '{role}' ({len(role_connections)} clients)"
                )
                await asyncio.gather(*[ws.send(message) for ws in role_connections])
        else:
            print(f"No active clients found for role '{role}'")

    async def broadcast(self, message: str):
        """Send a message to every single connected client, regardless of role."""
        all_connections = [
            ws
            for role_ws_set in self.connected_clients_by_role.values()
            for ws in role_ws_set
        ]
        if all_connections:
            print(f"Broadcasting message to {len(all_connections)} total clients.")
            await asyncio.gather(*[ws.send(message) for ws in all_connections])

    async def _register_client(self, role: str, websocket: WebSocketServerProtocol):
        """Add a new client connection to the appropriate role group."""
        self.connected_clients_by_role.setdefault(role, set()).add(websocket)
        print(
            f"Client with role '{role}' connected from {websocket.remote_address}. Total clients in role: {len(self.connected_clients_by_role[role])}"
        )

    async def _unregister_client(self, role: str, websocket: WebSocketServerProtocol):
        """Remove a client connection from its role group and perform cleanup."""
        if role in self.connected_clients_by_role:
            self.connected_clients_by_role[role].remove(websocket)
            print(
                f"Client with role '{role}' disconnected from {websocket.remote_address}."
            )

            # If the role has no more active connections, remove the role entry
            if not self.connected_clients_by_role[role]:
                del self.connected_clients_by_role[role]
                print(
                    f"Role '{role}' has no more connections. Removing from active list."
                )

    async def websocket_handler(self, websocket: WebSocketServerProtocol):
        """Handle new WebSocket connections, authorize their role, and track them."""
        user_id = None
        user_role = None
        try:
            # 1. AUTHENTICATE: Verify the user's identity via JWT
            user_token = await asyncio.wait_for(websocket.recv(), timeout=10)
            payload = jwt.decode(user_token, self.secret_key, algorithms=["HS256"])
            user_id = payload.get("email")

            if not user_id:
                raise ValueError("JWT payload does not contain an 'email' identifier.")

            # 2. AUTHORIZE: Look up the user's role
            user_role = self.user_roles.get(user_id)
            if not user_role:
                # This user is authenticated but not assigned a role. Disconnect them.
                raise ValueError(f"User '{user_id}' does not have an assigned role.")

            # 3. REGISTER: Add the connection to the correct role group
            await self._register_client(user_role, websocket)
            await websocket.send(
                f"Authentication successful. Connected as role: {user_role}."
            )

            # 4. MESSAGE HANDLING: Keep connection alive
            async for message in websocket:
                print(
                    f"Received message from '{user_id}' (role: {user_role}): {message}"
                )
                # You could add logic here, e.g., only allow admins to broadcast
                # if user_role == "admin" and message.startswith("/broadcast"):
                #     await self.broadcast(message.split(" ", 1)[1])

        except websockets.exceptions.ConnectionClosed:
            print(f"Connection for user '{user_id}' closed normally.")
        except asyncio.TimeoutError:
            await websocket.send("Authentication timeout. Disconnecting.")
            await websocket.close()
        except jwt.PyJWTError as e:
            await websocket.send(f"Authentication failed: {e}. Disconnecting.")
            await websocket.close()
        except Exception as e:
            print(f"An error occurred for user '{user_id}': {e}")
            if not websocket.closed:
                await websocket.close()
        finally:
            # 5. UNREGISTER: Clean up the connection from its role group
            if user_role and websocket in self.connected_clients_by_role.get(
                user_role, set()
            ):
                await self._unregister_client(user_role, websocket)

    async def start_server(self):
        """Start the authenticated WebSocket server."""
        async with websockets.serve(
            self.websocket_handler, self.host, self.port, origins=None
        ):
            print(f"WebSocket server started on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever
