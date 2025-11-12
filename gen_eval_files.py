# gen_eval_files.py
# Genera data/corpus/queries.jsonl.txt y data/corpus/gold.jsonl.txt
# a partir de data/corpus/corpus_texto.jsonl

import json, os

IN_PATH = r"data/corpus/corpus_texto.jsonl"
Q_OUT  = r"data/corpus/queries.jsonl.txt"
G_OUT  = r"data/corpus/gold.jsonl.txt"
N = 5  # cuántos pares generar (ajústalo si quieres)

os.makedirs(r"data/corpus", exist_ok=True)

def first_words(text, n=16):
    return " ".join(text.split()[:n])

queries = []
gold = []

with open(IN_PATH, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i >= N:
            break
        try:
            obj = json.loads(line)
        except Exception:
            obj = {"id": str(i), "texto": line.strip()}
        doc_id = str(obj.get("id", i))
        texto  = str(obj.get("texto", obj.get("content", ""))).strip()
        if not texto:
            texto = line.strip()

        qid = str(i + 1)
        queries.append({"qid": qid, "query": first_words(texto, 16)})
        gold.append({
            "qid": qid,
            "relevant_ids": [doc_id],
            "ref_answer": first_words(texto, 40)
        })

with open(Q_OUT, "w", encoding="utf-8") as f:
    for q in queries:
        f.write(json.dumps(q, ensure_ascii=False) + "\n")

with open(G_OUT, "w", encoding="utf-8") as f:
    for g in gold:
        f.write(json.dumps(g, ensure_ascii=False) + "\n")

print(f"[OK] Escritos {len(queries)} queries en {Q_OUT}")
print(f"[OK] Escritos {len(gold)} gold en {G_OUT}")