# services/indexer/merge_reports.py
import csv, sys, os
import statistics as st

def read_csv(path):
    rows=[]
    if not os.path.exists(path):
        print(f"[WARN] No existe {path}")
        return rows
    with open(path, encoding="utf-8-sig", newline="") as f:
        r=csv.DictReader(f)
        for row in r:
            rows.append({k.strip(): v.strip() for k,v in row.items()})
    return rows

def main():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--metrics_csv", required=True)         # reports/summary.csv
    ap.add_argument("--rouge_csv", required=True)           # reports/rouge_by_backend.csv
    ap.add_argument("--judge_csv", required=True)           # reports/llm_judge_summary.csv
    ap.add_argument("--out_dir",   default="reports")
    args=ap.parse_args()

    metrics = read_csv(args.metrics_csv)
    rouge   = read_csv(args.rouge_csv)
    judge   = read_csv(args.judge_csv)

    # Latencia media por backend (desde summary.csv)
    lat_by_backend = {}
    for r in metrics:
        b = r.get("backend","").strip()
        try:
            lat = float(r.get("latency_ms","") or r.get("latency_ms_mean","") or 0)
        except:
            lat = 0.0
        lat_by_backend.setdefault(b, []).append(lat)
    lat_mean = {b: (sum(v)/len(v) if v else 0.0) for b,v in lat_by_backend.items()}

    # ROUGE-L por backend
    rouge_idx = {}
    for r in rouge:
        b = r.get("backend","").strip()
        rouge_idx[b] = {
            "rougeL_mean":   float(r.get("rougeL_mean", 0)   or 0),
            "rougeL_median": float(r.get("rougeL_median", 0) or 0)
        }

    # LLM-as-a-judge por backend
    judge_idx = {}
    for r in judge:
        b = r.get("backend","").strip()
        judge_idx[b] = {
            "judge_n_pairs": int(float(r.get("n_pairs", 0) or 0)),
            "judge_score_mean": float(r.get("score_mean", 0) or 0)
        }

    # Backends presentes en cualquiera de las fuentes
    backends = set(list(lat_mean.keys()) + list(rouge_idx.keys()) + list(judge_idx.keys()))
    outp = os.path.join(args.out_dir, "final_report.csv")
    os.makedirs(args.out_dir, exist_ok=True)
    with open(outp, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["backend","latency_ms_mean","rougeL_mean","rougeL_median","judge_n_pairs","judge_score_mean"])
        for b in sorted(backends):
            w.writerow([
                b,
                round(lat_mean.get(b, 0.0), 2),
                round(rouge_idx.get(b,{}).get("rougeL_mean", 0.0), 4),
                round(rouge_idx.get(b,{}).get("rougeL_median", 0.0), 4),
                judge_idx.get(b,{}).get("judge_n_pairs", 0),
                round(judge_idx.get(b,{}).get("judge_score_mean", 0.0), 4),
            ])
    print(f"[OK] Final: {outp}")

if __name__ == "__main__":
    main()