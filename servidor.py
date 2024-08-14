import socket
import threading
import time
import pickle  # Para persistência de dados

class ChatServer:
    def init(self, host='localhost', port=12345):
        self.server = socket.socket(socket.AFINET, socket.SOCKSTREAM)
        self.server.bind((host, port))
        self.server.listen(5)
        self.clients = {}
        self.pendingmessages = {}

    def handleclient(self, client_socket):
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if message:
                    self.process_message(client_socket, message)
            except:
                client_socket.close()
                break

    def process_message(self, client_socket, message):
        # Processar a mensagem recebida
        pass

    def run(self):
        print("Servidor iniciado e aguardando conexões...")
        while True:
            client_socket, addr = self.server.accept()
            print(f"Conexão estabelecida com {addr}")
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_handler.start()

if __name == "__main":
    server = ChatServer()
    server.run()