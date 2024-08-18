import socket
import time

class ChatClient:
    def __init__(self, host='localhost', port=12345):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))
        self.client_id = None
    
    def register(self):
        message = "01"  # Código para registrar cliente
        self.client_socket.sendall(message.encode('utf-8'))
        response = self.client_socket.recv(1024).decode('utf-8')
        if response.startswith("02"):
            self.client_id = response[2:15]
            print(f"Registrado com ID: {self.client_id}")
    
    def connect(self):
        if self.client_id:
            message = f"03{self.client_id}"
            self.client_socket.sendall(message.encode('utf-8'))
    
    def send_message(self, dst, data):
        if self.client_id:
            timestamp = str(int(time.time())).zfill(10)
            message = f"05{self.client_id}{dst}{timestamp}{data.ljust(218)}"
            self.client_socket.sendall(message.encode('utf-8'))
    
    def run(self):
        self.register()
        self.connect()
        while True:
            data = input("Mensagem: ")
            self.send_message("DESTINATARIO_ID", data)  # Substituir por um ID de destinatário válido

if __name__ == "__main__":
    client = ChatClient()
    client.run()
