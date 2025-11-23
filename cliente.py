import curses
import threading
import socket
import time

HOST = "127.0.0.1"
PORT = 5001

def thread_receber(sock, win_chat, lock):
    """Recebe mensagens do servidor e atualiza a tela."""
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                with lock:
                    win_chat.addstr("\n[Desconectado do servidor]\n", curses.A_BOLD)
                    win_chat.refresh()
                break

            msg = data.decode()
            with lock:
                win_chat.addstr(msg + "\n")
                win_chat.refresh()
        except:
            break

def main(stdscr):
    # Configuração para aceitar cores e teclas especiais
    curses.curs_set(1)
    # stdscr.encoding = 'utf-8' # Força codificação se necessário em alguns terminais
    
    altura, largura = stdscr.getmaxyx()

    win_chat = curses.newwin(altura - 3, largura, 0, 0)
    win_input = curses.newwin(3, largura, altura - 3, 0)
    
    win_chat.scrollok(True)
    win_input.scrollok(False)
    
    # Habilita o teclado numérico e setas
    win_input.keypad(True) 

    # Conexão
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
    except:
        stdscr.addstr(0, 0, f"Erro: Não foi possível conectar a {HOST}:{PORT}")
        stdscr.refresh()
        time.sleep(3)
        return

    # Username
    stdscr.clear()
    stdscr.addstr(0, 0, "Seu Username: ")
    curses.echo()
    # getstr pode ter problemas com acentos dependendo do terminal, 
    # mas para o username inicial vamos manter simples.
    username_bytes = stdscr.getstr(0, 14) 
    username = username_bytes.decode('utf-8', errors='ignore').strip()
    curses.noecho()
    
    if not username: 
        username = "Anônimo"
    
    sock.send(username.encode())

    # Inicia thread de escuta
    lock = threading.Lock()
    t = threading.Thread(target=thread_receber, args=(sock, win_chat, lock), daemon=True)
    t.start()

    texto = ""

    # Loop de Input
    while True:
        win_input.erase()
        win_input.addstr(1, 1, "> " + texto)
        win_input.refresh()

        try:
            # MUDANÇA PRINCIPAL AQUI: get_wch() em vez de getch()
            # get_wch retorna um inteiro (para teclas especiais) 
            # OU uma string (para caracteres normais e acentuados)
            key = win_input.get_wch()
        except:
            continue

        # Tratamento da tecla
        codigo_tecla = None
        
        # Se for string (letras, acentos, números)
        if isinstance(key, str):
            codigo_tecla = ord(key) # Converte para número para checar Enter/Esc
            
            # Se for Enter (geralmente '\n' ou '\r')
            if codigo_tecla in (10, 13):
                msg_envio = texto.strip()
                if msg_envio:
                    sock.send(msg_envio.encode())
                    with lock:
                        win_chat.addstr(f"{username}: {msg_envio}\n")
                        win_chat.refresh()
                texto = ""
            
            # Se for Backspace (às vezes vem como string '\x7f')
            elif codigo_tecla == 127:
                 texto = texto[:-1]
                 
            # Caractere normal (adiciona ao texto)
            elif codigo_tecla >= 32:
                if len(texto) < largura - 5:
                    texto += key

        # Se for Inteiro (Teclas especiais como KEY_BACKSPACE, setas, etc)
        elif isinstance(key, int):
            if key == curses.KEY_BACKSPACE:
                texto = texto[:-1]
            elif key == 27: # ESC
                break
            # Ignora outras teclas especiais (setas, F1, etc) para não quebrar o texto

    sock.close()

if __name__ == "__main__":
    # Garante suporte a locale (acentos do sistema)
    import locale
    locale.setlocale(locale.LC_ALL, '') 
    
    curses.wrapper(main)