import csv, os, argparse
import matplotlib.pyplot as plt

def read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def bar(ax, xs, ys, title, ylabel):
    ax.bar(xs, ys)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xticklabels(xs, rotation=15, ha="right")

def get(vals, key):
    out=[]
    for r in vals:
        try:
            out.append(float(r.get(key,0) or 0))
        except:
            out.append(0.0)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--final_csv", required=True)
    ap.add_argument("--out_dir",   default="reports")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    rows = read_rows(args.final_csv)
    if not rows:
        print("[WARN] final_report.csv sin filas; no se graficará")
        return

    backends = [r["backend"] for r in rows]

    plt.figure(figsize=(7,4))
    bar(plt.gca(), backends, get(rows, "latency_ms_mean"), "Latency (ms) — promedio", "ms")
    plt.tight_layout(); plt.savefig(os.path.join(args.out_dir,"final_latency.png")); plt.close()

    plt.figure(figsize=(7,4))
    bar(plt.gca(), backends, get(rows, "rougel_mean"), "ROUGE-L — promedio", "ROUGE-L")
    plt.tight_layout(); plt.savefig(os.path.join(args.out_dir,"final_rouge.png")); plt.close()

    plt.figure(figsize=(7,4))
    bar(plt.gca(), backends, get(rows, "judge_score_mean"), "LLM-as-a-judge — score medio", "score")
    plt.tight_layout(); plt.savefig(os.path.join(args.out_dir,"final_judge.png")); plt.close()

    print("[OK] Gráficos en", args.out_dir)

if __name__ == "__main__":
    main()