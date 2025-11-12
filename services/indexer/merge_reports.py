import csv, os, argparse, statistics as st

def mean_safe(vals):
    vals = [v for v in vals if isinstance(v,(int,float))]
    return round(st.mean(vals),4) if vals else 0.0

def load_metrics(path):
    rows=[]
    if not os.path.exists(path):
        print(f"[WARN] No existe {path}")
        return rows
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows

def agg_from_rows(rows):
    lat = []
    rec = []
    mrr = []
    ndc = []
    for r in rows:
        # columnas que generó evaluator.py
        lat.append(float(r.get("latency_ms",0) or 0))
        rec.append(float(r.get("recall@k",0) or 0))
        mrr.append(float(r.get("mrr",0) or 0))
        ndc.append(float(r.get("ndcg",0) or 0))
    return {
        "latency_ms_mean": mean_safe(lat),
        "recall_k_mean":   mean_safe(rec),
        "mrr_mean":        mean_safe(mrr),
        "ndcg_mean":       mean_safe(ndc),
        # columnas opcionales que quizás no tengas (dejamos en 0.0)
        "rougel_mean":     0.0,
        "judge_score_mean":0.0,
        "judge_n_pairs":   0
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solr_csv",   required=True)
    ap.add_argument("--milvus_csv", required=True)
    ap.add_argument("--out_dir",    default="reports")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    solr_rows   = load_metrics(args.solr_csv)
    milvus_rows = load_metrics(args.milvus_csv)

    outp = os.path.join(args.out_dir, "final_report.csv")
    with open(outp, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["backend","latency_ms_mean","recall_k_mean","mrr_mean","ndcg_mean","rougel_mean","judge_n_pairs","judge_score_mean"])
        if solr_rows:
            a = agg_from_rows(solr_rows)
            w.writerow(["solr", a["latency_ms_mean"], a["recall_k_mean"], a["mrr_mean"], a["ndcg_mean"], a["rougel_mean"], a["judge_n_pairs"], a["judge_score_mean"]])
        else:
            print("[WARN] Solr sin filas")
        if milvus_rows:
            a = agg_from_rows(milvus_rows)
            w.writerow(["milvus", a["latency_ms_mean"], a["recall_k_mean"], a["mrr_mean"], a["ndcg_mean"], a["rougel_mean"], a["judge_n_pairs"], a["judge_score_mean"]])
        else:
            print("[WARN] Milvus sin filas")
    print(f"[OK] Final: {outp}")

if __name__ == "__main__":
    main()