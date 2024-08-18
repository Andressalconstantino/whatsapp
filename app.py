from flask import Flask, render_template, request, jsonify
import socket
import threading
import time

app = Flask(__name__)

# Configurações do servidor de chat
CHAT_SERVER_HOST = 'localhost'
CHAT_SERVER_PORT = 12345

# Armazenar um ID de cliente de exemplo
client_id = '1234567890123'  # Substitua por um ID gerado dinamicamente se necessário

# Função para enviar mensagens ao servidor de chat
def send_message_to_server(message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((CHAT_SERVER_HOST, CHAT_SERVER_PORT))
        client_socket.sendall(message.encode('utf-8'))
        response = client_socket.recv(1024).decode('utf-8')
    return response

# Adicione uma rota para obter o client_id
@app.route('/register', methods=['POST'])
def register_client():
    global client_id
    client_id = str(int(time.time() * 1000)).zfill(13)  # Gerar um ID único
    print(client_id)
    return jsonify({'client_id': client_id})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send', methods=['POST'])
def send_message():
    data = request.json
    dst = data.get('recipient')
    message = data.get('message')
    timestamp = str(int(time.time())).zfill(10)
    formatted_message = f"05{client_id}{dst}{timestamp}{message.ljust(218)}"
    response = send_message_to_server(formatted_message)
    return jsonify({'response': response})

if __name__ == "__main__":
    app.run(debug=True)

