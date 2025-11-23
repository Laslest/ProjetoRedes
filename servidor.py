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

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a conexão e anuncia a saída."""
        username = self._connections.pop(websocket, "Desconhecido")
        await self.broadcast(f"--- {username} saiu ---")

    async def broadcast(self, message: str) -> None:
        """Envia message para todas as conexões ativas."""
        for connection in list(self._connections.keys()):
            try:
                await connection.send_text(message)
            except RuntimeError:
                # Remove conexões quebradas de maneira simples
                self._connections.pop(connection, None)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Endpoint WebSocket principal.

    Fluxo resumido:
    - Lê `username` da query string (se fornecido) e chama ``manager.connect``.
    - Em loop, recebe mensagens de texto do cliente e rebroadcast para todos
      com o formato "<username>: <mensagem>".
    """
    # Padrão: 'Anonimo' quando não passa o parâmetro username
    username = websocket.query_params.get("username", "Anonimo").strip() or "Anonimo"
    await manager.connect(websocket, username)
    try:
        while True:
            # await receive_text aguarda até o cliente enviar texto
            data = await websocket.receive_text()
            mensagem = data.strip()
            if mensagem:
                # Reenvia para todos no formato 'nome: mensagem'
                await manager.broadcast(f"{username}: {mensagem}")
    except WebSocketDisconnect:
        # Cliente desconectou normalmente
        await manager.disconnect(websocket)
    except Exception:
        # Para qualquer outro erro, garantir remoção limpa
        await manager.disconnect(websocket)


def main() -> None:
    """Inicializa o servidor usando Uvicorn.

    Use `python servidor.py` para rodar localmente em `HOST:PORT`.
    """
    uvicorn.run("servidor:app", host=HOST, port=PORT, reload=False)


if __name__ == "__main__":
    main()