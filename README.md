# Lean ETL Pipeline

Pipeline simples em Python pra praticar extract/transform/load. Simula
ordens de manutenção de frota (baseado no tipo de dado que trabalho no
dia a dia) e agrega custo por tipo de serviço e regional num SQLite local.

## Fluxo

```
extract.py  -> gera CSV bruto (simula export do SAP B1, decimal em vírgula)
transform.py -> limpa, converte tipos, agrega
load.py      -> grava a tabela agregada em SQLite
```

## Rodando

```bash
pip install -r requirements.txt
python3 -m src.extract
python3 -m src.load
pytest tests/ -v
```

## Sobre o bug do commit `fix:`

Escrevi os testes unitários usando um DataFrame já limpo direto no fixture,
então eles passavam. Só fui perceber que o pipeline quebrava de verdade
quando rodei o `load.py` ponta a ponta: o CSV simula o export do SAP B1,
que vem com vírgula como separador decimal, e o pandas lia a coluna
`custo` como string em vez de float. Corrigi e adicionei um teste que
lê o CSV de verdade (não um DataFrame mockado) pra pegar esse tipo de
coisa da próxima vez.

## O que não tem aqui

Não tem orquestração (Airflow/Dagster), não tem CI/CD, e não tem testes
de qualidade de dados tipo dbt. É um projeto pequeno pra fixar o
conceito de ETL em camadas separadas e testáveis — os próximos projetos
do portfólio vão cobrir orquestração e CI/CD separadamente.
