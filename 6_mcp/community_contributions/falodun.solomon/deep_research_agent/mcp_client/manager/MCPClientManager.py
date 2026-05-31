class MCPClientManager:

    def __init__(self, clients):
        self.clients = clients

    async def connect_all(self):
        # Sequential connect (assumes clients can connect in any order)
        for client in self.clients:
            await client.connect()

    async def close_all(self):
        # Sequential close (assumes clients can close in any order)
        for client in self.clients:
            try:
                await client.close()
            except Exception as e:
                print(f"[WARN] Cleanup failed: {e}")

    async def disconnect_all(self):
        """
        Gracefully shuts down all managed MCP clients in reverse order 
        to ensure proper structured concurrency cleanup.
        """
        # Close in reverse order (LIFO) to respect AnyIO/Asyncio stacks
        for client in reversed(self.clients):
            try:
                # Only attempt close if the client has a close method
                if hasattr(client, 'close'):
                    await client.close()
            except Exception as e:
                # Log or print warning, but continue closing other clients
                print(f"[WARN] Failed to close client {client}: {e}")
