## Chat online interativo com jogo da velha


O ProjetoRedes é uma aplicação de chat em tempo real via navegador. Ele permite que múltiplos usuários se conectem por meio de um servidor Python e troquem mensagens instantaneamente por meio de uma interface web.

```Arquitetura de Software```


O projeto adota uma Arquitetura Cliente-Servidor distribuída, projetada para suportar comunicação assíncrona e bidirecional.

Servidor (Backend): Atua como a autoridade central (Authoritative Server). É responsável pela validação das regras de negócio (lógica do jogo), gerenciamento de estado das sessões e retransmissão de mensagens (broadcasting).

Cliente (Frontend): Responsável pela apresentação visual (renderização do DOM) e captura de eventos de entrada do usuário, atuando como um terminal "burro" que reflete o estado fornecido pelo servidor.

```Protocolos de Rede e Comunicação```

A comunicação é fundamentada sobre o protocolo WebSocket (RFC 6455), escolhido em detrimento do HTTP tradicional (REST) devido à natureza de tempo real da aplicação.

Handshake Inicial: A conexão inicia-se via HTTP com um cabeçalho de Upgrade, solicitando a transição para o protocolo WebSocket.

Persistência: Diferente do modelo Request-Response do HTTP, o WebSocket mantém um túnel TCP aberto e persistente. Isso elimina o overhead de latência causado pela renegociação de conexões SSL/TCP a cada pacote enviado.

Baixa Latência: Permite que o servidor envie dados ao cliente (server-push) instantaneamente, sem que o cliente precise solicitar (polling), o que é crítico para a sincronização do tabuleiro do Jogo da Velha.

```Stack Tecnológico e Justificativas```


Backend (Python)
A escolha do Python, especificamente com o uso de bibliotecas de I/O assíncrono (como asyncio e websockets), justifica-se pelo modelo de concorrência:

Concorrência via Event Loop: Ao contrário de servidores multithreaded tradicionais (que criam uma thread por cliente e consomem muita memória), o uso do asyncio permite gerenciar múltiplas conexões simultâneas em uma única thread (Single-Threaded Event Loop). Isso é altamente eficiente para aplicações I/O Bound (que esperam muita rede e processam pouco cálculo pesado).

Gerenciamento de Sockets: A biblioteca websockets abstrai a complexidade do empacotamento de frames binários do protocolo, permitindo o foco na lógica de aplicação.

Frontend (HTML5/JavaScript)
API Nativa de WebSocket: O navegador utiliza a interface WebSocket do JavaScript, permitindo conexão direta com o socket aberto pelo Python.

Manipulação do DOM: O JavaScript intercepta os eventos de clique no tabuleiro e submissão do chat, serializa os dados e os despacha para a rede.

```Descoberta de Jogadores e Sistema de Desafio```

Descoberta (Lista de Usuários): O servidor mantém um registro em memória (dicionário) mapeando o Nome de cada usuário ao seu Socket de conexão. Sempre que um jogador conecta ou desconecta, o servidor envia a lista atualizada via broadcast para todos os clientes, permitindo que a interface exiba quem está online em tempo real.

Mecanismo de Desafio: Ocorre através de roteamento direto (unicast). Quando um jogador envia um desafio, o servidor busca o socket do oponente alvo no registro e encaminha o convite exclusivamente para ele. Se aceito, o servidor vincula os dois sockets em uma instância de jogo privada.


## Chat pelo navegador

Como Rodar o Projeto
Siga os passos abaixo para colocar o chat e o jogo para funcionar no seu computador.

1º Passo: Baixar os arquivos


Clique no botão verde Code lá em cima e escolha Download ZIP.

Extraia (descompacte) a pasta em algum lugar do seu computador (ex: na Área de Trabalho).

2º Passo: Preparar o ambiente


Abra a pasta do projeto que você acabou de extrair.

Segure a tecla SHIFT do teclado e clique com o Botão Direito do mouse em um espaço vazio dentro da pasta.

Clique em "Abrir janela do PowerShell aqui" (ou "Abrir no Terminal").

Na tela azul/preta que abrir, digite o comando abaixo e aperte Enter:
pip install -r requirements.txt
(Isso vai instalar tudo o que o projeto precisa para rodar)

3º Passo: Ligar o Servidor


Ainda na tela preta (PowerShell), digite:
python servidor.py
Se aparecer uma mensagem dizendo que o servidor iniciou, deu tudo certo! 🎉

4º Passo: Acessar


Abra seu navegador (Chrome, Edge, etc.).

Digite na barra de endereço: http://127.0.0.1:8000

Coloque seu nome e clique em Conectar.

🎮 Como Jogar (Chat e Jogo da Velha)
Chat: Basta digitar e enviar, todos na sala verão.

Desafiar alguém:

Veja a lista de "Usuários Conectados" na direita.

Clique no nome do amigo que quer desafiar.

Clique no botão Desafiar.

Se o amigo aceitar, o jogo começa!

🌐 Como jogar online com um amigo (Modo Fácil)
Para jogar com alguém que não está na sua casa, vocês precisarão simular que estão na mesma rede. Siga este tutorial:

A. Configurando o Código (Só você precisa fazer)


Antes de ligar o servidor, precisamos permitir conexões de fora.

Abra o arquivo servidor.py

Procure a linha que tem o endereço 127.0.0.1.

Mude para 0.0.0.0 (Isso libera o servidor para a rede externa).

Salve o arquivo.

B. Usando uma VPN (Radmin ou Hamachi)


Baixe e instale o Radmin VPN (é grátis e fácil).

Crie uma nova rede no Radmin e peça para seu amigo entrar nela.

Copie o seu IP que aparece no Radmin (são vários números, ex: 26.154.20.1).

C. Conectando


Você (Host): Inicia o servidor (python servidor.py) e entra no navegador pelo endereço http://localhost:8000.

Seu Amigo: Abre o navegador e digita o SEU IP do Radmin + a porta 8000.

Exemplo: http://26.154.20.1:8000
