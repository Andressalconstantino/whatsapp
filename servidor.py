import asyncio
import websockets
import json
from collections import defaultdict

class ChatServer:
    def __init__(self):
        self.clients = {}  # clients {client_id: websocket}
        self.client_names = {}  # client_names {client_id: username}
        self.message_history = defaultdict(lambda: defaultdict(list))  # message_history {user_id: {recipient_id: list of messages}}

    async def handle_connection(self, websocket, path):
        client_id = str(id(websocket))
        self.clients[client_id] = websocket
        self.client_names[client_id] = None  # Initial value, to be set later
        await self.send_user_list()

        try:
            async for message in websocket:
                await self.process_message(client_id, message)
        except websockets.ConnectionClosed:
            print(f"Conexão com {client_id} fechada.")
        finally:
            del self.clients[client_id]
            del self.client_names[client_id]
            await self.send_user_list()  # Update user list when a client disconnects

    async def process_message(self, client_id, message):
        data = json.loads(message)
        if data['type'] == 'chat':
            recipient_id = data['recipient']
            if recipient_id in self.clients:
                # Save message to history for both users
                self.message_history[client_id][recipient_id].append(message)
                self.message_history[recipient_id][client_id].append(message)
                
                # Send message to the recipient
                await self.clients[recipient_id].send(message)
                # Also send message to the sender for immediate feedback
                await self.clients[client_id].send(message)
                
                # Notify both users of the new message
                await self.notify_users(client_id, recipient_id)
            else:
                print(f"Cliente {recipient_id} não encontrado.")
        elif data['type'] == 'register':
            self.client_names[client_id] = data['username']
            await self.send_user_list()
        elif data['type'] == 'request_history':
            recipient_id = data['recipient']
            history = self.message_history[client_id][recipient_id]
            history_message = json.dumps({
                'type': 'history',
                'history': history
            })
            if recipient_id in self.clients:
                await self.clients[recipient_id].send(history_message)
            if client_id in self.clients:
                await self.clients[client_id].send(history_message)
        elif data['type'] == 'user_list':
            await self.send_user_list()

    async def notify_users(self, user1_id, user2_id):
        # Notify both users of updated history
        for user_id in [user1_id, user2_id]:
            history_message = json.dumps({
                'type': 'history',
                'history': self.message_history[user_id][user2_id] if user_id == user1_id else self.message_history[user_id][user1_id]
            })
            if user_id in self.clients:
                await self.clients[user_id].send(history_message)

    async def send_user_list(self):
        user_list = {client_id: self.client_names.get(client_id, client_id) for client_id in self.clients}
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
