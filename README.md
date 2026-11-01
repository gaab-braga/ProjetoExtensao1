# Envelhecimento ativo com a PNS 2019

Projeto de extensão: um índice de envelhecimento ativo para pessoas com 60 anos ou mais, com os microdados da Pesquisa Nacional de Saúde 2019 (IBGE).

## Dados

- `scripts/pns_2019_pandas.py` e `scripts/pns_2019_spark.py`: ETL em pandas e em PySpark. Os dois leem o arquivo de largura fixa da PNS pelo layout do IBGE (`input_PNS_2019.sas`), selecionam as colunas e criam os indicadores de saúde e de capacidade funcional.
- `data/processed/pns_2019_pandas.csv`: 43.554 pessoas com 60 anos ou mais e 59 colunas.
- No notebook ficam 22.728 pessoas, as que têm peso amostral (as que responderam ao questionário individual). Com o peso, elas representam 34,4 milhões de idosos.

## O que o notebook faz (`EDA.ipynb`)

1. **Índice (AAI)**: média de duas notas de 0 a 1:
   - capacidade funcional: soma das respostas sobre dificuldade em comer, tomar banho, se vestir, fazer compras e ir ao médico;
   - saúde: combina autoavaliação, número de doenças crônicas e a própria capacidade funcional, que tem o maior peso.
   
   O plano previa cinco domínios. Participação (internet e celular), economia (escolaridade) e acesso (plano de saúde e consulta) são calculados depois, mas não entram no índice. **A nota de capacidade funcional parece invertida** (ver Limitações), então o índice ainda não mede o que promete.
2. **Comparações por grupo**, com média ponderada pelo peso amostral e intervalo de confiança por bootstrap. Por sexo, o índice médio é 0,16 para homens e 0,19 para mulheres.
3. **Perfis**: K-Means com 4 grupos sobre saúde, capacidade funcional, participação, escolaridade e número de doenças.
4. **Fatores de vulnerabilidade**: random forest que prevê quem está nos 20% com menor índice, a partir de idade, escolaridade, renda, número de medicamentos e atividade física, com SHAP para ler o peso de cada variável. AUC de 0,649 no teste. As variáveis que mais pesam são idade e renda.

Os números vêm das saídas salvas no notebook.

## Limitações

- **A capacidade funcional parece invertida.** Na base processada, 39.740 das 43.554 pessoas (91%) aparecem como "não consegue de modo algum" tomar banho sozinha, e a nota funcional tem mediana 0. Na PNS, o código mais alto dessas perguntas é, até onde sei, "não tem dificuldade". Se for isso, o ETL troca os rótulos e a nota trata como pior quem não tem dificuldade. Isso precisa ser conferido no dicionário do IBGE. Como a nota funcional entra na de saúde e no índice, tudo o que depende deles (índice, perfis, modelo, comparações) fica em dúvida até a correção.
- **A análise por município não é válida.** A PNS pública não traz o município da pessoa. O notebook cria um código com os 6 primeiros dígitos da unidade de amostragem (UPA), e o resultado não é um código de município do IBGE (por exemplo, `110000` em Rondônia). Por isso, os arquivos `municipal_scores_with_ci.csv` e `priority_municipalities_bottom20.csv` não devem ser lidos como municípios. Ao cruzar com a malha municipal, só 7 códigos bateram, e o mapa e a análise espacial não rodaram.
- **O intervalo de confiança ignora o desenho da amostra.** O bootstrap sorteia pessoas, não as unidades de amostragem e os estratos da PNS. O intervalo real é mais largo.
- **O teste do modelo está contaminado.** Antes de separar treino e teste, o notebook sorteia 10.000 linhas com reposição, ponderadas pelo peso. A mesma pessoa pode cair no treino e no teste, o que deixa a AUC otimista.
- **O resumo automático (`policy_brief_automated.txt`) tem um erro.** Mostra o índice médio como 0,12 com intervalo de 0,17 a 0,18. O 0,12 é a média do último grupo da comparação por raça ("ignorado"), que ficou na variável. O valor nacional calculado no notebook é 0,18 (intervalo de 0,17 a 0,18).
- A análise de mediação (escolaridade → medicamentos → índice) encontra um efeito indireto de 1% do efeito total, pequeno demais para orientar decisão.
- Os dados são de 2019 e transversais, então mostram associação, não causa.

## Como rodar

```bash
pip install pandas numpy scikit-learn statsmodels seaborn matplotlib shap
jupyter notebook EDA.ipynb
```

O notebook lê `data/processed/pns_2019_pandas.csv`. Para refazer o ETL, baixe os microdados da PNS 2019 no site do IBGE, coloque o arquivo em `data/raw/` e rode `scripts/pns_2019_pandas.py`. A versão em PySpark pede `pyspark` e `findspark`.

## Arquivos

```
scripts/            ETL em pandas e em PySpark
data/raw/           layout e metadados da PNS
data/processed/     base de idosos usada no notebook
EDA.ipynb           análise completa
outputs_aai/        tabelas e gráficos gerados pelo notebook
```
