
# 🧠 Taller RAG con Solr y Milvus — Entrega funcional

Este repositorio implementa dos pipelines **RAG (Retrieval-Augmented Generation)**:

* **Léxico (BM25)** con **Apache Solr**
* **Vectorial (embeddings)** con **Milvus**

Ambos se exponen mediante una **API unificada (FastAPI)**.
Incluye scripts para **conversión, indexación y evaluación** del desempeño de recuperación.

---

## 📁 Estructura del proyecto

```
rag-solr-milvus/
├── data/
│   └── corpus/
│       ├── corpus_bloques_100.csv      # Corpus original
│       └── corpus_texto.jsonl          # Generado tras conversión
├── services/
│   ├── api/                            # API FastAPI (Solr & Milvus)
│   ├── indexer/                        # Scripts de conversión, indexación y evaluación
│   ├── solr/                           # Configuración (schema, core)
│   └── milvus/                         # Notas sobre la colección
├── reports/                            # Resultados del evaluador
├── docker-compose.yml
└── README.md
```

---

## ⚙️ Requisitos previos

* 🐳 **Docker** y **Docker Compose**
* 🐍 **Python 3.10+** (solo si deseas ejecutar scripts de indexación o evaluación desde el host)
* Archivo de datos:
  `data/corpus/corpus_bloques_100.csv`

---

## 🚀 Pasos para ejecución

### 1️⃣ Levantar los servicios

Desde la raíz del proyecto:

```bash
docker compose up -d --build
```

Esto iniciará los contenedores de:

* `solr` (BM25)
* `milvus`, `etcd`, `minio` (vectorial)
* `api` (FastAPI unificada)

Verifica el estado:

```bash
docker ps
```

---

### 2️⃣ Preparar e indexar datos

Instala dependencias de los scripts:

```bash
pip install -r services/indexer/requirements.txt
```

#### 🔹 Convertir CSV → JSONL

```bash
python services/indexer/convertir_csv.py ^
  --input data/corpus/corpus_bloques_100.csv ^
  --output data/corpus/corpus_texto.jsonl ^
  --text-col texto_limpio
```

#### 🔹 Indexar en Solr

```bash
python services/indexer/indexar_solr.py ^
  --solr http://localhost:8983/solr/rag2 ^
  --input data/corpus/corpus_texto.jsonl
```

#### 🔹 Indexar en Milvus

```bash
python services/indexer/index_milvus.py ^
  --input data/corpus/corpus_texto.jsonl ^
  --host localhost ^
  --port 19530
```

---

### 3️⃣ Probar la API

#### ✅ Salud del servicio

```bash
curl http://localhost:8000/health
```

#### 🔍 Consultar Solr (BM25)

```bash
curl "http://localhost:8000/solr?q=paz territorial&k=5"
```

#### 🔎 Consultar Milvus (vectorial)

```bash
curl "http://localhost:8000/milvus?q=paz territorial&k=5"
```

📘 **Documentación interactiva (Swagger):**
👉 [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 4️⃣ Evaluar desempeño

#### 📊 Evaluar Solr

```bash
python services/indexer/evaluator.py ^
  --backend solr ^
  --queries data/corpus/queries.jsonl ^
  --gold data/corpus/gold.jsonl ^
  --k 5
```

#### 📈 Evaluar Milvus

```bash
python services/indexer/evaluator.py ^
  --backend milvus ^
  --queries data/corpus/queries.jsonl ^
  --gold data/corpus/gold.jsonl ^
  --k 5
```

📂 Los resultados se guardarán en:

```
/reports/
```

---

## 🧩 Notas técnicas

* **Solr** usa el campo `text` (definido en `services/solr/schema.json`).
* **Milvus** utiliza la colección `corpus_rag` con los campos:

  * `id` → Clave primaria
  * `embedding` → `FLOAT_VECTOR (dim=384)`
  * `text` → texto del documento

---

## 🧠 Accesos rápidos

* **Solr UI:** [http://localhost:8983](http://localhost:8983)
* **FastAPI Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 💡 Recomendaciones

* No incluyas tu entorno `.venv` en el repositorio (ya está ignorado en `.gitignore`).
* Puedes reiniciar servicios con:

  ```bash
  docker compose down && docker compose up -d
  ```
* Si cambias el modelo de embeddings, asegúrate de **reindexar** en Milvus.

## Evaluación — Solr vs Milvus (q1–q2, k ∈ {5, 20})

**Conjunto y gold**
- Pairs evaluados: 61 (57 positivos) a partir de `data/corpus/*.jsonl`.
- Gold y queries: `data/corpus/gold.jsonl`, `data/corpus/queries.jsonl`.

**Resultados agregados**
- **Latencia media (ms)**: **Milvus ≈ 7.75** | **Solr ≈ 8.88**.
- **ROUGE-L (mean / median)**: **Milvus 0.0133 / 0.0164** | **Solr 0.0012 / 0.0003**.
- **recall@k, mrr, ndcg**: 0.0 (con el *gold* actual y corpus pequeño).
  
**Artefactos**
- CSV final: `reports/final_report.csv`
- Gráficos: `reports/final_latency.png`, `reports/final_rouge.png`, `reports/final_judge.png`

**Reproducibilidad (post-evaluación)**
```bash
python services\indexer\merge_reports.py ^
  --metrics_csv reports\summary.csv ^
  --rouge_csv reports\rouge_by_backend.csv ^
  --judge_csv reports\llm_judge_summary.csv ^
  --out_dir reports

python services\indexer\plot_final.py ^
  --final_csv reports\final_report.csv ^
  --out_dir reports