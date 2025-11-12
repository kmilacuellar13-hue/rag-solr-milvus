# services/indexer/summarize_metrics.py
import csv, json, os, argparse, statistics, glob

NUM_COLS = {
    "latency_ms": float,
    "recall@k":  float,
    "mrr":       float,
    "ndcg":      float,
    "rougeL":    float,
}

def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def safe_mean(values):
    vals = [v for v in values if v is not None]
    return (sum(vals)/len(vals)) if vals else 0.0

def to_num(v, cast):
    if v is None or v == "":
        return None
    try:
        return cast(v)
    except Exception:
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reports", default="reports")
    ap.add_argument("--out_prefix", default="summary")
    args = ap.parse_args()

    files = glob.glob(os.path.join(args.reports, "metrics_*.csv"))
    if not files:
        raise SystemExit(f"No se hallaron CSV de métricas en {args.reports} (metrics_*.csv)")

    by_backend = {}
    k_seen = None

    for fp in files:
        rows = read_csv(fp)
        for r in rows:
            b = r.get("backend","").strip()
            if not b:
                continue
            k_seen = k_seen or r.get("k") or r.get("K") or ""
            slot = by_backend.setdefault(b, {col: [] for col in NUM_COLS})
            for col, caster in NUM_COLS.items():
                slot[col].append(to_num(r.get(col), caster))

    summary_rows = []
    for b, cols in by_backend.items():
        out = {
            "backend": b,
            "k": k_seen if k_seen is not None else "",
            "recall_mean":     round(safe_mean(cols["recall@k"]), 4),
            "mrr_mean":        round(safe_mean(cols["mrr"]), 4),
            "ndcg_mean":       round(safe_mean(cols["ndcg"]), 4),
            "latency_ms_mean": round(safe_mean(cols["latency_ms"]), 1),
        }
        if any(v is not None for v in cols["rougeL"]):
            out["rougeL_mean"] = round(safe_mean(cols["rougeL"]), 4)
        summary_rows.append(out)

    json_out = os.path.join(args.reports, f"{args.out_prefix}.json")
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(summary_rows, f, indent=2, ensure_ascii=False)

    csv_out = os.path.join(args.reports, f"{args.out_prefix}.csv")
    fieldnames = ["backend","k","latency_ms_mean","recall_mean","mrr_mean","ndcg_mean","rougeL_mean"]
    with open(csv_out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in summary_rows:
            w.writerow({k: row.get(k,"") for k in fieldnames})

    print(f"[OK] Resúmenes en: {json_out} y {csv_out}")

if __name__ == "__main__":
    main()