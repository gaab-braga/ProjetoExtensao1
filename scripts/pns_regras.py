"""Regras do ETL da PNS 2019, comuns às versões pandas e PySpark.

Os códigos das perguntas e as categorias de resposta foram conferidos no dicionário oficial
do IBGE (Dicionario_e_input_20220530.zip, arquivo dicionario_PNS_microdados_2019.xls).
O extrato das perguntas usadas está em tests/dicionario_ibge_extrato.csv.
"""

import re

import numpy as np
import pandas as pd

# Código da pergunta no layout do IBGE -> nome da coluna extraída
COLUNAS = {
    "V0001": "uf",
    "V0024": "estrato",
    "UPA_PNS": "upa",
    "V0006_PNS": "num_domicilio",
    "C00301": "num_morador",
    "V00291": "peso_amostral",          # peso do morador selecionado, com calibração
    "V0026": "area_urbana",
    "V0031": "tipo_area",
    "V0022": "num_pessoas_domicilio",
    "C006": "sexo",
    "C008": "idade",
    "C009": "raca_cor",
    "C011": "estado_civil",
    "VDD004A": "nivel_instrucao",
    "VDF003": "renda_percapita",
    "VDE002": "situacao_ocupacional",
    "N001": "autoavaliacao_saude",
    "Q00101": "ultima_medicao_pressao",
    "Q00201": "hipertensao",
    "Q02901": "ultimo_exame_glicemia",
    "Q03001": "diabetes",
    "Q06306": "doenca_cardiaca",
    "Q068": "avc",
    "Q074": "asma",
    "Q11604": "doenca_pulmonar",
    "Q120": "cancer",
    "Q092": "depressao_diag",
    "I00102": "possui_plano_saude",
    "J01101": "ultima_consulta",
    "J037": "internacao_12m",
    "J026": "atendimento_sus",
    "K001": "dificuldade_alimentar",
    "K004": "dificuldade_banho",
    "K010": "dificuldade_vestir",
    "K022": "dificuldade_compras",
    "K031": "dificuldade_medico",
    "K01901": "ajuda_adl",
    "K03401": "ajuda_iadl",
    "K04301": "usa_medicamento_continuo",
    "K04302": "qtd_medicamentos",
    "K052": "vacina_influenza",
    "K05401": "queda_12m",
    "P034": "atividade_fisica",
    "P050": "fumante_atual",
    "P00104": "peso_kg",
    "P00404": "altura_cm",
}

ADL_COLS = ["dificuldade_vestir", "dificuldade_banho", "dificuldade_alimentar"]
IADL_COLS = ["dificuldade_compras", "dificuldade_medico"]
# Cada pergunta vale de 0 (não tem dificuldade) a 3 (não consegue)
MAX_DIFICULDADE = 3 * len(ADL_COLS + IADL_COLS)

CRONICAS = ["hipertensao", "diabetes", "doenca_cardiaca", "avc", "doenca_respiratoria", "cancer", "depressao_diag"]
SIM_NAO = ["hipertensao", "diabetes", "doenca_cardiaca", "avc", "asma", "doenca_pulmonar", "cancer",
           "depressao_diag", "possui_plano_saude", "internacao_12m", "ajuda_adl", "ajuda_iadl",
           "vacina_influenza", "queda_12m", "atividade_fisica"]

# K001, K004, K010, K022 e K031: 1 = não consegue ... 4 = não tem dificuldade
ROTULOS_DIFICULDADE = {
    "1": "Não consegue",
    "2": "Tem grande dificuldade",
    "3": "Tem pequena dificuldade",
    "4": "Não tem dificuldade",
    "9": "Ignorado",
}

ROTULOS = {
    "uf": {
        "11": "Rondônia", "12": "Acre", "13": "Amazonas", "14": "Roraima", "15": "Pará", "16": "Amapá", "17": "Tocantins",
        "21": "Maranhão", "22": "Piauí", "23": "Ceará", "24": "Rio Grande do Norte", "25": "Paraíba", "26": "Pernambuco", "27": "Alagoas", "28": "Sergipe", "29": "Bahia",
        "31": "Minas Gerais", "32": "Espírito Santo", "33": "Rio de Janeiro", "35": "São Paulo",
        "41": "Paraná", "42": "Santa Catarina", "43": "Rio Grande do Sul",
        "50": "Mato Grosso do Sul", "51": "Mato Grosso", "52": "Goiás", "53": "Distrito Federal",
    },
    "area_urbana": {"1": "Urbano", "2": "Rural"},
    "tipo_area": {"1": "Capital", "2": "Resto da RM", "3": "RIDE", "4": "Resto da UF"},
    "sexo": {"1": "Homem", "2": "Mulher"},
    "raca_cor": {"1": "Branca", "2": "Preta", "3": "Amarela", "4": "Parda", "5": "Indígena", "9": "Ignorado"},
    "estado_civil": {"1": "Casado(a)", "2": "Separado(a) ou divorciado(a)", "3": "Viúvo(a)", "4": "Solteiro(a)", "9": "Ignorado"},
    "situacao_ocupacional": {"1": "Ocupado", "2": "Desocupado"},
    "autoavaliacao_saude": {"1": "Muito boa", "2": "Boa", "3": "Regular", "4": "Ruim", "5": "Muito ruim", "9": "Ignorado"},
    "atendimento_sus": {"1": "Sim", "2": "Não", "3": "Não sabe"},
    "fumante_atual": {"1": "Sim", "2": "Sim", "3": "Não", "9": "Ignorado"},
    **{c: {"1": "Sim", "2": "Não", "9": "Ignorado"} for c in SIM_NAO},
    **{c: ROTULOS_DIFICULDADE for c in ADL_COLS + IADL_COLS},
}

