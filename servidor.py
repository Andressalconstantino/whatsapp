import asyncio
import websockets
import json

class ChatServer:
    def __init__(self):
        self.clients = {}  # clients {client_id: websocket}

    async def handle_connection(self, websocket, path):
        client_id = str(id(websocket))
        self.clients[client_id] = websocket
        await self.send_user_list()

        try:
            async for message in websocket:
                await self.process_message(client_id, message)
        except websockets.ConnectionClosed:
            print(f"Conexão com {client_id} fechada.")
        finally:
            del self.clients[client_id]
            await self.send_user_list()  # Update user list when a client disconnects

    async def process_message(self, client_id, message):
        data = json.loads(message)
        if data['type'] == 'chat':
            recipient_id = data['recipient']
            if recipient_id in self.clients:
                await self.clients[recipient_id].send(message)
            else:
                print(f"Cliente {recipient_id} não encontrado.")
        elif data['type'] == 'register':
            # Handle user registration or other types of messages if necessary
            pass

    async def send_user_list(self):
        user_list = list(self.clients.keys())
        for client_id, websocket in self.clients.items():
            message = json.dumps({
                'type': 'user_list',
                'users': user_list
            })
            await websocket.send(message)

    def run(self):
        start_server = websockets.serve(self.handle_connection, "localhost", 8765)
        asyncio.get_event_loop().run_until_complete(start_server)
        print("Servidor WebSocket iniciado em ws://localhost:8765")
        asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    server = ChatServer()
    server.run()
