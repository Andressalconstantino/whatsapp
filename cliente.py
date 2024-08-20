import socket
import time
import threading
import pickle  # Para persistência simples

class ChatClient:
    def __init__(self, host='localhost', port=12345):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host, port))
        self.client_id = None
        self.load_state()
    
    def save_state(self):
        state = {
            'client_id': self.client_id,
            'contacts': self.contacts,
            'groups': self.groups
        }
        with open('client_state.pkl', 'wb') as f:
            pickle.dump(state, f)
    
    def load_state(self):
        try:
            with open('client_state.pkl', 'rb') as f:
                state = pickle.load(f)
                self.client_id = state.get('client_id')
                self.contacts = state.get('contacts', {})
                self.groups = state.get('groups', {})
        except FileNotFoundError:
            self.contacts = {}
            self.groups = {}
    
    def register(self):
        client_id = input("Por favor, insira seu ID de cliente de 13 dígitos ou pressione Enter para gerar um automaticamente: ").strip()
        if len(client_id) != 13:
            print("ID de cliente inválido. Gerando um automaticamente...")
            message = "01"  # Código para registrar cliente
        else:
            message = f"03{client_id}"  # Código para conectar cliente
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
                    dst = message[15:28]
                    data = message[38:].strip()
                    print(f"Mensagem de {src} para {dst}: {data}")
                    # Enviar confirmação de leitura
                    self.send_read_confirmation(src, message[28:38])
                elif code == "07":  # Confirmação de entrega
                    dst = message[2:15]
                    timestamp = message[15:25]
                    print(f"Mensagens entregues para {dst} até {timestamp}.")
                elif code == "09":  # Confirmação de leitura
                    src = message[2:15]
                    dst = message[15:28]
                    timestamp = message[28:38]
                    print(f"Mensagens enviadas para {dst} lidas por {src} até {timestamp}.")
                elif code == "11":  # Grupo criado
                    group_id = message[2:16]
                    timestamp = message[16:26]
                    members = [message[i:i+13].strip() for i in range(26, len(message), 13)]
                    self.groups[group_id] = members
                    print(f"Grupo criado: ID {group_id}, membros: {members}")
                    # Salvar estado após a criação do grupo
                    self.save_state()
            except ConnectionResetError:
                print("Conexão perdida com o servidor.")
                break
    
    def send_read_confirmation(self, src, timestamp):
        message = f"08{src}{self.client_id}{timestamp}"
        self.client_socket.sendall(message.encode('utf-8'))

    def get_members(self, group_id):
        """Retorna a lista de IDs dos membros de um grupo."""
        return self.groups.get(group_id, [])
    
    def send_message(self, dst, data):
        timestamp = str(int(time.time()))
        data = data.ljust(218)
        if dst.startswith("G"):
            # Mensagem para o grupo
            members = self.get_members(dst)
            for member in members:
                message = f"05{self.client_id}{member}{timestamp}{data}"
                self.client_socket.sendall(message.encode('utf-8'))
        else:
            # Mensagem direta
            message = f"05{self.client_id}{dst}{timestamp}{data}"
            self.client_socket.sendall(message.encode('utf-8'))
    
    def create_group(self, members):
        timestamp = str(int(time.time()))
        members_str = ''.join([member_id.ljust(13) for member_id in members])
        message = f"10{self.client_id}{timestamp}{members_str}"
        self.client_socket.sendall(message.encode('utf-8'))

    def run(self):
        self.register()
        threading.Thread(target=self.listen_for_messages).start()
        
        while True:
            try:
                command = input("Digite 'msg <destinatário> <mensagem>' para enviar uma mensagem, 'group <membros>' para criar um grupo, ou 'exit' para sair: \n").strip()
                
                if command.startswith("msg "):
                    parts = command.split(maxsplit=2)
                    if len(parts) == 3:
                        _, dst, data = parts
                        self.send_message(dst, data)
                    else:
                        print("Formato inválido. Use: msg <destinatário> <mensagem>")
                
                elif command.startswith("group "):
                    members = command[6:].strip().split()
                    if members:
                        self.create_group(members)
                    else:
                        print("Formato inválido. Use: group <membro1> <membro2> ...")

                elif command == "exit":
                    print("Saindo...")
                    self.client_socket.close()  # Fechar o socket
                    break
                
                else:
                    print("Comando desconhecido. Use 'msg', 'group', ou 'exit'.")
            
            except Exception as e:
                print(f"Erro ao processar comando: {e}")

if __name__ == "__main__":
    client = ChatClient()
    client.run()
