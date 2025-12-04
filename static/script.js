(() => {
			const statusEl = document.getElementById('status');
			const logEl = document.getElementById('chat-log');
			const formEl = document.getElementById('message-form');
			const inputEl = document.getElementById('message-input');
			const submitBtn = formEl.querySelector('button');
			const btnAccept = document.getElementById('btn-accept');
			const usernameDialog = document.getElementById('username-dialog');
			const usernameForm = document.getElementById('username-form');
			const usernameInput = document.getElementById('username-input');

			const chatScreen = document.getElementById('chat-screen');
			const gameScreen = document.getElementById('game-screen');
			const gameTitle = document.getElementById('game-title');
			const gameStatus = document.getElementById('game-status');
			const gameBoard = document.getElementById('game-board');
			const btnQuitGame = document.getElementById('btn-quit-game');

			const clubSymbolEl = document.getElementById('club-symbol');

			let socket = null;
			let username = '';
			let gameActive = false;
			let opponent = '';
			let mySymbol = '';
			let myTurn = false;
			let board = Array(9).fill('');

			const userListEl = document.getElementById('user-items');

			const appendMessage = (text, type = 'message') => {
				const div = document.createElement('div');
				div.className = type;
				div.textContent = text;
				logEl.appendChild(div);
				// Mantém a rolagem no próprio container do chat
				try {
					div.scrollIntoView({ behavior: 'auto', block: 'end' });
				} catch (e) {
					logEl.scrollTop = logEl.scrollHeight;
				}
			};

			const setStatus = (text, online) => {
				statusEl.textContent = text;
				statusEl.className = `status ${online ? 'status-online' : 'status-offline'}`;
				inputEl.disabled = !online;
				submitBtn.disabled = !online;
				btnAccept.disabled = !online;
				if (!online) {
					inputEl.value = '';
				} else {
					inputEl.focus();
				}
			};

			const getWsUrl = () => {
				const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
				const defaultHost = '127.0.0.1:8000';
				const host = window.location.host || defaultHost;
				return `${protocol}://${host}/ws?username=${encodeURIComponent(username)}`;
			};

			const showChatScreen = () => {
				gameActive = false;
				chatScreen.style.display = 'flex';
				gameScreen.style.display = 'none';
			};

			const showGameScreen = () => {
				gameActive = true;
				chatScreen.style.display = 'none';
				gameScreen.style.display = 'flex';
				renderBoard();
			};

			const renderBoard = () => {
				gameBoard.innerHTML = '';
				for (let i = 0; i < 9; i++) {
					const cell = document.createElement('div');
					cell.className = 'board-cell';
					const symbol = board[i];
					if (symbol === 'X') cell.classList.add('x');
					else if (symbol === 'O') cell.classList.add('o');
					if (symbol || !myTurn) cell.classList.add('disabled');
					cell.textContent = symbol || '';
					cell.addEventListener('click', () => onCellClick(i));
					gameBoard.appendChild(cell);
				}
			};

			const onCellClick = (index) => {
				if (!socket || socket.readyState !== WebSocket.OPEN) return;
				if (!myTurn || board[index]) return;
				const r = Math.floor(index / 3);
				const c = index % 3;
				socket.send(`/jogada ${r} ${c}`);
			};

			const connect = () => {
				if (!username) return;
				socket = new WebSocket(getWsUrl());

				socket.addEventListener('open', () => {
					setStatus(`Conectado como ${username}`, true);
					appendMessage('Conexão estabelecida!', 'system');
				});

				socket.addEventListener('message', event => {
					const text = event.data;

				// Comandos especiais de controle de cliente
				if (text.startsWith('THEME ')) {
					const name = text.split(' ')[1] || '';
					if (name === 'flamengo') applyTheme('flamengo');
					if (name === 'reset') resetTheme();
					return;
				}					// Mensagem especial enviada pelo servidor com a lista de usuários:
					// "USUARIOS <json_array>"
					if (text.startsWith('USUARIOS ')) {
						try {
							const payload = text.substring('USUARIOS '.length);
							const users = JSON.parse(payload);
							renderUserList(users);
						} catch (e) {
							console.error('Falha ao parsear USUARIOS', e);
						}
						return;
					}

					if (text.startsWith('GAME_START')) {
						// GAME_START velha <oponente> <X|O>
						const parts = text.split(' ');
						if (parts.length >= 4) {
							opponent = parts[2];
							mySymbol = parts[3];
							board = Array(9).fill('');
							myTurn = false;
							gameTitle.textContent = `Você: ${mySymbol} vs ${opponent}: ${mySymbol === 'X' ? 'O' : 'X'}`;
							showGameScreen();
						}
						return;
					}

					if (text.startsWith('GAME_MOVE')) {
						// GAME_MOVE r c jogador
						const parts = text.split(' ');
						if (parts.length >= 4) {
							const r = parseInt(parts[1], 10);
							const c = parseInt(parts[2], 10);
							const jogador = parts[3];
							const pos = r * 3 + c;
							let symbol = mySymbol;
							if (jogador === opponent) symbol = mySymbol === 'X' ? 'O' : 'X';
							board[pos] = symbol;
							renderBoard();
						}
						return;
					}

					if (text.startsWith('GAME_END')) {
						// GAME_END <vencedor|empate>
						const parts = text.split(' ');
						const who = parts[1] || 'desconhecido';
						if (who === 'empate') {
							gameStatus.textContent = 'Resultado: EMPATE!';
						} else {
							gameStatus.textContent = `Vencedor: ${who}`;
						}
						myTurn = false;
						renderBoard();
						setTimeout(() => showChatScreen(), 3000);
						return;
					}

					if (text.startsWith('SISTEMA: vez de ')) {
						// SISTEMA: vez de <nome>
						const playerName = text.substring('SISTEMA: vez de '.length).trim();
						myTurn = playerName === username;
						gameStatus.textContent = myTurn ? 'Sua vez!' : `Vez de ${playerName}`;
						renderBoard();
						return;
					}

					// Mensagens normais de chat
					if (gameActive) return;
					appendMessage(text);
				});

				socket.addEventListener('close', () => {
					setStatus('Desconectado', false);
					appendMessage('Conexão encerrada.', 'system');
					showChatScreen();
					usernameDialog.showModal();
				});

				socket.addEventListener('error', () => {
					appendMessage('Erro na conexão. Tente novamente.', 'system');
				});
			};

			usernameForm.addEventListener('submit', event => {
				event.preventDefault();
				const value = usernameInput.value.trim();
				if (!value) return;
				username = value;
				usernameDialog.close();
				connect();
			});

			function renderUserList(users) {
				userListEl.innerHTML = '';
				users.forEach(u => {
					const li = document.createElement('li');
					const btn = document.createElement('button');
					btn.textContent = u;
					btn.type = 'button';
					if (u === username) btn.classList.add('self');
					btn.addEventListener('click', (e) => {
						showUserMenu(e, u);
					});
					li.appendChild(btn);
					userListEl.appendChild(li);
				});
			}

			function applyTheme(name) {
				if (name === 'flamengo') {
					document.documentElement.classList.add('theme-flamengo');
					// Persistir preferência do usuário
					try { localStorage.setItem('theme', 'flamengo'); } catch (e) {}

					// Tentar carregar imagem do escudo em /static/flamengo.png
					const img = new Image();
					img.onload = () => {
						clubSymbolEl.style.display = 'inline-flex';
						clubSymbolEl.style.backgroundImage = `url('/static/flamengo.png')`;
						clubSymbolEl.style.backgroundSize = 'contain';
						clubSymbolEl.style.backgroundRepeat = 'no-repeat';
						clubSymbolEl.style.backgroundPosition = 'center';
						clubSymbolEl.textContent = '';
						clubSymbolEl.title = 'Tema Flamengo (clique para restaurar)';
						clubSymbolEl.addEventListener('click', resetTheme);
					};
					img.onerror = () => {
						// fallback textual se imagem não estiver presente
						clubSymbolEl.style.display = 'inline-flex';
						clubSymbolEl.textContent = 'CRF';
						clubSymbolEl.style.backgroundImage = '';
						clubSymbolEl.style.color = 'var(--accent)';
						clubSymbolEl.title = 'Tema Flamengo (clique para restaurar)';
						clubSymbolEl.addEventListener('click', resetTheme);
					};
					img.src = '/static/flamengo.png';
				}
			}

			function resetTheme() {
				document.documentElement.classList.remove('theme-flamengo');
				try { localStorage.removeItem('theme'); } catch (e) {}
				clubSymbolEl.style.display = 'none';
				clubSymbolEl.textContent = '';
				clubSymbolEl.style.backgroundImage = '';
				try { clubSymbolEl.removeEventListener('click', resetTheme); } catch (e) {}
			}

			// Ao carregar a página, aplicar tema salvo (se houver)
			try {
				const saved = localStorage.getItem('theme');
				if (saved) applyTheme(saved);
			} catch (e) {}

			let currentUserMenu = null;

			function showUserMenu(event, user) {
				closeUserMenu();
				const menu = document.createElement('div');
				menu.id = 'user-menu';
				menu.style.position = 'absolute';
				menu.style.zIndex = 9999;
				menu.style.background = 'rgba(15,23,42,0.95)';
				menu.style.border = '1px solid rgba(255,255,255,0.06)';
				menu.style.padding = '8px';
				menu.style.borderRadius = '8px';
				menu.style.minWidth = '160px';
				menu.style.boxShadow = '0 8px 20px rgba(0,0,0,0.4)';

				const title = document.createElement('div');
				title.textContent = user;
				title.style.fontWeight = '700';
				title.style.marginBottom = '6px';
				menu.appendChild(title);

				const btnDesafiar = document.createElement('button');
				btnDesafiar.type = 'button';
				btnDesafiar.textContent = 'Desafiar Jogo da Velha';
				btnDesafiar.style.display = 'block';
				btnDesafiar.style.width = '100%';
				btnDesafiar.style.marginBottom = '6px';
				if (user === username) {
				    btnDesafiar.disabled = true;
				    btnDesafiar.textContent = 'Você não pode se desafiar';
				    btnDesafiar.style.opacity = '0.5';
				    btnDesafiar.style.cursor = 'not-allowed';
				}
				btnDesafiar.addEventListener('click', () => {
					if (!socket || socket.readyState !== WebSocket.OPEN) {
						appendMessage('Você não está conectado.', 'system');
						closeUserMenu();
						return;
					}
					socket.send(`/desafiar ${user}`);
					appendMessage(`Desafio enviado para ${user}`, 'system');
					closeUserMenu();
				});
				menu.appendChild(btnDesafiar);

				// (campo de desafio removido) opção de preencher campo removida

				const btnClose = document.createElement('button');
				btnClose.type = 'button';
				btnClose.textContent = 'Fechar';
				btnClose.style.display = 'block';
				btnClose.style.width = '100%';
				btnClose.addEventListener('click', closeUserMenu);
				menu.appendChild(btnClose);

				document.body.appendChild(menu);
				currentUserMenu = menu;

				// position near click, but keep inside viewport
				const x = event.clientX;
				const y = event.clientY;
				const rect = menu.getBoundingClientRect();
				let left = x;
				let top = y;
				if (left + rect.width > window.innerWidth - 8) left = window.innerWidth - rect.width - 8;
				if (top + rect.height > window.innerHeight - 8) top = window.innerHeight - rect.height - 8;
				menu.style.left = `${left}px`;
				menu.style.top = `${top}px`;

				// close when clicking elsewhere
				setTimeout(() => {
					document.addEventListener('click', onDocumentClickForMenu);
				});
			}

			function closeUserMenu() {
				if (!currentUserMenu) return;
				document.body.removeChild(currentUserMenu);
				currentUserMenu = null;
				document.removeEventListener('click', onDocumentClickForMenu);
			}

			function onDocumentClickForMenu(e) {
				if (!currentUserMenu) return;
				if (currentUserMenu.contains(e.target)) return;
				if (e.target.tagName === 'BUTTON' && e.target.parentElement && e.target.parentElement.id === 'user-items') return;
				closeUserMenu();
			}

			// botão de desafio por campo removido — desafios agora são realizados via menu da lista

			btnAccept.addEventListener('click', () => {
				if (!socket || socket.readyState !== WebSocket.OPEN) {
					appendMessage('Você não está conectado.', 'system');
					return;
				}
				socket.send('/aceitar');
			});

			formEl.addEventListener('submit', event => {
				event.preventDefault();
				const raw = inputEl.value || '';
				const text = raw.trim();
				if (!text) return;

				// Comandos locais do cliente
				const cmd = text.toLowerCase();
				if (cmd === '/tema normal' || cmd === '/tema reset' || cmd === '/tema default') {
					resetTheme();
					appendMessage('Tema restaurado localmente.', 'system');
					inputEl.value = '';
					return; // não enviar ao servidor
				}

				if (!socket || socket.readyState !== WebSocket.OPEN) {
					appendMessage('Você não está conectado.', 'system');
					return;
				}

				socket.send(text);
				inputEl.value = '';
			});

			btnQuitGame.addEventListener('click', () => {
				showChatScreen();
				appendMessage('Você saiu do jogo.', 'system');
			});

			window.addEventListener('beforeunload', () => {
				if (socket) socket.close();
			});
		})();