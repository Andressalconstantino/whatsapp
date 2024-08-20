import socket
import time
import threading
import pickle

class ClienteChat:
    def __init__(self, host='localhost', port=12345):
        self.cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cliente_socket.connect((host, port))
        self.cliente_id = None
        self.carregaEstadoCliente()
    
    def salvaEstadoCliente(self):
        state = {
            'cliente_id': self.cliente_id,
            'contatos': self.contatos,
            'grupos': self.grupos
        }
        with open('cliente_state.pkl', 'wb') as f:
            pickle.dump(state, f)
    
    def carregaEstadoCliente(self):
        try:
            with open('cliente_state.pkl', 'rb') as f:
                state = pickle.load(f)
                self.cliente_id = state.get('cliente_id')
                self.contatos = state.get('contatos', {})
                self.grupos = state.get('grupos', {})
        except FileNotFoundError:
            self.contatos = {}
            self.grupos = {}
    
    def registrar(self):
        cliente_id = input("Por favor, insira seu ID de cliente de 13 dígitos ou pressione Enter para gerar um automaticamente: ").strip()
        if len(cliente_id) != 13:
            print("ID de cliente inválido. Gerando um automaticamente...")
            mensagem = "01"  #registrar cliente
        else:
            mensagem = f"03{cliente_id}"  #conectar cliente
        self.cliente_socket.sendall(mensagem.encode('utf-8'))
        resposta = self.cliente_socket.recv(1024).decode('utf-8')
        if resposta.startswith("02"):
            self.cliente_id = resposta[2:15]
            print(f"Registrado com ID: {self.cliente_id}")
    
    def receberMensagens(self):
        while True:
            try:
                mensagem = self.cliente_socket.recv(1024).decode('utf-8')
                if not mensagem:
                    break
                codigo = mensagem[:2]
                if codigo == "05":  #recebendo uma mensagem
                    remetente = mensagem[2:15]
                    destinatario = mensagem[15:28]
                    dados = mensagem[38:].strip()
                    print(f"Mensagem de {remetente} para {destinatario}: {dados}")
                    #confirmação de leitura
                    self.confirmacaoLeitura(remetente, mensagem[28:38])
                elif codigo == "07":  #confirmação de entrega
                    destinatario = mensagem[2:15]
                    horario = mensagem[15:25]
                    print(f"Mensagens entregues para {destinatario} até {horario}.")
                elif codigo == "09":  #confirmação de leitura
                    remetente = mensagem[2:15]
                    destinatario = mensagem[15:28]
                    horario = mensagem[28:38]
                    print(f"Mensagens enviadas para {destinatario} lidas por {remetente} até {horario}.")
                elif codigo == "11":  #grupo criado
                    grupoId = mensagem[2:16]
                    horario = mensagem[16:26]
                    membros = [mensagem[i:i+13].strip() for i in range(26, len(mensagem), 13)]
                    self.grupos[grupoId] = membros
                    print(f"Grupo criado: ID {grupoId}, membros: {membros}")
                    self.salvaEstadoCliente()
            except ConnectionResetError:
                print("Conexão perdida com o servidor.")
                break
    
    def confirmacaoLeitura(self, remetente, horario):
        mensagem = f"08{remetente}{self.cliente_id}{horario}"
        self.cliente_socket.sendall(mensagem.encode('utf-8'))

    def obterMembros(self, grupoId):#obtem ids dos integrantes do grupo
        return self.grupos.get(grupoId, [])
    
    def enviarMensagens(self, destinatario, dados):
        horario = str(int(time.time()))
        dados = dados.ljust(218)
        if destinatario.startswith("G"):
            #mensagem para o grupo
            membros = self.obterMembros(destinatario)
            for membro in membros:
                mensagem = f"05{self.cliente_id}{membro}{horario}{dados}"
                self.cliente_socket.sendall(mensagem.encode('utf-8'))
        else:
            #mensagem para um usuário
            mensagem = f"05{self.cliente_id}{destinatario}{horario}{dados}"
            self.cliente_socket.sendall(mensagem.encode('utf-8'))
    
    def criarGrupo(self, membros):
        horario = str(int(time.time()))
        membros_str = ''.join([membro_id.ljust(13) for membro_id in membros])
        mensagem = f"10{self.cliente_id}{horario}{membros_str}"
        self.cliente_socket.sendall(mensagem.encode('utf-8'))

    def run(self):
        self.registrar()
        threading.Thread(target=self.receberMensagens).start()
        
        while True:
            try:
                comando = input("Digite 'msg <destinatário> <mensagem>' para enviar uma mensagem, 'grupo <membros>' para criar um grupo, ou 'exit' para sair: \n").strip()
                
                if comando.startswith("msg "):
                    partes = comando.split(maxsplit=2)
                    if len(partes) == 3:
                        _, destinatario, dados = partes
                        self.enviarMensagens(destinatario, dados)
                    else:
                        print("Formato inválido. Use: msg <destinatário> <mensagem>")
                
                elif comando.startswith("grupo "):
                    membros = comando[6:].strip().split()
                    if membros:
                        self.criarGrupo(membros)
                    else:
                        print("Formato inválido. Use: grupo <membro1> <membro2> ...")

                elif comando == "exit":
                    print("Saindo...")
                    self.cliente_socket.close()  # Fechar o socket
                    break
                
                else:
                    print("Comando desconhecido. Use 'msg', 'grupo', ou 'exit'.")
            
            except Exception as e:
                print(f"Erro ao processar comando: {e}")

if __name__ == "__main__":
    client = ClienteChat()
    client.run()