Para editar:

1º passo :
instalar https://git-scm.com/

2º passo:

shift + direito em uma pasta abrir janela do powershell aqui, deem o comando do git clone igual esta abaixo e pronto

git clone https://github.com/Laslest/ProjetoRedes.git

3º passo: 

Para enviarem atualizações ( estejam certo de que esteja funcionando )

shift + direito na pasta ProjetoRedes (a que voces clonaram) abrir janela do powershell aqui e deem os seguintes comandos

git add NOME DO ARQUIVO QUE MODIFICOU (por exemplo redes.py)

git commit -m "AQUI ADICIONEM A FUNCIONALIDADE OU O QUE VOCES ATUALIZARAM"

git push origin main


4º passo:

para puxar atualizações

shift + direito na pasta ProjetoRedes abrir janela do powershell aqui e de o seguinte comando

git pull origin main

## Chat pelo navegador (opcional)


1º Instale as dependências mínimas:
	```powershell
	pip install -r requirements.txt
	```

	
2º. Inicie o servidor (escolha apenas um comando):
	```powershell
	python servidor.py
	```

	
3º. Abra o navegador e acesse `http://127.0.0.1:8000`.



4º. Informe um nome simples e clique em "Conectar" para começar a conversar.

