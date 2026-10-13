# DI x Pré Analytics 📈

Aplicação analítica e interativa para acompanhamento, interpolação e visualização da Estrutura a Termo da Taxa de Juros (ETTJ) de contratos **DI x Pré da B3**.

---

## 📁 Estrutura do Repositório

```text
di_pre_analytics/
│
├── data/
│   ├── raw/                  # Os 22 CSVs originais da B3 — nunca modificados
│   └── processed/            # Dados tratados prontos para consumo (CSV e Parquet)
│
├── etl/
│   ├── __init__.py
│   ├── extractor.py          # Leitura e parsing dos CSVs brutos
│   ├── transformer.py        # Limpeza, padronização e cálculos (interpolação e spreads)
│   └── loader.py             # Exportação para data/processed/
│
├── app/
│   ├── main.py               # Ponto de entrada (Streamlit)
│   ├── components/
│   │   ├── curvas.py         # Gráfico de comparação início x fim
│   │   ├── evolucao.py       # Evolução histórica por prazo (vértices)
│   │   ├── heatmap.py        # Mapa de calor de variações diárias (bps)
│   │   └── inclinacao.py     # Spread 5A - 1M e métricas de inclinação
│   └── utils/
│       └── formatters.py     # Formatação de datas, taxas e tooltips em pt-BR
│
├── notebooks/
│   └── exploratorio.ipynb    # Exploração inicial dos dados (pesquisa/desenvolvimento)
│
├── tests/
│   └── test_transformer.py   # Testes automatizados de validação dos cálculos
│
├── .streamlit/
│   └── config.toml           # Tema e configurações visuais do app
│
├── requirements.txt          # Dependências do projeto
├── README.md                 # Documentação do projeto
└── .gitignore                # Arquivos e diretórios ignorados pelo Git
```

---

## 🚀 Como Executar

### 1. Criar e ativar o ambiente virtual (Python 3.10+)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 3. Executar o pipeline de ETL (opcional, automático na inicialização do app)

```bash
python -m etl.loader
```

### 4. Executar os testes automatizados

```bash
pytest tests/
```

### 5. Iniciar o Dashboard Interativo

```bash
streamlit run app/main.py
```
