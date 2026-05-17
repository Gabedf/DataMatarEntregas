````md
# ETL - Inteligência de Negócios

Projeto desenvolvido para a disciplina de Inteligência de Negócios utilizando Python + Polars para realizar o processo de ETL dos dados de entregas da base transacional para o modelo dimensional. :contentReference[oaicite:0]{index=0}

---

# Objetivo

O projeto realiza:

- Extração dos dados do MySQL
- Transformação utilizando Polars
- Criação das dimensões analíticas
- Preparação dos dados para o Data Mart de entregas

---

# Configuração do `.env`

Crie um arquivo `.env` na raiz do projeto com suas credenciais do MySQL:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=[INSIRA SENHA AQUI]
DB_SOURCE=dblogistica
DB_DW=data_mart_entregas
````

As variáveis são utilizadas para conexão com os bancos de dados durante o processo de ETL. 

---

# Utilizando o uv

O projeto utiliza `uv` para gerenciamento das dependências.

## Instalar o uv

### Windows

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Linux / MacOS

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Documentação oficial:

[uv](https://docs.astral.sh/uv/?utm_source=chatgpt.com)

---

# Instalar as dependências

Com o `uv` instalado:

```bash
uv sync
```

---

# Caso não tenha o uv

Você também pode instalar as dependências utilizando o `pip`:

```bash
pip install -r requirements.txt
```

---

# Executar o projeto

Com `uv`:

```bash
uv run main.py
```

Sem `uv`:

```bash
python main.py
```

---

```
```
