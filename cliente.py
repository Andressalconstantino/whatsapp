import socket
import time
import threading

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
    
    def listen_for_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                code = message[:2]
                if code == "05":  # Recebendo uma mensagem
                    src = message[2:15]
                    data = message[38:].strip()
                    print(f"Mensagem de {src}: {data}")
                elif code == "07":  # Confirmação de entrega
                    dst = message[2:15]
                    timestamp = message[15:25]
                    print(f"Mensagens entregues para {dst} até {timestamp}.")
            except ConnectionResetError:
                print("Conexão perdida com o servidor.")
                break
    
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
        threading.Thread(target=self.listen_for_messages).start()
        while True:
            data = input("Mensagem: ")
            recipient_id = input("ID do destinatário: ")
            self.send_message(recipient_id, data)  # Substituir por um ID de destinatário válido

if __name__ == "__main__":
    client = ChatClient()
    client.run()
