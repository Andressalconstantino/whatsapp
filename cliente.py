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
                    group_or_dst = message[15:28]
                    data = message[38:].strip()
                    print(f"Mensagem de {src} para {group_or_dst}: {data}")
                    # Enviar confirmação de leitura
                    self.send_read_confirmation(src, message[28:38])
                elif code == "07":  # Confirmação de entrega
                    dst = message[2:15]
                    timestamp = message[15:25]
                    print(f"Mensagens entregues para {dst} até {timestamp}.")
                elif code == "09":  # Confirmação de leitura
                    dst = message[2:15]
                    timestamp = message[15:25]
                    print(f"Mensagens de {dst} lidas até {timestamp}.")
                elif code == "12":  # Recebendo confirmação de criação de grupo
                    group_id = message[2:]
                    print(f"Grupo criado com sucesso! ID do grupo: {group_id}")
            except ConnectionResetError:
                print("Conexão perdida com o servidor.")
                break



    
    def send_read_confirmation(self, src, timestamp):
        if self.client_id:
            message = f"08{src}{timestamp}"
            self.client_socket.sendall(message.encode('utf-8'))

    
    def connect(self):
        if self.client_id:
            message = f"03{self.client_id}"
            self.client_socket.sendall(message.encode('utf-8'))
    
    def send_message(self, dst, data):
        if self.client_id:
            timestamp = str(int(time.time())).zfill(10)
            message = f"05{self.client_id}{dst}{timestamp}{data.ljust(218)}"
            self.client_socket.sendall(message.encode('utf-8'))

    def create_group(self, members):
        if self.client_id:
            timestamp = str(int(time.time()))
            members_str = ''.join(members)  # Formatar IDs dos membros
            message = f"10{self.client_id}{timestamp}{members_str}"
            self.client_socket.sendall(message.encode('utf-8'))

    
    def run(self):
        self.register()
        self.connect()
        threading.Thread(target=self.listen_for_messages).start()
        
        while True:
            action = input("Digite '1' para enviar uma mensagem, '2' para criar um grupo, ou '3' para enviar mensagem para um grupo: ")
            if action == '1':
                data = input("Mensagem: ")
                recipient_id = input("ID do destinatário: ")
                self.send_message(recipient_id, data)
            elif action == '2':
                members = []
                while True:
                    member_id = input("ID do membro (ou deixe em branco para finalizar): ")
                    if not member_id:
                        break
                    members.append(member_id)
                self.create_group(members)
            elif action == '3':
                group_id = input("ID do grupo: ")
                data = input("Mensagem para o grupo: ")
                self.send_message(group_id, data)

if __name__ == "__main__":
    client = ChatClient()
    client.run()
