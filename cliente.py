import socket
import time
import pickle  # Para persistência de dados

class ChatClient:
    def init(self, host='localhost', port=12345):
        self.client = socket.socket(socket.AFINET, socket.SOCKSTREAM)
        self.client.connect((host, port))
        self.clientid = None
        self.contacts = {}
        self.groups = {}
        self.messagehistory = []

    def register_client(self):
        message = "01"  # Código para registrar cliente
        self.client.send(message.encode('utf-8'))
        response = self.client.recv(1024).decode('utf-8')
        self.client_id = response[2:]
        print(f"Cliente registrado com ID: {self.client_id}")

    def send_message(self, dst, data):
        timestamp = int(time.time())
        message = f"05{self.client_id}{dst}{timestamp}{data}"
        self.client.send(message.encode('utf-8'))

    def receive_message(self):
        while True:
            message = self.client.recv(1024).decode('utf-8')
            # Processar a mensagem recebida
            print(f"Mensagem recebida: {message}")

    def run(self):
        # Registrar ou conectar o cliente, enviar mensagens, etc.
        pass

if __name == "__main":
    client = ChatClient()
    client.register_client()
    client.run()