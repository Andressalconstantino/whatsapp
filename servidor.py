import socket
import threading
import time

class ChatServer:
    def __init__(self, host='localhost', port=12345):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        print(f"Servidor iniciado em {host}:{port}")
        
        self.clients = {}  # Armazenar clientes {client_id: (connection, address)}
        self.pending_messages = {}  # Mensagens pendentes {client_id: [(message_data)]}
    
    def generate_client_id(self):
        return str(int(time.time() * 1000)).zfill(13)  # Gerar um ID único com 13 dígitos
    
    def handle_client(self, connection, address):
        try:
            while True:
                data = connection.recv(1024).decode('utf-8')
                if not data:
                    break
                print(f"Recebido de {address}: {data}")
                self.process_message(connection, data)
        except ConnectionResetError:
            print(f"Conexão com {address} perdida.")
        finally:
            connection.close()
    
    def process_message(self, connection, message):
        code = message[:2]
        if code == "01":  # Registrar cliente
            client_id = self.generate_client_id()
            self.clients[client_id] = (connection, None)
            response = f"02{client_id}"
            connection.sendall(response.encode('utf-8'))
        elif code == "03":  # Conectar cliente
            client_id = message[2:15]
            if client_id in self.clients:
                self.clients[client_id] = (connection, None)
                self.deliver_pending_messages(client_id)
    
    def deliver_pending_messages(self, client_id):
        if client_id in self.pending_messages:
            for message in self.pending_messages[client_id]:
                self.clients[client_id][0].sendall(message.encode('utf-8'))
            del self.pending_messages[client_id]
    
    def run(self):
        while True:
            connection, address = self.server_socket.accept()
            print(f"Conexão aceita de {address}")
            threading.Thread(target=self.handle_client, args=(connection, address)).start()

if __name__ == "__main__":
    server = ChatServer()
    server.run()
