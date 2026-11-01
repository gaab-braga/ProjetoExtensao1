"""Testes do ETL da PNS 2019.

O dicionário do IBGE é o oráculo: tests/dicionario_ibge_extrato.csv é um extrato do arquivo oficial
dicionario_PNS_microdados_2019.xls (Dicionario_e_input_20220530.zip) com as perguntas que o ETL usa.
"""

import csv
import re
import sys
from pathlib import Path

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from pns_regras import COLUNAS, ROTULOS_DIFICULDADE, derivar, ler_layout  # noqa: E402

CSV = RAIZ / "data" / "processed" / "pns_2019_pandas.csv"
SAIDAS = RAIZ / "outputs_aai"

with open(Path(__file__).with_name("dicionario_ibge_extrato.csv"), encoding="utf-8") as f:
    DICIONARIO = {linha["codigo"]: linha for linha in csv.DictReader(f)}

# Coluna do ETL -> trecho que a pergunta do IBGE tem de conter
PERGUNTA_ESPERADA = {
    "uf": "Unidade da Federação",
    "peso_amostral": "Peso do morador selecionado com calibração",
    "area_urbana": "situação censitária",
    "num_pessoas_domicilio": "Total de moradores",
    "sexo": "Sexo",
    "idade": "Idade",
    "raca_cor": "Cor ou raça",
    "estado_civil": "estado civil",
    "nivel_instrucao": "Nível de instrução",
    "renda_percapita": "Rendimento domiciliar per capita",
    "situacao_ocupacional": "Condição de ocupação",
    "autoavaliacao_saude": "avalia a sua saúde",
    "hipertensao": "hipertensão",
    "diabetes": "diabetes",
    "doenca_cardiaca": "doença do coração",
    "avc": "AVC",
    "asma": "asma",
    "doenca_pulmonar": "pulmão",
    "cancer": "câncer",
    "depressao_diag": "depressão",
    "possui_plano_saude": "plano de saúde médico",
    "ultima_consulta": "consultou um médico pela última vez",
    "internacao_12m": "internado",
    "atendimento_sus": "SUS",
    "dificuldade_alimentar": "para comer sozinho",
    "dificuldade_banho": "para tomar banho sozinho",
    "dificuldade_vestir": "para se vestir sozinho",
    "dificuldade_compras": "para fazer compras sozinho",
    "dificuldade_medico": "para ir ao médico sozinho",
    "usa_medicamento_continuo": "uso regular ou contínuo",
    "qtd_medicamentos": "Quantos medicamentos",
    "vacina_influenza": "vacina contra gripe",
    "queda_12m": "queda",
    "atividade_fisica": "exercício físico",
    "fumante_atual": "fuma",
    "peso_kg": "Peso - Final",
    "altura_cm": "Altura - Final",
}


@pytest.mark.parametrize("coluna,trecho", PERGUNTA_ESPERADA.items())
def test_codigo_aponta_para_a_pergunta_certa(coluna, trecho):
    codigo = {nome: cod for cod, nome in COLUNAS.items()}[coluna]
    assert codigo in DICIONARIO, f"{codigo} não está no extrato do dicionário"
    assert trecho.lower() in DICIONARIO[codigo]["descricao"].lower(), (
        f"{coluna} usa {codigo}, que no IBGE é: {DICIONARIO[codigo]['descricao']}")


@pytest.mark.parametrize("coluna", ["dificuldade_alimentar", "dificuldade_banho", "dificuldade_vestir",
                                    "dificuldade_compras", "dificuldade_medico"])
def test_rotulos_de_dificuldade_iguais_ao_dicionario(coluna):
    codigo = {nome: cod for cod, nome in COLUNAS.items()}[coluna]
    categorias = dict(c.split("=", 1) for c in DICIONARIO[codigo]["categorias"].split(" | "))
    assert ROTULOS_DIFICULDADE == categorias


def test_layout_sem_correcao_manual_de_posicao():
    layout = ler_layout(RAIZ / "data" / "raw" / "input_PNS_2019.sas")
    assert layout["K004"] == (449, 1)
    assert layout["P00404"] == (616, 3)
    assert layout["V00291"] == (1425, 14)


def _linha(**respostas):
    base = {nome: "" for nome in COLUNAS.values()}
    base.update(uf="35", idade="070", peso_amostral="00100.00000000", autoavaliacao_saude="2",
                hipertensao="2", diabetes="2", doenca_cardiaca="2", avc="2", asma="2",
                doenca_pulmonar="2", cancer="2", depressao_diag="2")
    base.update(respostas)
    return base


K = ["dificuldade_alimentar", "dificuldade_banho", "dificuldade_vestir", "dificuldade_compras", "dificuldade_medico"]


def test_quem_nao_tem_dificuldade_tem_nota_funcional_maxima():
    sem = _linha(**{c: "4" for c in K})
    nao_consegue = _linha(**{c: "1" for c in K})
    df = derivar(pd.DataFrame([sem, nao_consegue]))
    assert df.loc[0, "dificuldade_banho"] == "Não tem dificuldade"
    assert df.loc[0, "functional_score"] == 1
    assert df.loc[1, "dificuldade_banho"] == "Não consegue"
    assert df.loc[1, "functional_score"] == 0


def test_resposta_ignorada_nao_vira_nota():
    df = derivar(pd.DataFrame([_linha(**{**{c: "4" for c in K}, "dificuldade_banho": "9"})]))
    assert pd.isna(df.loc[0, "functional_score"])


def test_quem_nunca_mediu_a_pressao_conta_sem_hipertensao():
    df = derivar(pd.DataFrame([_linha(hipertensao="", ultima_medicao_pressao="6")]))
    assert df.loc[0, "hipertensao"] == "Não"


# ---------- base gerada (data/processed/pns_2019_pandas.csv) ----------

@pytest.fixture(scope="module")
def base():
    return pd.read_csv(CSV, low_memory=False)


def test_csv_maioria_dos_idosos_sem_dificuldade_para_tomar_banho(base):
    assert (base["dificuldade_banho"] == "Não tem dificuldade").mean() > 0.5


def test_csv_nota_funcional_alta_na_maioria(base):
    assert base["functional_score"].median() > 0.5


def test_csv_autoavaliacao_tem_as_cinco_respostas(base):
    respondentes = base[base["peso_amostral"].notna()]
    assert set(respondentes["autoavaliacao_saude"].dropna()) == {"Muito boa", "Boa", "Regular", "Ruim", "Muito ruim"}


def test_csv_altura_em_metros_plausivel(base):
    assert base["altura_m"].dropna().between(1.2, 2.2).mean() > 0.99


# ---------- saídas do notebook ----------

def test_resumo_mostra_a_media_nacional():
    pessoas = pd.read_csv(SAIDAS / "pns_2019_processed_60plus.csv")
    nacional = (pessoas["AAI_total"] * pessoas["peso_amostral"]).sum() / pessoas["peso_amostral"].sum()
    texto = (SAIDAS / "policy_brief_automated.txt").read_text(encoding="utf-8")
    valor = float(re.search(r"AAI médio: ([0-9.]+)", texto).group(1))
    assert valor == pytest.approx(nacional, abs=0.005)


def test_analise_por_uf_tem_as_27_ufs():
    ufs = pd.read_csv(SAIDAS / "uf_scores_with_ci.csv")
    assert len(ufs) == 27
    assert not (SAIDAS / "municipal_scores_with_ci.csv").exists()
