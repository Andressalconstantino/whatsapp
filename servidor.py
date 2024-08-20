import socket
import threading
import time
import csv
import os

class ChatServer:
    def __init__(self, host='localhost', port=12345):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        print(f"Servidor iniciado em {host}:{port}")
        
        self.clients = {}  # Armazenar clientes {client_id: (connection, address)}
        self.pending_messages = {}  # Mensagens pendentes {client_id: [(message_data)]}
        self.groups = {}  # Armazenar grupos {group_id: [client_id1, client_id2, ...]}
    
    def generate_group_id(self):
        return f"G{str(int(time.time() * 1000)).zfill(12)}"  # Gerar um ID único para o grupo com prefixo 'G'

    def generate_client_id(self):
        return str(int(time.time() * 1000)).zfill(13)  # Gerar um ID único com 13 dígitos
    
    def handle_client(self, connection, address):
        client_id = None
        try:
            while True:
                data = connection.recv(1024).decode('utf-8')
                if not data:
                    break
                print(f"Recebido de {address}: {data}")
                if client_id is None and data.startswith("03"):
                    client_id = data[2:15]
                    self.load_chat_history(client_id)
                self.process_message(connection, data)
        except ConnectionResetError:
            print(f"Conexão com {address} perdida.")
        finally:
            if client_id and client_id in self.clients:
                self.clients.pop(client_id, None)
                self.pending_messages.pop(client_id, None)
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
            print(f"Tentando conectar o cliente {client_id}...")  # Adicionado
            if client_id in self.clients:
                print(f"Cliente {client_id} encontrado.")  # Adicionado
                self.clients[client_id] = (connection, None)
                self.deliver_pending_messages(client_id)
            else:
                print(f"Cliente {client_id} não encontrado.")  # Adicionado

        elif code == "05":  # Enviar mensagem
            src = message[2:15]
            dst = message[15:28]
            timestamp = message[28:38]
            data = message[38:].strip()

            if dst in self.clients and self.clients[dst][0]:  # Destinatário é um cliente conectado
                self.clients[dst][0].sendall(message.encode('utf-8'))
                # Confirmar entrega ao originador
                confirmation = f"07{dst}{timestamp}"
                self.clients[src][0].sendall(confirmation.encode('utf-8'))
                # Salvar mensagem no histórico
                self.save_message(src, dst, data)
            else:
                # Armazenar mensagem se o destinatário estiver offline
                if dst not in self.pending_messages:
                    self.pending_messages[dst] = []
                self.pending_messages[dst].append(message)

        elif code == "08":  # Confirmação de leitura do cliente
            src = message[2:15]
            dst = message[15:28]
            timestamp = message[28:38]
            # Enviar confirmação de leitura para o originador
            confirmation = f"09{dst}{src}{timestamp}"
            if src in self.clients and self.clients[src][0]:
                self.clients[src][0].sendall(confirmation.encode('utf-8'))

        elif code == "10":  # Criar grupo
            creator = message[2:15]
            timestamp = message[15:25]
            members = [message[i:i+13] for i in range(25, len(message), 13)]  # Ler IDs dos membros
            group_id = self.generate_group_id()
            self.groups[group_id] = members + [creator]

            # Notificar membros do grupo
            group_notification = f"11{group_id}{timestamp}{''.join(self.groups[group_id])}"
            for member in self.groups[group_id]:
                if member in self.clients:
                    self.clients[member][0].sendall(group_notification.encode('utf-8'))
            
            # Retornar o ID do grupo para o criador
            group_creation_confirmation = f"12{group_id}"
            connection.sendall(group_creation_confirmation.encode('utf-8'))

    def deliver_pending_messages(self, client_id):
        print(f"Tentando entregar mensagens pendentes para o cliente {client_id}...")  # Adicionado
        if client_id in self.pending_messages:
            print(f"Mensagens pendentes encontradas para o cliente {client_id}.")  # Adicionado
            for message in self.pending_messages[client_id]:
                self.clients[client_id][0].sendall(message.encode('utf-8'))
            del self.pending_messages[client_id]
        else:
            print(f"Nenhuma mensagem pendente encontrada para o cliente {client_id}.")  # Adicionado

    def save_message(self, src, dst, data):
        file_path = f"chat_history/{src}_{dst}.csv"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([src, dst, data])
    
    def load_chat_history(self, client_id):
        print(f"Carregando histórico de chat para o cliente {client_id}...")
        for file in os.listdir('chat_history'):
            if file.startswith(client_id):
                with open(os.path.join('chat_history', file), 'r') as file:
                    reader = csv.reader(file)
                    for row in reader:
                        if len(row) == 4:  # Verificar se a linha tem o número correto de campos
                            timestamp, src, dst, data = row
                            print(f"Mensagem de {src} para {dst} ({timestamp}): {data}")
    
    def run(self):
        while True:
            connection, address = self.server_socket.accept()
            print(f"Conexão aceita de {address}")
            threading.Thread(target=self.handle_client, args=(connection, address)).start()

if __name__ == "__main__":
    server = ChatServer()
    server.run()