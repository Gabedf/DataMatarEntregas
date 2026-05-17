# %% IMPORTS
import polars as pl
from itables import show
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

## %% VARIÁVEIS DE AMBIENTE
load_dotenv()

source_url = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_SOURCE')}"
)

engine = create_engine(source_url)

with engine.connect() as conn:
    print("Conectado!")

## %% TABELAS EXISTENTES (utilizado para possíveis análises)
tabelas = ["centrosdistribuicao", "cidades", "clientes", "encomendas", "entregas", "estados", 
 "motoristas", "movimentacoes_encomenda", "rotas", "situacoeentregas", "situacoesmovimentacao", 
 "tiposervico", "tiposveiculos", "veiculos", "viagens", "viagens_encomendas"]

## %% QUERYS
query_cidade    = f"""
                    SELECT
                    *
                    FROM cidades
                    """

query_estado    = f"""
                    SELECT
                    *
                    FROM estados
                    """

query_servico    = f"""
                    SELECT
                    *
                    FROM tiposervico
                    """

query_encomenda = f"""
                    SELECT
                    *
                    FROM encomendas
                    """

query_clientes = f"""
                    SELECT
                    *
                    FROM clientes
                    """

query_entregas  = f"""
                    SELECT
                    *
                    FROM entregas
                    """

query_status    = f"""
                    SELECT
                    *
                    FROM situacoeentregas
                    """

## %% CONSULTA MYSQL
cidade = pl.read_database(
    query=query_cidade,
    connection=engine
)

estado = pl.read_database(
    query=query_estado,
    connection=engine
)

servico = pl.read_database(
    query=query_servico,
    connection=engine
)

clientes = pl.read_database(
    query=query_clientes,
    connection=engine
)

encomenda = pl.read_database(
    query=query_encomenda,
    connection=engine
)

entrega = pl.read_database(
    query=query_entregas,
    connection=engine
)

situacao = pl.read_database(
    query=query_status,
    connection=engine
)

data = pl.read_excel('data/raw/Ch3-SampleDateDim.xls', sheet_name='LoadDates')

## %% TRATAMENTOS E CONSOLUIDAÇÃO TABELAS DIMENSÃO
# CONSOLIDAÇÃO DIMENSÃO ENCOMENDA
dim_encomenda = (
    encomenda.join(
        servico,
        left_on='id_tiposervico',
        right_on='id_tipoServico',
        how='left'
    )
    .select([
        'id_encomenda',
        'id_cliente',
        'desc_TipoServico',
        'peso',
        'volume',
        'valor_frete'
    ])
    .rename({
        'desc_TipoServico': 'tipo_servico'
    })
)

# GERA NOVO ID DIMENSIONAL
dim_encomenda = (
    dim_encomenda
    .with_row_index(name='idDimEncomenda', offset=1)
)

# CONSOLIDAÇÃO DIMENSÃO CLIENTES
dim_cliente = (
    clientes
    .join(
        cidade,
        on='id_cidade',
        how='left'
    )
    .join(
        estado,
        left_on='id_estado',
        right_on='id_estados',
        how='left'
    )
    .select([
        "id_cliente",
        "nome_cliente",
        "tipo_cliente",
        "nm_cidade",
        "nm_estado"
    ])
    .with_row_index(name='idDimCliente', offset=1)
)
dim_cliente = dim_cliente.rename({'nome_cliente': 'nomeCliente', 'nm_cidade': 'cidade', 'nm_estado': 'estado'})

# CONSOLIDAÇÃO DIMENSÃO DATA
dim_data  = (data
             .select(['date key', 'day num in month', 'month', 'year'])
             .rename({'date key': 'idDimData',
                      'day num in month': 'dia',
                      'month': 'mes',
                      'year': 'ano'}))

# LISTA COM TABELAS DIMENSÃO EXISTENTES
dimensoes = [dim_encomenda, dim_cliente, dim_data]

## %% - TRATAMENTOS E CONSOLIDAÇÃO TABELA FATO
entrega = entrega.with_columns([(pl.col("data_entrega") - pl.col("data_saida_entrega")).dt.total_minutes().cast(pl.Int64).alias('tempoEntrega'),
                                pl.col("data_entrega").dt.strftime("%Y%m%d").cast(pl.Int64).alias('idDimDataEntrega')])

# Joins para trazer tabelas dimensão para tabela fato
fatoEntregaAux = (
    entrega
        .join(
            dim_encomenda,
            on='id_encomenda',
            how='left')
        .join(
            dim_cliente,
            on='id_cliente',
            how='left'
        )
        .join(
            situacao,
            on='id_situacao',
            how='left'
        )
               )

## %%
# Colunas essenciais para tabela fato
fatoEntrega     = (fatoEntregaAux
                   .rename({'desc_situacao': 'situacaoEntrega'})
                   .select(['idDimCliente', 'idDimEncomenda', 'idDimDataEntrega', 'tempoEntrega', 'situacaoEntrega']))
dim_encomenda   = dim_encomenda.drop(['id_cliente', 'id_encomenda'])
dim_cliente     = dim_cliente.drop('id_cliente')

## %%
show(dim_encomenda)
show(dim_cliente)
show(dim_data)
show(fatoEntrega)

## %% SUBIR BANCO
server_url = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}"
)

engine_server = create_engine(server_url)

with engine_server.connect() as conn:
    conn.execute(text(
        "CREATE DATABASE IF NOT EXISTS data_mart_entregas"
    ))
    conn.commit()

print("Banco dimensional criado!")

dw_url = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}/data_mart_entregas"
)

engine_dw = create_engine(dw_url)
with engine_dw.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS fatoEntrega"))
    conn.execute(text("DROP TABLE IF EXISTS dim_cliente"))
    conn.execute(text("DROP TABLE IF EXISTS dim_encomenda"))
    conn.execute(text("DROP TABLE IF EXISTS dim_data"))
    conn.commit()
    
## %%
dim_cliente.to_pandas().to_sql(
    name='dim_cliente',
    con=engine_dw,
    if_exists='fail',
    index=False
)
dim_encomenda.to_pandas().to_sql(
    name='dim_encomenda',
    con=engine_dw,
    if_exists='fail',
    index=False
)
dim_data.to_pandas().to_sql(
    name='dim_data',
    con=engine_dw,
    if_exists='fail',
    index=False
)
fatoEntrega.to_pandas().to_sql(
    name='fatoEntrega',
    con=engine_dw,
    if_exists='fail',
    index=False
)