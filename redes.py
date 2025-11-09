from socket import *
import threading
import time
import os

meuHost = '127.0.0.1'
minhaPorta = 5001

conexoes = []

def auxiliar(conn, cliente):
    print('Assistente cuidando de:', cliente)
    try:
        while True:
            recvMsg = conn.recv(1024)

            if recvMsg == b'\x18' or not recvMsg:
                print(f'Cliente {cliente} desconectou.')
                break 

            print(f'[Servidor] {cliente}: {recvMsg.decode()}')

            for conexao in conexoes:
                if conexao != conn: 
                    try:
                        conexao.send(recvMsg)
                    except Exception as e:
                        print(f"Erro no broadcast para {conexao}: {e}")

    finally:
        print('Finalizando conexão do cliente', cliente)
        if conn in conexoes:
            conexoes.remove(conn) 
        conn.close() 


def servidor():
    sockobj = socket(AF_INET, SOCK_STREAM)
    orig = (meuHost, minhaPorta)
    try:
        sockobj.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sockobj.bind(orig)
        sockobj.listen(5)
        print("Servidor escutando...")

        while True:
            conn, cliente = sockobj.accept()
            
            conexoes.append(conn)
            print('Conectado por:', cliente)

            client_thread = threading.Thread(target=auxiliar, args=(conn, cliente))
            client_thread.daemon = True
            client_thread.start()

    except Exception as e:
        print('Servidor erro:', e)
    finally:
        sockobj.close()

def receber_mensagens(sock):
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                print("\n[Conexão com o servidor perdida]")
                break
            
            print(f"\n{data.decode()}")

        except Exception as e:
            print(f"\n[Saindo da thread de recebimento... {e}]")
            break
    
    os._exit(0) 


def cliente():
    sockobj = socket(AF_INET, SOCK_STREAM)
    dest = (meuHost, minhaPorta)
    
    try:
        sockobj.connect(dest)
    except Exception as e:
        print(f"Não foi possível conectar ao servidor: {e}")
        print("Verifique se o Terminal 1 (servidor) está rodando.")
        return

    print('Conectado! Para sair use CTRL+X e tecle Enter.\n')

    thread_receber = threading.Thread(target=receber_mensagens, args=(sockobj,), daemon=True)
    thread_receber.start()

    try:
        while True:
            msg = input()
            
            if msg == '\x18':
                sockobj.send(msg.encode())
                break  

            sockobj.send(msg.encode())

    except (EOFError, KeyboardInterrupt):
        print("\nSaindo...")
        sockobj.send(b'\x18') 
    finally:
        sockobj.close()  

if __name__ == '__main__':
    servidor_thread = threading.Thread(target=servidor)
    servidor_thread.daemon = True
    servidor_thread.start()

    time.sleep(1)

    cliente()