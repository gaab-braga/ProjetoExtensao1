# Envelhecimento ativo com a PNS 2019

Projeto de extensão: um índice de envelhecimento ativo para pessoas com 60 anos ou mais, com os microdados da Pesquisa Nacional de Saúde 2019 (IBGE).

## Dados

- `scripts/pns_2019_pandas.py` e `scripts/pns_2019_spark.py`: ETL em pandas e em PySpark. Os dois leem o arquivo de largura fixa da PNS pelo layout do IBGE (`input_PNS_2019.sas`) e usam as mesmas regras, que ficam em `scripts/pns_regras.py`.
- Cada código de pergunta e cada categoria de resposta foram conferidos no dicionário oficial do IBGE (`dicionario_PNS_microdados_2019.xls`). O extrato das perguntas usadas está em `tests/dicionario_ibge_extrato.csv`.
- `data/processed/pns_2019_pandas.csv`: 43.554 pessoas com 60 anos ou mais e 59 colunas.
- No notebook ficam 22.728 pessoas, as que têm peso amostral (as que responderam ao questionário individual). Com o peso, elas representam 34,4 milhões de idosos.

## O que o notebook faz (`EDA.ipynb`)

1. **Índice (AAI)**: média de duas notas de 0 a 1.
   - **Capacidade funcional**: dificuldade para comer, tomar banho, se vestir, fazer compras e ir ao médico sozinho. Cada pergunta vale de 0 (não tem dificuldade) a 3 (não consegue), e a nota é 1 menos a soma dividida por 15.
   - **Saúde**: combina a autoavaliação de saúde, o número de doenças crônicas (7) e a própria capacidade funcional, que tem o maior peso.

   Índice médio nacional: **0,862** (intervalo de 0,858 a 0,865). Saúde: 0,808. Capacidade funcional: 0,916. A maioria dos idosos não tem dificuldade nenhuma: 39.740 das 43.554 pessoas (91%) não têm dificuldade para tomar banho.
2. **Comparações por grupo**, com média ponderada pelo peso amostral e intervalo de confiança por bootstrap:
   - por sexo: 0,847 para mulheres e 0,882 para homens;
   - por região: Nordeste com o menor índice (0,843) e Centro-Oeste com o maior (0,875);
   - por UF: Ceará com o menor (0,824) e Distrito Federal com o maior (0,887). As 9 UFs do Nordeste são as 9 com menor índice.
3. **Perfis**: K-Means com 4 grupos. Um deles reúne quem tem saúde e capacidade funcional baixas (notas médias de 0,48 e 0,44).
4. **Fatores de vulnerabilidade**: random forest que prevê quem está nos 20% com menor índice, a partir de idade, nível de instrução, renda, número de remédios de uso contínuo, consulta no último ano, plano de saúde, atividade física e fumo. AUC de 0,849 no teste, ponderada pelo peso. As variáveis que mais pesam são o número de remédios e a idade.
5. **Mediação**: quem tem mais instrução tem índice um pouco maior. Quase todo esse efeito é direto. O caminho que passa pelo número de remédios vale 3% do efeito total e vai no sentido contrário: mais instrução vem com um pouco mais de remédios, e mais remédios vêm com índice menor.

Os números vêm das saídas salvas no notebook e de `outputs_aai/`.

## Correções desta versão

A versão anterior do ETL lia várias perguntas erradas. Os dados não mudaram, só a leitura.

- **A capacidade funcional estava invertida.** Na PNS, o código 4 dessas perguntas é "não tem dificuldade" e o 1 é "não consegue". O ETL usava a ordem contrária, então dava a pior nota a quem não tinha dificuldade. O índice médio caía para 0,18.
- **Cerca de 20 colunas apontavam para outra pergunta.** Por exemplo, a "autoavaliação de saúde" era a pergunta "O(A) Sr(a) sabe seu peso?", e "usa internet" era "a entrevista foi realizada". Já "vacina da gripe" era "dirige automóvel", e a altura era o peso dividido por 100. Das 7 doenças crônicas, 5 eram outras perguntas.
- **A análise por município saiu.** A PNS pública não traz o município da pessoa, e o código que o notebook montava a partir da UPA não é um código de município. A análise geográfica agora é por UF (`outputs_aai/uf_scores_with_ci.csv`).
- **O resumo automático mostra a média nacional.** Antes mostrava a média do último subgrupo calculado.
- **O sorteio com reposição do modelo acontece depois da divisão entre treino e teste.** Antes a mesma pessoa podia cair nos dois lados.
- **Os gráficos de SHAP usam os valores reais das variáveis.** Antes usavam valores sorteados. O diagrama de mediação usa os coeficientes estimados, não um valor fixo.

Saíram do ETL o uso de internet e de celular: a PNS só pergunta isso para o domicílio, não para cada pessoa. Por isso não existe nota de participação digital.

## Limitações

- **O intervalo de confiança ignora o desenho da amostra.** O bootstrap sorteia pessoas, não as unidades de amostragem e os estratos da PNS. O intervalo real é mais largo, e algumas diferenças entre UFs podem deixar de ser claras.
- **O índice tem "teto".** 29.335 das 43.554 pessoas (67%) não têm dificuldade em nenhuma das 5 atividades e ficam com nota funcional 1, então a nota separa pouco quem está bem.
- **O modelo pode estar se apoiando em uma parte do próprio índice.** O número de remédios de uso contínuo anda junto com o número de doenças crônicas, que entra na nota de saúde. Parte da AUC pode vir daí.
- **A mediação é uma regressão simples**, sem peso amostral e sem controles.
- **O ETL em PySpark não foi executado nesta versão** (falta Java no ambiente). Ele usa as mesmas regras testadas da versão pandas, que foi a que gerou o CSV.
- Os dados são de 2019 e transversais, então mostram associação, não causa.

## Como rodar

```bash
pip install pandas numpy scikit-learn statsmodels seaborn matplotlib shap openpyxl pytest
python -m pytest tests
jupyter notebook EDA.ipynb
```

O notebook lê `data/processed/pns_2019_pandas.csv`. Para refazer o ETL, baixe os microdados da PNS 2019 no FTP do IBGE (`PNS/2019/Microdados/Dados/PNS_2019_20220525.zip`), extraia `PNS_2019.txt` e rode:

```bash
python scripts/pns_2019_pandas.py --raw caminho/para/PNS_2019.txt
```

A versão em PySpark pede `pyspark`, `findspark` e Java.

## Testes

`tests/test_etl.py` confere:
- se cada coluna lê a pergunta certa, comparando com o extrato do dicionário do IBGE;
- se as categorias de dificuldade são as do dicionário;
- se a base gerada é plausível (a maioria sem dificuldade para tomar banho, as 5 respostas de autoavaliação, altura em metros);
- se as saídas do notebook trazem a média nacional e as 27 UFs.

Os testes reprovam contra o CSV antigo e contra o código com os rótulos invertidos.

## Arquivos

```
scripts/            ETL em pandas e em PySpark, e as regras comuns (pns_regras.py)
tests/              testes e extrato do dicionário do IBGE
data/raw/           layout da PNS (input SAS do IBGE)
data/processed/     base de idosos usada no notebook
EDA.ipynb           análise completa
outputs_aai/        tabelas e gráficos gerados pelo notebook
```
