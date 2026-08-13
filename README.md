# Lean ETL Pipeline

ETL em camadas pra praticar extract/transform/load com validação de qualidade
levada a sério. Simula ordens de manutenção de frota (o tipo de dado que eu mexo
no dia a dia) e agrega custo por tipo de serviço e regional num SQLite local.

O que faz esse projeto valer a leitura não é o ETL — é onde ficam as checagens.

## As duas portas

A ideia central: validar em dois pontos, porque o diagnóstico é diferente em cada um.

```
extract.py  ->  CSV bruto (simula export do SAP B1, decimal em vírgula)
                     |
                [Porta 1]  validar_entrada()  <- o dado como veio da origem
                     |
transform.py ->  limpa e agrega
                     |
                [Porta 2]  validar_saida()    <- o agregado + reconciliação da soma
                     |
load.py     ->  SQLite
```

**Porta 1** olha o dado cru. Se falha aqui, o problema não é meu código — é o que
chegou. Layout diferente, coluna faltando, custo negativo, data no futuro.

**Porta 2** olha o agregado, antes de gravar. Se falha aqui, o problema **é** meu
código: a origem passou na Porta 1, então algo entre uma porta e outra estragou o
número.

A separação é o que torna o erro acionável: um me faz cobrar da origem, o outro me
faz abrir o `transform.py`.

## O check que eu acho mais importante

`checar_soma_preservada()` — compara a soma antes e depois da agregação:

```python
total_antes  = df_origem["custo"].sum()
total_depois = df_agregado["custo_total"].sum()
if abs(total_antes - total_depois) > 0.01:
    raise FalhaQualidadeDados(...)
```

É o único check que pega `groupby` com chave errada, join que multiplicou linha ou
filtro que comeu dado. Sem ele, o total vai errado pro dashboard **e continua
parecendo plausível** — que é o pior tipo de erro, porque ninguém desconfia.

## Quarentena

`separar_quarentena()` faz o contraponto da Porta 1: em vez de abortar a carga
inteira, separa o que presta do que não presta e anota o motivo de cada descarte.

```
4 linhas -> 1 boa, 3 em quarentena
    placa='PR2'  motivo=custo_negativo
    placa='PR3'  motivo=tipo_servico_vazio
    placa='  '   motivo=custo_zerado;placa_vazia
```

Uma linha pode acumular mais de um motivo. A regra que eu sigo: descartar é ok,
descartar sem registrar o motivo é perda de dado silenciosa com outro nome.

Quando usar cada um: Porta 1 aborta quando o arquivo está estruturalmente errado
(dispensa o dado do dia); quarentena salva os 99% quando só algumas linhas estão
ruins.

## Rodando

```bash
pip install -r requirements.txt

python -m src.extract     # gera o CSV bruto
python -m src.load        # extract -> transform -> load, com as duas portas
pytest tests/ -v          # 9 testes
```

Saída esperada do `python -m src.load`:

```
20 linhas carregadas em data/processed/warehouse.db
```

## Estrutura

```
src/
  extract.py         gera o CSV bruto + separar_quarentena()
  quality_checks.py  as duas portas e as checagens individuais
  transform.py       carga, limpeza e agregação
  load.py            grava no SQLite
tests/               9 testes
data/raw/            CSV de entrada
data/processed/      warehouse.db (gerado)
```

## Bugs que este repo já teve, e o que aprendi

**1. Teste que passava com pipeline quebrado.** Escrevi os testes unitários usando
um DataFrame já limpo no fixture, então eles passavam — mas o `load.py` quebrava
ponta a ponta. O CSV simula o export do SAP B1, que vem com vírgula decimal, e o
pandas lia `custo` como string.

Correção: teste que lê o CSV de verdade (`test_carregar_dados_brutos_converte_custo_com_virgula`),
não um DataFrame mockado.

**2. Fixture testando um schema que não existia.** O `quality_checks.py` validava
`id_manutencao` e `data_manutencao`. O CSV real tem `placa` e `data_servico` — e
nem tem `id_manutencao`. Os testes passavam porque o fixture inventava as colunas;
o pipeline real estourava `KeyError`.

Correção: fixture com as colunas reais da origem, e um `checar_colunas_esperadas()`
que falha dizendo qual coluna faltou em vez de dar `KeyError` no meio da validação.

**3. Import de função que não existia.** O `transform.py` importava `validar_saida`
do `quality_checks`, que nunca tinha sido escrita — `ImportError` no `import`. E o
`RAW_PATH` estava definido *depois* das funções que o usavam como valor default,
o que dá `NameError`, porque default de parâmetro é avaliado quando a função é
definida, não quando é chamada.

Correção: `validar_saida()` escrita, `RAW_PATH` movido pro topo.

## O que não tem aqui

Não tem orquestração nem CI — de propósito, é um projeto pequeno pra fixar ETL em
camadas testáveis. Essas partes estão cobertas em
[frota-brasil-pipeline](https://github.com/AlyssonCaputti/frota-brasil-pipeline),
que tem DAG do Airflow com dependência entre tarefas e CI que roda o pipeline
inteiro na amostra.
