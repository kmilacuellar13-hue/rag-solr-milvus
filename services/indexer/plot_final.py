# services/indexer/plot_final.py
import csv, os
import matplotlib.pyplot as plt

def read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def bar(ax, xs, ys, title, ylabel):
    ax.bar(xs, ys)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xticklabels(xs, rotation=15, ha="right")

def main():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--final_csv", required=True)
    ap.add_argument("--out_dir", default="reports")
    args=ap.parse_args()

    rows = read_rows(args.final_csv)
    backends = [r["backend"] for r in rows]
    lat = [float(r["latency_ms_mean"] or 0) for r in rows]
    rouge = [float(r["rougeL_mean"] or 0) for r in rows]
    judge = [float(r["judge_score_mean"] or 0) for r in rows]

    os.makedirs(args.out_dir, exist_ok=True)

    plt.figure(figsize=(7,4))
    bar(plt.gca(), backends, lat, "Latency (ms) — promedio", "ms")
    plt.tight_layout(); plt.savefig(os.path.join(args.out_dir, "final_latency.png")); plt.close()

    plt.figure(figsize=(7,4))
    bar(plt.gca(), backends, rouge, "ROUGE-L — promedio", "ROUGE-L")
    plt.tight_layout(); plt.savefig(os.path.join(args.out_dir, "final_rouge.png")); plt.close()

    plt.figure(figsize=(7,4))
    bar(plt.gca(), backends, judge, "LLM-as-a-judge — score medio", "score")
    plt.tight_layout(); plt.savefig(os.path.join(args.out_dir, "final_judge.png")); plt.close()

    print("[OK] Gráficos en", args.out_dir)

if __name__ == "__main__":
    main()