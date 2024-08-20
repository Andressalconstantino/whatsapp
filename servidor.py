import socket
import threading
import time
import csv
import os

class ServidorChat:
    def __init__(self, host='localhost', port=12345):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        print(f"Servidor iniciado em {host}:{port}")
        
        self.clientes = {}  #armazenar clientes
        self.mensagensPendentes = {}  #mensagens pendentes
        self.grupos = {}  #armazenar grupos
    
    def gera_grupoId(self):
        return f"G{str(int(time.time() * 1000)).zfill(12)}"  #gerar um ID para o grupo

    def gera_cliente_id(self):
        return str(int(time.time() * 1000)).zfill(13)  #gerar um ID para o usuário
    
    def gerenciaCliente(self, conexao, endereco):
        cliente_id = None
        try:
            while True:
                dados = conexao.recv(1024).decode('utf-8')
                if not dados:
                    break
                print(f"Recebido de {endereco}: {dados}")
                if cliente_id is None and dados.startswith("03"):
                    cliente_id = dados[2:15]
                    self.carregaHistoricoChat(cliente_id)
                self.processa_mensagem(conexao, dados)
        except ConnectionResetError:
            print(f"Conexão com {endereco} perdida.")
        finally:
            if cliente_id and cliente_id in self.clientes:
                self.clientes.pop(cliente_id, None)
                self.mensagensPendentes.pop(cliente_id, None)
            conexao.close()
    
    def processa_mensagem(self, conexao, mensagem):
        codigo = mensagem[:2]
        if codigo == "01":  #registrar cliente
            cliente_id = self.gera_cliente_id()
            self.clientes[cliente_id] = (conexao, None)
            resposta = f"02{cliente_id}"
            conexao.sendall(resposta.encode('utf-8'))

        elif codigo == "03":  #conectar cliente
            cliente_id = mensagem[2:15]
            print(f"Tentando conectar o cliente {cliente_id}...")
            if cliente_id in self.clientes:
                self.clientes[cliente_id] = (conexao, None)
                self.envia_mensagensPendentes(cliente_id)
            else:
                print(f"Cliente {cliente_id} não encontrado.")

        elif codigo == "05":  #enviar mensagem
            remetente = mensagem[2:15]
            destinatario = mensagem[15:28]
            horario = mensagem[28:38]
            dados = mensagem[38:].strip()

            if destinatario in self.clientes and self.clientes[destinatario][0]:  # Destinatário é um cliente conectado
                self.clientes[destinatario][0].sendall(mensagem.encode('utf-8'))
                #confirmar entrega ao remetente
                confirmacao = f"07{destinatario}{horario}"
                self.clientes[remetente][0].sendall(confirmacao.encode('utf-8'))
                #salvar mensagem no histórico
                self.save_mensagem(remetente, destinatario, dados)
            else:
                #armazenar mensagem se o destinatário estiver offline
                if destinatario not in self.mensagensPendentes:
                    self.mensagensPendentes[destinatario] = []
                self.mensagensPendentes[destinatario].append(mensagem)

        elif codigo == "08":  #confirmação de leitura do cliente
            remetente = mensagem[2:15]
            destinatario = mensagem[15:28]
            horario = mensagem[28:38]
            #enviar confirmação de leitura para o remetente
            confirmacao = f"09{destinatario}{remetente}{horario}"
            if remetente in self.clientes and self.clientes[remetente][0]:
                self.clientes[remetente][0].sendall(confirmacao.encode('utf-8'))

        elif codigo == "10":  #criar grupo
            criador = mensagem[2:15]
            horario = mensagem[15:25]
            membros = [mensagem[i:i+13].strip() for i in range(25, len(mensagem), 13)]
            grupoId = self.gera_grupoId()
            self.grupos[grupoId] = list(set(membros + [criador]))  #adiciona o criador ao grupo e remove duplicatas

            #notificar membros do grupo
            notificaGrupo = f"11{grupoId}{horario}{''.join(self.grupos[grupoId])}"
            for membro in self.grupos[grupoId]:
                if membro in self.clientes:
                    self.clientes[membro][0].sendall(notificaGrupo.encode('utf-8'))

            #retornar o ID do grupo para o criador
            grupo_criado_confirmacao = f"12{grupoId}"
            conexao.sendall(grupo_criado_confirmacao.encode('utf-8'))

    def envia_mensagensPendentes(self, cliente_id):
        print(f"Tentando entregar mensagens pendentes para o cliente {cliente_id}...")
        if cliente_id in self.mensagensPendentes:
            print(f"Mensagens pendentes encontradas para o cliente {cliente_id}.")
            for mensagem in self.mensagensPendentes[cliente_id]:
                self.clientes[cliente_id][0].sendall(mensagem.encode('utf-8'))
            del self.mensagensPendentes[cliente_id]
        else:
            print(f"Nenhuma mensagem pendente encontrada para o cliente {cliente_id}.")
    
    def save_mensagem(self, remetente, destinatario, dados):
        horario = str(int(time.time()))
        caminhoArq = f"chat_history/{remetente}_{destinatario}.csv"
        os.makedirs(os.path.dirname(caminhoArq), exist_ok=True)
        with open(caminhoArq, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([horario, remetente, destinatario, dados])
    
    def carregaHistoricoChat(self, cliente_id):
        print(f"Carregando histórico de chat para o cliente {cliente_id}...")
        for file in os.listdir('chat_history'):
            if file.startswith(cliente_id):
                with open(os.path.join('chat_history', file), 'r') as file:
                    reader = csv.reader(file)
                    for row in reader:
                        if len(row) == 4:  #verificar se a linha tem o número correto de campos
                            horario, remetente, destinatario, dados = row
                            print(f"Mensagem de {remetente} para {destinatario} ({horario}): {dados}")
    
    def run(self):
        while True:
            conexao, endereco = self.server_socket.accept()
            print(f"Conexão aceita de {endereco}")
            threading.Thread(target=self.gerenciaCliente, args=(conexao, endereco)).start()

if __name__ == "__main__":
    servidor = ServidorChat()
    servidor.run()