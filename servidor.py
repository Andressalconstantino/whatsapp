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
        self.groups = {}  # Armazenar grupos {group_id: [client_id1, client_id2, ...]}
    
    def generate_client_id(self):
        return str(int(time.time() * 1000)).zfill(13)  # Gerar um ID único com 13 dígitos
    
    def generate_group_id(self):
        return f"G{int(time.time() * 1000)}"  # Gerar um ID único para o grupo
    
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

        elif code == "05":  # Enviar mensagem
            src = message[2:15]
            dst = message[15:28]
            timestamp = message[28:38]
            data = message[38:].strip()

            if dst.startswith("G"):  # Verificar se o destinatário é um grupo
                self.send_message_to_group(src, dst, timestamp, data)
            elif dst in self.clients and self.clients[dst][0]:  # Destinatário é um cliente conectado
                self.clients[dst][0].sendall(message.encode('utf-8'))
                # Confirmar entrega ao originador
                confirmation = f"07{dst}{timestamp}"
                self.clients[src][0].sendall(confirmation.encode('utf-8'))
            else:
                # Armazenar mensagem se o destinatário estiver offline
                if dst not in self.pending_messages:
                    self.pending_messages[dst] = []
                self.pending_messages[dst].append(message)

        elif code == "08":  # Confirmação de leitura
            src = message[2:15]
            timestamp = message[15:25]
            if src in self.clients:
                # Notificar o originador da mensagem sobre a leitura
                for client_id, (conn, _) in self.clients.items():
                    if client_id == src:
                        continue
                    # Verificar se há mensagens pendentes para este cliente
                    for pending_message in self.pending_messages.get(client_id, []):
                        if pending_message.startswith(f"05{src}"):
                            confirmation = f"09{src}{timestamp}"
                            conn.sendall(confirmation.encode('utf-8'))

        elif code == "10":  # Criar grupo
            creator = message[2:15]
            timestamp = message[15:25]
            members = [message[i:i+13] for i in range(25, len(message), 13)]
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

    def send_message_to_group(self, src, group_id, timestamp, data):
        if group_id in self.groups:
            for member in self.groups[group_id]:
                try:
                    if member in self.clients and self.clients[member][0]:  # Membro conectado
                        message = f"05{src}{group_id}{timestamp}{data.ljust(218)}"
                        self.clients[member][0].sendall(message.encode('utf-8'))
                        print(f"Mensagem enviada para {member} no grupo {group_id}.")
                    else:
                        # Armazenar mensagem se o destinatário estiver offline
                        if member not in self.pending_messages:
                            self.pending_messages[member] = []
                        self.pending_messages[member].append(f"05{src}{group_id}{timestamp}{data}")
                        print(f"Mensagem armazenada para {member} no grupo {group_id}.")
                except Exception as e:
                    print(f"Erro ao enviar mensagem para {member} no grupo {group_id}: {e}")





    
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