REGIAO = {"1": "Norte", "2": "Nordeste", "3": "Sudeste", "4": "Sul", "5": "Centro-Oeste"}


def ler_layout(sas_file):
    """Lê o input SAS do IBGE: código -> (posição inicial 0-based, tamanho)."""
    layout = {}
    padrao = re.compile(r"@(\d{5})\s*(\w+)\s*\$?(\d+)")
    with open(sas_file, "r", encoding="latin-1") as f:
        for linha in f:
            m = padrao.search(linha)
            if m:
                layout[m.group(2)] = (int(m.group(1)) - 1, int(m.group(3)))
    return layout


def _numero(serie):
    return pd.to_numeric(serie.str.strip(), errors="coerce")


def _sim_nao(serie):
    """'1' -> 1, '2' -> 0, resto (ignorado, em branco) -> NaN."""
    return serie.map({"1": 1.0, "2": 0.0})


def derivar(cod):
    """Recebe as colunas extraídas como texto (códigos do IBGE) e devolve a base final.

    Respostas em branco ("não aplicável") e "ignorado" viram ausentes; nada é imputado aqui.
    """
    cod = cod.apply(lambda s: s.astype(str).str.strip())
    # Quem nunca mediu a pressão (ou a glicemia) pula a pergunta do diagnóstico: conta como "não"
    cod["hipertensao"] = cod["hipertensao"].mask(cod["ultima_medicao_pressao"] == "6", "2")
    cod["diabetes"] = cod["diabetes"].mask(cod["ultimo_exame_glicemia"] == "6", "2")
    df = pd.DataFrame(index=cod.index)

    for col in ["uf", "estrato", "upa", "num_domicilio", "num_morador"]:
        df[col] = cod[col]
    df["regiao"] = cod["uf"].str[0].map(REGIAO)

    df["peso_amostral"] = _numero(cod["peso_amostral"])
    df["idade"] = _numero(cod["idade"])
    df["num_pessoas_domicilio"] = _numero(cod["num_pessoas_domicilio"])
    df["mora_sozinho"] = np.where(df["num_pessoas_domicilio"] == 1, "Sim", "Não")
    df["nivel_instrucao"] = _numero(cod["nivel_instrucao"])   # 1 = sem instrução ... 7 = superior completo
    df["renda_percapita"] = _numero(cod["renda_percapita"])

    peso = _numero(cod["peso_kg"])
    altura = _numero(cod["altura_cm"]).where(lambda a: a < 999) / 100
    df["peso_kg"] = peso
    df["altura_m"] = altura
    df["imc"] = peso / altura ** 2

    # Remédios de uso contínuo: quem respondeu "não usa" tem 0
    qtd = _numero(cod["qtd_medicamentos"]).where(lambda q: q < 99)
    df["num_medicamentos"] = np.where(cod["usa_medicamento_continuo"] == "2", 0, qtd)

    df["consulta_12m"] = cod["ultima_consulta"].map(
        {"1": "Sim", "2": "Não", "3": "Não", "4": "Não", "5": "Não"})

    # Doenças crônicas: 1 = sim, 0 = não
    cronicas = pd.DataFrame({c: _sim_nao(cod[c]) for c in CRONICAS if c in cod})
    cronicas["doenca_respiratoria"] = pd.concat(
        [_sim_nao(cod["asma"]), _sim_nao(cod["doenca_pulmonar"])], axis=1).max(axis=1)
    df["multimorbidity_count"] = cronicas[CRONICAS].sum(axis=1, min_count=len(CRONICAS))
    df["multimorb_cat"] = pd.cut(df["multimorbidity_count"], bins=[-1, 0, 1, 2, 100], labels=["0", "1", "2", "3+"])

    # Capacidade funcional: dificuldade = 4 - código (0 = nenhuma, 3 = não consegue)
    dificuldade = pd.DataFrame({
        c: (4 - _numero(cod[c])).where(cod[c].isin(["1", "2", "3", "4"])) for c in ADL_COLS + IADL_COLS})
    df["adl_score"] = dificuldade[ADL_COLS].sum(axis=1, min_count=len(ADL_COLS))
    df["iadl_score"] = dificuldade[IADL_COLS].sum(axis=1, min_count=len(IADL_COLS))
    df["functional_raw"] = df["adl_score"] + df["iadl_score"]
    df["functional_score"] = 1 - df["functional_raw"] / MAX_DIFICULDADE

    plano = _sim_nao(cod["possui_plano_saude"])
    sus = _sim_nao(cod["atendimento_sus"])
    df["dependencia_SUS"] = ((plano == 0) & (sus == 1)).astype(float).where(plano.notna())
    df["cobertura_influenza"] = _sim_nao(cod["vacina_influenza"])

    # Nota de saúde: autoavaliação (1 = muito boa), número de doenças e capacidade funcional
    autoav = _numero(cod["autoavaliacao_saude"]).where(lambda a: a <= 5)

    def z(s):
        return (s - s.mean()) / s.std(ddof=0)

    df["autoav_z"] = z(autoav)
    df["multimorb_z"] = z(df["multimorbidity_count"])
    df["functional_z"] = z(df["functional_score"])
    bruto = -0.5 * df["autoav_z"] - 0.7 * df["multimorb_z"] + 1.2 * df["functional_z"]
    df["health_score_raw"] = bruto
    df["health_score"] = (bruto - bruto.min()) / (bruto.max() - bruto.min())

    for col, rotulos in ROTULOS.items():
        if col in cod:
            df[col] = cod[col].map(rotulos)

    return df
