#!/usr/bin/env python3
"""
ETL PNS 2019 - Versão PySpark
=============================
A extração (leitura do arquivo de largura fixa e filtro de 60+) roda no Spark.
Os códigos, rótulos e indicadores vêm de pns_regras.py, os mesmos da versão pandas.

Uso: python scripts/pns_2019_spark.py [caminho/PNS_2019.txt]
"""

import os
import sys
from pathlib import Path

from pns_regras import COLUNAS, derivar, ler_layout

# ==========================================
# CONFIGURAÇÕES
# ==========================================

BASE_PATH = Path(__file__).resolve().parent.parent
RAW_FILE = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE_PATH / "data" / "raw" / "PNS_2019.txt"
SAS_FILE = BASE_PATH / "data" / "raw" / "input_PNS_2019.sas"
OUTPUT_DIR = BASE_PATH / "data" / "processed"
OUTPUT_CSV = OUTPUT_DIR / "pns_2019_spark.csv"

# ==========================================
# SETUP SPARK
# ==========================================

print("=" * 70)
print("🚀 ETL PNS 2019 - VERSÃO PYSPARK")
print("=" * 70)

os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

import findspark
findspark.init()

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, substring, trim

spark = SparkSession.builder \
    .appName("ETL_PNS_2019") \
    .master("local[*]") \
    .config("spark.driver.memory", "8g") \
    .config("spark.sql.shuffle.partitions", "32") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")
print(f"✅ Spark {spark.version} iniciado\n")

# ==========================================
# ETAPA 1: LAYOUT DO IBGE
# ==========================================

print("📖 [1/3] Lendo o layout (input SAS do IBGE)...")
layout = ler_layout(SAS_FILE)
faltando = [c for c in COLUNAS if c not in layout]
if faltando:
    raise SystemExit(f"Códigos ausentes no layout: {faltando}")
print(f"   ✓ {len(COLUNAS)} colunas localizadas")

# ==========================================
# ETAPA 2: EXTRAÇÃO E FILTRO 60+ NO SPARK
# ==========================================

print("\n📥 [2/3] Extraindo colunas do arquivo raw...")
df_raw = spark.read.text(str(RAW_FILE), lineSep="\n")
n_total = df_raw.count()

# substring é 1-based no Spark
extract_expr = [substring(col("value"), pos + 1, tam).alias(nome)
                for codigo, nome in COLUNAS.items()
                for pos, tam in [layout[codigo]]]
df_extracted = df_raw.select(*extract_expr)

df_filtered = df_extracted.filter(trim(col("idade")).cast("int") >= 60)
n_60plus = df_filtered.count()
print(f"   ✓ {n_total:,} → {n_60plus:,} registros com 60 anos ou mais")

# ==========================================
# ETAPA 3: INDICADORES (mesmas regras do pandas)
# ==========================================

print("\n🧮 [3/3] Criando indicadores...")
df_pandas = derivar(df_filtered.toPandas())

df_pandas.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
print(f"\n✅ Arquivo salvo: {OUTPUT_CSV.relative_to(BASE_PATH)} ({len(df_pandas):,} registros, {len(df_pandas.columns)} colunas)")

spark.stop()
print("\n🔌 Spark encerrado")
