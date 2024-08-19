import asyncio
import websockets
import json
import threading

class ChatServer:
    def __init__(self):
        self.clients = {}  # {client_id: websocket}
        self.lock = threading.Lock()  # Para gerenciar o acesso a `self.clients` entre threads

    async def handle_connection(self, websocket, path):
        client_id = str(id(websocket))
        
        with self.lock:
            self.clients[client_id] = websocket
        
        await self.send_user_list()

        try:
            async for message in websocket:
                await self.process_message(client_id, message)
        except websockets.ConnectionClosed:
            print(f"Conexão com {client_id} fechada.")
        finally:
            with self.lock:
                del self.clients[client_id]
            await self.send_user_list()  # Atualiza a lista de usuários quando um cliente desconecta

    async def process_message(self, client_id, message):
        data = json.loads(message)
        if data['type'] == 'chat':
            recipient_id = data['recipient']
            # Enviar a mensagem para o destinatário
            if recipient_id in self.clients:
                await self.clients[recipient_id].send(message)
            
            # Enviar a mensagem de volta para o remetente
            # Verifica se o remetente é diferente do destinatário para evitar duplicação
            if recipient_id != client_id:
                await self.clients[client_id].send(message)
        elif data['type'] == 'register':
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
        server = websockets.serve(self.handle_connection, "localhost", 8765)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(server)
        print("Servidor WebSocket iniciado em ws://localhost:8765")
        loop.run_forever()

if __name__ == "__main__":
    server = ChatServer()
    server.run()
