# services/indexer/evaluator.py
import argparse, json, time, math, pathlib, statistics, requests
from typing import List, Dict, Any, Optional

# --------- Métricas de recuperación ---------
def recall_at_k(ranked_ids: List[str], gold_ids: List[str], k: int = 5) -> float:
    if not gold_ids:
        return 0.0
    top = set(ranked_ids[:k])
    return len(top & set(gold_ids)) / len(set(gold_ids))

def mrr(ranked_ids: List[str], gold_ids: List[str]) -> float:
    gold = set(gold_ids)
    for i, docid in enumerate(ranked_ids, 1):
        if docid in gold:
            return 1.0 / i
    return 0.0

def ndcg(ranked_ids: List[str], gold_ids: List[str], k: int = 10) -> float:
    gold = set(gold_ids)
    def dcg(ids: List[str]) -> float:
        s = 0.0
        for i, d in enumerate(ids[:k], 1):
            rel = 1.0 if d in gold else 0.0
            if rel:
                s += (2**rel - 1) / math.log2(i + 1)
        return s
    ideal_ids = list(gold)  # todas relevantes al inicio
    ideal = dcg(ideal_ids)
    return (dcg(ranked_ids) / ideal) if ideal > 0 else 0.0

# --------- ROUGE-L opcional (si hay 'ref_answer' en gold) ---------
try:
    from rouge_score import rouge_scorer
    _scorer = rouge_scorer.RougeScorer(["rougeLsum"], use_stemmer=False)
except Exception:
    _scorer = None

def rouge_l(pred: str, ref: Optional[str]) -> Optional[float]:
    if not _scorer or not ref:
        return None
    s = _scorer.score(ref, pred)
    return float(s["rougeLsum"].fmeasure)

# --------- Evaluación ---------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queries", default="data/corpus/queries.jsonl",
                    help="JSONL con objetos {qid, query}")
    ap.add_argument("--gold", default="data/corpus/gold.jsonl",
                    help="JSONL con objetos {qid, relevant_ids, [ref_answer]}")
    ap.add_argument("--backend", default="solr", choices=["solr","milvus"])
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--api", default="http://localhost:8000/ask")
    ap.add_argument("--out", default="reports/resultados.jsonl")
    args = ap.parse_args()

    queries = [json.loads(l) for l in open(args.queries, encoding="utf-8")]
    gold_map: Dict[str, Dict[str, Any]] = {}
    for d in map(json.loads, open(args.gold, encoding="utf-8")):
        gold_map[d["qid"]] = d

    outp = pathlib.Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)

    agg = {"recall": [], "mrr": [], "ndcg": [], "lat_ms": [], "rougeL": []}

    with outp.open("w", encoding="utf-8") as fout:
        for q in queries:
            qid, query = q["qid"], q["query"]
            gold = gold_map.get(qid, {})
            gold_ids = gold.get("relevant_ids", [])
            ref_answer = gold.get("ref_answer")

            t0 = time.time()
            # --- Llamada al API del buscador ---
            resp = requests.get(
                args.api,
                params={"query": query, "backend": args.backend, "k": args.k},
                timeout=120
            ).json()

            # Algunos backends (o proxys) devuelven una LISTA en vez de un objeto
            # Estandarizamos a dict tomando el primer elemento si llega como lista.
            if isinstance(resp, list):
                resp = resp[0] if resp else {}

            # Campos esperados (con valores por defecto por si faltan)
            lat = resp.get("latency_ms", int((time.time() - t0) * 1000))
            sources = resp.get("sources", [])
            ids = [s.get("id") for s in sources if isinstance(s, dict) and "id" in s]
            pred_answer = resp.get("answer", "")

            # Métricas
            rec = recall_at_k(ids, gold_ids, k=args.k)
            rr  = mrr(ids, gold_ids)
            nd  = ndcg(ids, gold_ids, k=args.k)
            rl  = rouge_l(pred_answer, ref_answer)

            agg["recall"].append(rec)
            agg["mrr"].append(rr)
            agg["ndcg"].append(nd)
            agg["lat_ms"].append(lat)
            if rl is not None:
                agg["rougeL"].append(rl)

            fout.write(json.dumps({
                "qid": qid,
                "query": query,
                "backend": args.backend,
                "k": args.k,
                "latency_ms": lat,
                "recall@k": rec,
                "mrr": rr,
                "ndcg": nd,
                **({"rougeL": rl} if rl is not None else {})
            }, ensure_ascii=False) + "\n")

    # Resumen
    summary = {
        "backend": args.backend,
        "k": args.k,
        "recall_mean":     statistics.mean(agg["recall"]) if agg["recall"] else 0.0,
        "mrr_mean":        statistics.mean(agg["mrr"])    if agg["mrr"]    else 0.0,
        "ndcg_mean":       statistics.mean(agg["ndcg"])   if agg["ndcg"]   else 0.0,
        "latency_ms_mean": round(statistics.mean(agg["lat_ms"]), 2) if agg["lat_ms"] else 0.0,
    }
    if agg["rougeL"]:
        summary["rougeL_mean"] = statistics.mean(agg["rougeL"])

    pathlib.Path("reports/summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    # CSV rápido
    csv = "metric,value\n" + "\n".join(f"{k},{v}" for k, v in summary.items())
    pathlib.Path("reports/summary.csv").write_text(csv, encoding="utf-8")
    print("Resumen:", summary)

if __name__ == "__main__":
    main()
