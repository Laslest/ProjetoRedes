import socket
import threading
import os

# Configurações
HOST = '127.0.0.1'
PORT = 5001

# Lista de conexões: armazena tuplas (socket, endereco, username)
conexoes = []
lock = threading.Lock()

def broadcast(mensagem, remetente_sock=None):
    """Envia mensagem para todos, exceto (opcionalmente) o remetente."""
    with lock:
        for conn, addr, username in conexoes:
            if conn != remetente_sock:
                try:
                    conn.send(mensagem.encode())
                except:
                    # Se der erro ao enviar, removemos o cliente na thread dele
                    pass

def lidar_com_cliente(conn, addr):
    """Lógica de controle de cada cliente conectado."""
    print(f"[NOVA CONEXÃO] {addr} conectado.")
    username = "Desconhecido"

    try:
        # 1. Recebe o username
        username = conn.recv(1024).decode()
        
        # Atualiza o username na lista de conexões
        with lock:
            for i, (c, a, u) in enumerate(conexoes):
                if c == conn:
                    conexoes[i] = (conn, addr, username)
                    break
        
        msg_entrada = f"--- {username} entrou na sala. ---"
        print(msg_entrada)
        broadcast(msg_entrada)

        # 2. Loop principal de mensagens
        while True:
            data = conn.recv(1024)
            if not data:
                break
            
            msg_texto = data.decode()
            
            # Formata a mensagem
            mensagem_final = f"{username}: {msg_texto}"
            print(f"[CLIENTE] {mensagem_final}") # Apenas log no servidor
            
            # Envia para todos (exceto quem enviou)
            broadcast(mensagem_final, remetente_sock=conn)

    except Exception as e:
        print(f"[ERRO] {addr}: {e}")
    finally:
        # Remoção segura
        with lock:
            conexoes[:] = [tup for tup in conexoes if tup[0] != conn]
        
        conn.close()
        msg_saida = f"--- {username} saiu da sala. ---"
        print(msg_saida)
        broadcast(msg_saida)

def iniciar_servidor():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((HOST, PORT))
        server.listen()
        print(f"Servidor rodando em {HOST}:{PORT}")
        print("Aguardando conexões...")

        while True:
            conn, addr = server.accept()
            
            with lock:
                conexoes.append((conn, addr, None)) # Username None inicialmente
            
            thread = threading.Thread(target=lidar_com_cliente, args=(conn, addr))
            thread.daemon = True
            thread.start()

    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    finally:
        server.close()
        os._exit(0)

if __name__ == '__main__':
    iniciar_servidor()