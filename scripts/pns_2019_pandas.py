# ETL da PNS 2019 em pandas: lê o arquivo de largura fixa do IBGE, fica com as pessoas de 60 anos ou mais,
# cria os indicadores (regras em pns_regras.py) e salva data/processed/pns_2019_pandas.csv.
#
# Uso: python scripts/pns_2019_pandas.py [--raw caminho/PNS_2019.txt]
# Os microdados (PNS_2019_20220525.zip) ficam no FTP do IBGE: PNS/2019/Microdados/Dados.

import argparse
from pathlib import Path

import pandas as pd

from pns_regras import COLUNAS, derivar, ler_layout

RAIZ = Path(__file__).resolve().parent.parent
RAW_FILE = RAIZ / "data" / "raw" / "PNS_2019.txt"
SAS_FILE = RAIZ / "data" / "raw" / "input_PNS_2019.sas"
OUTPUT_CSV = RAIZ / "data" / "processed" / "pns_2019_pandas.csv"


def extrair_60mais(raw_file, layout):
    """Lê o arquivo linha a linha e guarda só as colunas desejadas das pessoas com 60 anos ou mais."""
    pos_idade, tam_idade = layout["C008"]
    campos = [(nome, *layout[codigo]) for codigo, nome in COLUNAS.items()]
    linhas = []
    with open(raw_file, "r", encoding="latin-1") as f:
        for linha in f:
            idade = linha[pos_idade:pos_idade + tam_idade].strip()
            if idade and int(idade) >= 60:
                linhas.append({nome: linha[pos:pos + tam] for nome, pos, tam in campos})
    return pd.DataFrame(linhas)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=RAW_FILE)
    args = parser.parse_args()

    layout = ler_layout(SAS_FILE)
    faltando = [c for c in COLUNAS if c not in layout]
    if faltando:
        raise SystemExit(f"Códigos ausentes no layout: {faltando}")

    cod = extrair_60mais(args.raw, layout)
    print(f"OK Extraído: {cod.shape} (60 anos ou mais)")

    df = derivar(cod)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"OK Arquivo salvo em {OUTPUT_CSV.relative_to(RAIZ)}: {df.shape}")


if __name__ == "__main__":
    main()
