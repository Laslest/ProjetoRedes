import curses
import threading
import time
from websocket import create_connection, WebSocketException

HOST = "127.0.0.1"
PORT = 5001
WS_PORT = 8000


class WebSocketAdapter:
    """Adapter mínimo para expor `recv(bufsize)`/`send(bytes)` sobre websocket-client.

    A implementação devolve bytes para `recv` (compatível com `sock.recv` usado no código)
    e aceita strings/bytes em `send`.
    """
    def __init__(self, ws):
        self.ws = ws

    def recv(self, bufsize=1024):
        try:
            msg = self.ws.recv()
        except WebSocketException:
            return b""
        if msg is None:
            return b""
        if isinstance(msg, bytes):
            return msg
        return msg.encode('utf-8')

    def send(self, data):
        try:
            if isinstance(data, bytes):
                text = data.decode('utf-8', errors='ignore')
            else:
                text = str(data)
            self.ws.send(text)
        except WebSocketException:
            pass

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass

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

            # suportar bytes (socket) ou str (websocket adapter)
            if isinstance(data, bytes):
                msg = data.decode(errors='ignore').strip()
            else:
                # adapter pode retornar str encoded as bytes; normalize
                try:
                    msg = data.decode().strip()
                except Exception:
                    msg = str(data).strip()

            # =====================================================
            #   TRATAMENTO DE MENSAGENS DO JOGO DA VELHA
            # =====================================================

            # Ao iniciar o cliente, estas variáveis ainda não existem.
            # Então criamos atributos na thread se necessário.
            if not hasattr(thread_receber, "jogo_ativo"):
                thread_receber.jogo_ativo = False
                thread_receber.tabuleiro = [""] * 9
                thread_receber.simbolo = None
                thread_receber.oponente = None

            # ------- GAME_START -------
            if msg.startswith("GAME_START"):
                # Formato esperado:
                # GAME_START velha <oponente> <X|O>
                partes = msg.split()
                if len(partes) >= 4:
                    _, _, oponente, simbolo = partes[:4]

                    # valida símbolo
                    if simbolo not in ("X", "O"):
                        with lock:
                            win_chat.addstr("[Aviso] GAME_START com símbolo inválido.\n")
                            win_chat.refresh()
                        # Ainda assim inicializa o jogo, mas sem símbolo definido
                        thread_receber.simbolo = None
                    else:
                        thread_receber.simbolo = simbolo

                    thread_receber.jogo_ativo = True
                    thread_receber.oponente = oponente
                    thread_receber.tabuleiro = [""] * 9

                    with lock:
                        win_chat.clear()
                        win_chat.addstr("=== JOGO DA VELHA INICIADO ===\n")
                        win_chat.addstr(f"Você é: {thread_receber.simbolo or 'desconhecido'}\n")
                        win_chat.addstr(f"Oponente: {oponente}\n")
                        win_chat.addstr("\nAguarde ou faça sua jogada...\n")
                        win_chat.refresh()

                    continue  # não imprime como mensagem normal


            # ------- GAME_MOVE -------
            if msg.startswith("GAME_MOVE"):
                # formato:
                # GAME_MOVE r c jogador
                partes = msg.split()
                if len(partes) >= 4:
                    _, r_s, c_s, jogador = partes[:4]
                    try:
                        r = int(r_s)
                        c = int(c_s)
                    except ValueError:
                        with lock:
                            win_chat.addstr("[Erro] GAME_MOVE com coordenadas inválidas.\n")
                            win_chat.refresh()
                        continue

                    # valida coordenadas (esperamos 0..2)
                    if not (0 <= r <= 2 and 0 <= c <= 2):
                        with lock:
                            win_chat.addstr("[Erro] Coordenadas fora do intervalo (0..2).\n")
                            win_chat.refresh()
                        continue

                    pos = r*3 + c

                    # Atualizamos nosso tabuleiro local:
                    if thread_receber.simbolo is None:
                        with lock:
                            win_chat.addstr("[Aviso] Símbolo do jogador desconhecido; ignorando GAME_MOVE.\n")
                            win_chat.refresh()
                        continue

                    if jogador == thread_receber.oponente:
                        simbolo_jogada = "O" if thread_receber.simbolo == "X" else "X"
                    else:
                        simbolo_jogada = thread_receber.simbolo

                    # protege contra pos inválido (por segurança)
                    if pos < 0 or pos >= len(thread_receber.tabuleiro):
                        with lock:
                            win_chat.addstr("[Erro] Posição calculada inválida.\n")
                            win_chat.refresh()
                        continue

                    thread_receber.tabuleiro[pos] = simbolo_jogada

                    # redesenha o jogo
                    with lock:
                        win_chat.clear()
                        win_chat.addstr("=== JOGO DA VELHA ===\n\n")

                        t = thread_receber.tabuleiro
                        win_chat.addstr(f" {t[0] or '-'} | {t[1] or '-'} | {t[2] or '-'}\n")
                        win_chat.addstr("---+---+---\n")
                        win_chat.addstr(f" {t[3] or '-'} | {t[4] or '-'} | {t[5] or '-'}\n")
                        win_chat.addstr("---+---+---\n")
                        win_chat.addstr(f" {t[6] or '-'} | {t[7] or '-'} | {t[8] or '-'}\n\n")

                        win_chat.addstr("Digite sua jogada: /jogada r c\n")
                        win_chat.refresh()

                    continue  # impede cair no chat normal


            # ------- GAME_END -------
            if msg.startswith("GAME_END"):
                # formato:
                # GAME_END vencedor
                vencedor = msg.split(maxsplit=1)[1] if " " in msg else "desconhecido"

                with lock:
                    win_chat.addstr("\n=== FIM DO JOGO ===\n", curses.A_BOLD)
                    if vencedor == "empate":
                        win_chat.addstr("Resultado: EMPATE!\n\n")
                    else:
                        win_chat.addstr(f"Vencedor: {vencedor}\n\n")
                    win_chat.addstr("Voltando ao chat...\n")
                    win_chat.refresh()

                # reset do estado local
                thread_receber.jogo_ativo = False
                thread_receber.tabuleiro = [""] * 9
                thread_receber.oponente = None
                thread_receber.simbolo = None

                continue  # não mostra como mensagem normal no chat


            # =====================================================
            #   CASO NÃO SEJA MENSAGEM DO JOGO, EXIBE NORMAL
            # =====================================================
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

    # Username (pedimos antes de conectar para usar query param no WebSocket)
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

    # Conexão via WebSocket (servidor usa FastAPI / Uvicorn em WS_PORT)
    try:
        ws_url = f"ws://{HOST}:{WS_PORT}/ws?username={username}"
        ws = create_connection(ws_url)
        sock = WebSocketAdapter(ws)
    except Exception:
        stdscr.addstr(0, 0, f"Erro: Não foi possível conectar a {HOST}:{WS_PORT} via WebSocket")
        stdscr.refresh()
        time.sleep(3)
        return

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
                    sock.send(msg_envio)
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