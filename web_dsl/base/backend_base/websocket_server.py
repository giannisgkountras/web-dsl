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
            ws for conns in self.connected_clients_by_role.values() for ws in conns
        ]
        print("Broadcasting message to all connected clients.", all_connections)
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
        """
        Handle new WebSocket connections.
        Authenticates users with a JWT and assigns a role.
        If authentication fails or is skipped, assigns an 'unauthorized' role.
        """
        # Set default identifiers for logging purposes before authentication.
        user_id = f"anonymous_{websocket.remote_address}"
        user_role = None

        try:
            # --- Block for Authentication and Authorization ---
            try:
                # 1. ATTEMPT AUTHENTICATION: Wait for a token.
                user_token = await asyncio.wait_for(websocket.recv(), timeout=10)
                payload = jwt.decode(user_token, self.secret_key, algorithms=["HS256"])
                email = payload.get("email")

                # 2. ATTEMPT AUTHORIZATION: Check if the user and their role exist.
                role = self.user_roles.get(email)

                if email and role:
                    # Case A: Success - User is authenticated and authorized.
                    user_id = email
                    user_role = role
                    await websocket.send(
                        f"Authentication successful. Connected as role: {user_role}."
                    )
                else:
                    # Case B: Valid JWT, but user/role not found in our system.
                    user_id = email or user_id  # Keep email for logging if it exists
                    user_role = "unauthorized"
                    await websocket.send(
                        "JWT valid, but role not assigned. Connected as unauthorized."
                    )

            except (asyncio.TimeoutError, jwt.PyJWTError) as auth_error:
                # Case C: No token sent or token is invalid. Assign 'unauthorized'.
                print(
                    f"Authentication failed for {websocket.remote_address}: {auth_error}. Assigning 'unauthorized' role."
                )
                user_role = "unauthorized"
                await websocket.send(
                    "Could not authenticate. Connected as unauthorized."
                )

            # --- At this point, every connection has a role (either real or 'unauthorized') ---

            # 3. REGISTER: Add the connection to the correct role group.
            await self._register_client(user_role, websocket)

            # 4. MESSAGE HANDLING: Keep the connection alive.
            async for message in websocket:
                print(
                    f"Received message from '{user_id}' (role: {user_role}): {message}"
                )

                # Example of role-based permissions:
                if user_role == "unauthorized":
                    await websocket.send(
                        "Action denied. Please log in to perform this action."
                    )
                    continue

                # Add other message processing for authorized users here...

        except websockets.exceptions.ConnectionClosed:
            print(f"Connection for '{user_id}' (role: {user_role}) closed normally.")
        except Exception as e:
            print(
                f"An unexpected error occurred for '{user_id}' (role: {user_role}): {e}"
            )
            if not websocket.closed:
                await websocket.close()
        finally:
            # 5. UNREGISTER: Clean up the connection from its role group.
            # This will run for both authorized and unauthorized users.
            if user_role:
                await self._unregister_client(user_role, websocket)

    async def start_server(self):
        """Start the authenticated WebSocket server."""
        async with websockets.serve(
            self.websocket_handler, self.host, self.port, origins=None
        ):
            print(f"WebSocket server started on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever
