"""
Simula a extração de ordens de manutenção de frota vindas do ERP (SAP B1).

Obs: o export real do SAP costuma vir com separador decimal em vírgula
(padrão pt-BR), então geramos os dados aqui do mesmo jeito pra testar
o pipeline com um cenário mais próximo da realidade.
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "manutencoes.csv"

TIPOS_SERVICO = ["Troca de óleo", "Freios", "Suspensão", "Pneus", "Revisão elétrica"]
REGIONAIS = ["Curitiba", "Sao Paulo", "Joinville", "Londrina"]
PLACAS = [f"PR{n:04d}" for n in range(1, 31)]


def gerar_dados_brutos(n_linhas=400, seed=7):
    random.seed(seed)
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    inicio = datetime(2025, 6, 1)

    with open(RAW_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["data_servico", "placa", "tipo_servico", "regional", "custo"])

        for _ in range(n_linhas):
            data = inicio + timedelta(days=random.randint(0, 300))
            placa = random.choice(PLACAS)
            tipo = random.choice(TIPOS_SERVICO)
            regional = random.choice(REGIONAIS)
            custo = round(random.uniform(80.0, 2400.0), 2)
            # formato pt-BR igual ao export do ERP (vírgula decimal)
            custo_str = str(custo).replace(".", ",")
            writer.writerow([data.strftime("%d/%m/%Y"), placa, tipo, regional, custo_str])

    return RAW_PATH


if __name__ == "__main__":
    caminho = gerar_dados_brutos()
    print(f"gerado: {caminho}")
