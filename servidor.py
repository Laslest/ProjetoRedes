"""Servidor web simples para o chat.

Esse módulo expõe um endpoint WebSocket em ``/ws`` e serve um arquivo
HTML estático em ``/`` (quando `static/index.html` existir).

Observações importantes:
- O código aqui é uma camada WebSocket/HTTP (FastAPI + Uvicorn) pensada
  para uso via navegador. Ele é independente da sua implementação de
  chat via terminal (sockets TCP).
"""

from pathlib import Path
from typing import Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import json

# Endereço e porta onde o servidor HTTP/WebSocket vai escutar.
HOST = "127.0.0.1"
PORT = 8000

# Diretório e arquivo HTML estático (se existir serão servidos em '/').
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"

app = FastAPI(title="Projeto Redes Chat")

# Se existe um diretório `static`, montamos para servir recursos estáticos
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def home():
    """Retorna `index.html` se existir, caso contrário um aviso simples.

    Uso: abre o navegador em `http://<HOST>:<PORT>/`.
    """
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    return HTMLResponse("<h1>Crie o arquivo static/index.html</h1>")


class ConnectionManager:
    """Gerencia conexões WebSocket e envio de mensagens.

    Estrutura interna:
    - ``self._connections``: mapeia instâncias de ``WebSocket`` para nomes
      de usuário (str). Usamos o objeto WebSocket como chave porque é único
      por conexão.

    Métodos principais:
    - ``connect``: aceita a conexão e anuncia a entrada para todos.
    - ``disconnect``: remove a conexão e anuncia a saída.
    - ``broadcast``: envia uma string para todas as conexões ativas.
    """

    def __init__(self) -> None:
        # Mapeia WebSocket -> username
        self._connections: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, username: str) -> None:
        """Aceita a conexão e registra o usuário.

        username pode ser passado (ex: ``/ws?username=Ana``).
        """
        await websocket.accept()
        # Armazena o nome (ou 'Anonimo' se vazio)
        self._connections[websocket] = username or "Anonimo"
        # Anuncia para todos
        await self.broadcast(f"--- {self._connections[websocket]} entrou ---")
        # Envia lista atualizada de usuários para todos
        try:
            await self.broadcast_user_list()
        except Exception:
            pass

    def get_ws_by_username(self, username: str):
        """Obtém o WebSocket a partir do nome do usuário."""
        for ws, name in self._connections.items():
            if name == username:
                return ws
        return None

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a conexão e anuncia a saída."""
        username = self._connections.pop(websocket, "Desconhecido")
        await self.broadcast(f"--- {username} saiu ---")
        # Envia lista atualizada de usuários para todos
        try:
            await self.broadcast_user_list()
        except Exception:
            pass
        # Se não houver mais usuários, reiniciar o tema de todos
        if len(self._connections) == 0:
            try:
                await self.broadcast("THEME reset")
            except Exception:
                pass

    async def broadcast(self, message: str) -> None:
        """Envia message para todas as conexões ativas."""
        for connection in list(self._connections.keys()):
            try:
                await connection.send_text(message)
            except RuntimeError:
                # Remove conexões quebradas de maneira simples
                self._connections.pop(connection, None)

    async def broadcast_user_list(self) -> None:
        """Envia uma mensagem especial com a lista de usuários conectados.

        O formato é: `USUARIOS <json_array>` onde `<json_array>` é uma
        lista JSON com os nomes de usuário ativos.
        """
        users = list(self._connections.values())
        payload = json.dumps(users)
        for connection in list(self._connections.keys()):
            try:
                await connection.send_text(f"USUARIOS {payload}")
            except RuntimeError:
                self._connections.pop(connection, None)


manager = ConnectionManager()

active_games: dict = {}
pending_challenges: dict = {}


def check_winner(board: list) -> str:
    """Retorna 'X' ou 'O' se houver vencedor, ou None caso contrário."""
    wins = (
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6),
    )
    for a, b, c in wins:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return None


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Endpoint WebSocket principal com suporte a jogo da velha."""
    username = websocket.query_params.get("username", "Anonimo").strip() or "Anonimo"
    await manager.connect(websocket, username)
    try:
        while True:
            data = await websocket.receive_text()
            mensagem = data.strip()

            # /desafiar <nome>
            if mensagem.startswith("/desafiar "):
                alvo = mensagem.split(maxsplit=1)[1].strip()
                if alvo == username:
                    await websocket.send_text("SISTEMA: você não pode desafiar a si mesmo!")
                    continue
                ws_alvo = manager.get_ws_by_username(alvo)
                if not ws_alvo:
                    await websocket.send_text("SISTEMA: usuário não encontrado")
                else:
                    pending_challenges[alvo] = username
                    await ws_alvo.send_text(f"SISTEMA: {username} te desafiou para 'velha'. Digite /aceitar ou /recusar")
                    await websocket.send_text("SISTEMA: desafio enviado")
                continue

            # /aceitar
            if mensagem.startswith("/aceitar"):
                meu_nome = username
                desafiante = pending_challenges.pop(meu_nome, None)
                if not desafiante:
                    await websocket.send_text("SISTEMA: nenhum desafio pendente")
                else:
                    key = tuple(sorted([meu_nome, desafiante]))
                    active_games[key] = {"board": [""]*9, "turn": desafiante, "symbols": {desafiante:"X", meu_nome:"O"}}
                    await websocket.send_text(f"GAME_START velha {desafiante} O")
                    ws_desafiante = manager.get_ws_by_username(desafiante)
                    if ws_desafiante:
                        await ws_desafiante.send_text(f"GAME_START velha {meu_nome} X")
                    for player in key:
                        ws_player = manager.get_ws_by_username(player)
                        if ws_player:
                            await ws_player.send_text(f"SISTEMA: vez de {desafiante}")
                continue

            # /jogada r c
            if mensagem.startswith("/jogada "):
                parts = mensagem.split()
                if len(parts) < 3:
                    await websocket.send_text("SISTEMA: uso correto /jogada r c")
                    continue
                try:
                    r = int(parts[1])
                    c = int(parts[2])
                except ValueError:
                    await websocket.send_text("SISTEMA: coordenadas inválidas")
                    continue

                if not (0 <= r <= 2 and 0 <= c <= 2):
                    await websocket.send_text("SISTEMA: coordenadas fora do intervalo 0..2")
                    continue

                meu = username
                for key, game in list(active_games.items()):
                    if meu in key:
                        if game["turn"] != meu:
                            await websocket.send_text("SISTEMA: não é sua vez")
                            break

                        pos = r * 3 + c
                        if pos < 0 or pos >= 9:
                            await websocket.send_text("SISTEMA: posição inválida")
                            break

                        if game["board"][pos]:
                            await websocket.send_text("SISTEMA: posição ocupada")
                            break

                        game["board"][pos] = game["symbols"][meu]

                        for player in key:
                            ws = manager.get_ws_by_username(player)
                            if ws:
                                await ws.send_text(f"GAME_MOVE {r} {c} {meu}")

                        winner_symbol = check_winner(game["board"])
                        if winner_symbol:
                            winner_name = None
                            for p, s in game["symbols"].items():
                                if s == winner_symbol:
                                    winner_name = p
                                    break
                            for player in key:
                                ws = manager.get_ws_by_username(player)
                                if ws:
                                    await ws.send_text(f"GAME_END {winner_name}")
                            active_games.pop(key, None)
                            break

                        if all(cell for cell in game["board"]):
                            for player in key:
                                ws = manager.get_ws_by_username(player)
                                if ws:
                                    await ws.send_text("GAME_END empate")
                            active_games.pop(key, None)
                            break

                        jogador_outro = key[0] if key[1] == meu else key[1]
                        game["turn"] = jogador_outro
                        for player in key:
                            ws_player = manager.get_ws_by_username(player)
                            if ws_player:
                                await ws_player.send_text(f"SISTEMA: vez de {jogador_outro}")
                        break
                continue

            if mensagem:
                await manager.broadcast(f"{username}: {mensagem}")
                # Resposta automática quando alguém digita exatamente "flamengo" (case-insensitive)
                try:
                    if mensagem.strip().lower() == 'flamengo':
                        await manager.broadcast("Maior Clube do Planeta Terra. VAMOS FLAMENGO!!!")
                        # Informa clientes para trocar o tema
                        await manager.broadcast("THEME flamengo")
                except Exception:
                    # Não queremos que um erro no auto-reply derrube a conexão
                    pass
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)


def main() -> None:
    """Inicializa o servidor usando Uvicorn.

    Use `python servidor.py` para rodar localmente em `HOST:PORT`.
    """
    uvicorn.run("servidor:app", host=HOST, port=PORT, reload=False)


if __name__ == "__main__":
    main()