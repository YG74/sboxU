"""
Autoresearch Progress Analyzer — generates progress.png
"""
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")

def load_results(path="results.tsv"):
    df = pd.read_csv(path, sep="\t", comment="#")
    df["experiment"] = range(1, len(df) + 1)
    return df

def plot_progress(df, metric_col="total_time_ms", output="progress.png"):
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), dpi=150,
                              gridspec_kw={"height_ratios": [3, 1]})

    ax = axes[0]
    ax.set_title("sboxU Affine Equivalence — Optimization Timeline", fontsize=16, fontweight="bold")
    ax.set_xlabel("Experiment #")
    ax.set_ylabel("Total Time (ms)")

    # Discarded (gray)
    discarded = df[df["status"] == "discard"]
    if len(discarded) > 0:
        ax.scatter(discarded["experiment"], discarded[metric_col],
                   c="lightgray", s=40, zorder=2, label="Discarded", alpha=0.7)

    # Crashed (red X)
    crashed = df[df["status"] == "crash"]
    if len(crashed) > 0:
        ax.scatter(crashed["experiment"],
                   [df[metric_col].max() * 1.05] * len(crashed),
                   c="red", marker="x", s=60, zorder=2, label="Crash")

    # Kept (green, connected)
    kept = df[df["status"] == "keep"]
    if len(kept) > 0:
        ax.scatter(kept["experiment"], kept[metric_col],
                   c="#2ecc71", s=80, zorder=3, edgecolors="darkgreen",
                   linewidths=0.5, label="Kept")
        ax.plot(kept["experiment"], kept[metric_col],
                c="#2ecc71", linewidth=2, zorder=2, alpha=0.7)

        # Running best line
        running_best = kept[metric_col].cummin()
        ax.step(kept["experiment"], running_best,
                c="darkgreen", linewidth=1.5, linestyle="--", alpha=0.5,
                label="Best so far", where="post")

        # Annotate
        for _, row in kept.iterrows():
            desc = str(row["description"])[:40]
            ax.annotate(desc, xy=(row["experiment"], row[metric_col]),
                        xytext=(5, 10), textcoords="offset points",
                        fontsize=6, rotation=30, alpha=0.8,
                        arrowprops=dict(arrowstyle="-", alpha=0.3))

    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    # Baseline reference
    baseline = df.iloc[0][metric_col]
    ax.axhline(y=baseline, color="gray", linestyle=":", alpha=0.5)
    ax.text(0.02, baseline, f"  baseline: {baseline:.1f} ms",
            transform=ax.get_yaxis_transform(), fontsize=8, color="gray")

    # Bottom: per-benchmark breakdown
    ax2 = axes[1]
    ax2.set_title("Benchmark Breakdown (kept)")
    ax2.set_xlabel("Experiment #")
    ax2.set_ylabel("ms")

    bench_cols = [c for c in df.columns if c.endswith("_ms") and c != metric_col]
    colors = plt.cm.Set1(np.linspace(0, 1, max(len(bench_cols), 1)))

    if len(kept) > 0:
        for bench, color in zip(bench_cols, colors):
            if bench in kept.columns:
                ax2.plot(kept["experiment"], kept[bench], marker="o",
                         markersize=4, label=bench, color=color, linewidth=1.5)
        ax2.legend(loc="upper right", fontsize=8, ncol=3)
        ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output, bbox_inches="tight")
    print(f"Saved: {output}")

    # Summary
    total = len(df)
    n_keep = len(kept)
    n_discard = len(discarded)
    n_crash = len(crashed)
    print(f"\n=== SUMMARY ===")
    print(f"Experiments: {total} ({n_keep} kept, {n_discard} discarded, {n_crash} crashed)")
    if len(kept) > 1:
        improvement = (1 - kept[metric_col].min() / kept.iloc[0][metric_col]) * 100
        print(f"Baseline: {kept.iloc[0][metric_col]:.1f} ms → Best: {kept[metric_col].min():.1f} ms ({improvement:.1f}%)")

if __name__ == "__main__":
    plot_progress(load_results())
