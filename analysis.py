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


def short_desc(text, max_len=35):
    text = str(text)
    if len(text) > max_len:
        return text[:max_len - 1] + "…"
    return text


def plot_progress(df, metric_col="total_time_ms", output="progress.png"):
    baseline = df.iloc[0][metric_col]
    kept = df[df["status"] == "keep"].copy()
    kept["speedup"] = baseline / kept[metric_col]
    kept_running = kept[metric_col].cummin()

    fig, axes = plt.subplots(2, 1, figsize=(16, 11), dpi=150,
                             gridspec_kw={"height_ratios": [3.5, 1]})
    fig.patch.set_facecolor("white")

    # ---------- Top panel: total time timeline ----------
    ax = axes[0]
    ax.set_facecolor("white")
    ax.set_title("sboxU Affine Equivalence — Optimization Timeline", fontsize=18, fontweight="bold", pad=16)
    ax.set_xlabel("Experiment #", fontsize=12)
    ax.set_ylabel("Total Time (ms)", fontsize=12)
    ax.set_yscale("log")

    # Speedup twin axis
    ax_speedup = ax.twinx()
    ax_speedup.set_ylabel("Overall Speedup (×)", fontsize=12, color="darkgreen")
    ax_speedup.set_yscale("log")
    ax_speedup.tick_params(axis="y", labelcolor="darkgreen", labelsize=10)

    t_min = max(kept[metric_col].min() * 0.7, df[metric_col].replace(0, np.nan).min() * 0.7)
    t_max = df[metric_col].max() * 1.15
    ax.set_ylim(t_min, t_max)
    ax_speedup.set_ylim(baseline / t_max, baseline / t_min)
    ax_speedup.grid(False)

    # Discarded points
    discarded = df[df["status"] == "discard"]
    if len(discarded) > 0:
        ax.scatter(discarded["experiment"], discarded[metric_col],
                   c="#b0b0b0", s=45, zorder=2, label="Discarded", alpha=0.6, edgecolors="none")

    # Crashed points
    crashed = df[df["status"] == "crash"]
    if len(crashed) > 0:
        ax.scatter(crashed["experiment"],
                   [df[metric_col].max() * 1.08] * len(crashed),
                   c="red", marker="x", s=80, zorder=4, label="Crash", linewidths=2)

    # Kept points and line
    ax.scatter(kept["experiment"], kept[metric_col],
               c="#27ae60", s=100, zorder=4, edgecolors="#145a32", linewidths=1.2, label="Kept")
    ax.plot(kept["experiment"], kept[metric_col],
            c="#27ae60", linewidth=2, zorder=3, alpha=0.8)

    # Running best line
    ax.step(kept["experiment"], kept_running,
            c="#145a32", linewidth=2, linestyle="--", alpha=0.7,
            label="Best so far", where="post", zorder=3)

    # Baseline reference line
    ax.axhline(y=baseline, color="gray", linestyle=":", alpha=0.5, linewidth=1.5)
    ax.text(0.02, 0.96, f"baseline: {baseline:.1f} ms",
            transform=ax.transAxes, fontsize=9, color="gray", va="top", ha="left")

    # Milestone annotations (only major drops, skip baseline)
    milestones = []
    prev = baseline
    for _, row in kept.iterrows():
        val = row[metric_col]
        if row["experiment"] == 1:
            continue
        if val <= prev * 0.5:
            milestones.append(row)
            prev = val

    # Add final best as milestone
    if len(kept) > 0:
        best_row = kept.loc[kept[metric_col].idxmin()]
        if best_row["experiment"] not in [m["experiment"] for m in milestones]:
            milestones.append(best_row)

    for i, row in enumerate(milestones):
        exp = row["experiment"]
        val = row[metric_col]
        speedup = row["speedup"]
        desc = short_desc(row["description"], 32)

        # Alternate label placement to reduce overlap
        above = (i % 2 == 0)
        y_offset_desc = 18 if above else -18
        y_offset_speed = -16 if above else 16
        va_desc = "bottom" if above else "top"
        va_speed = "top" if above else "bottom"

        # Description label
        ax.annotate(desc,
                    xy=(exp, val),
                    xytext=(0, y_offset_desc),
                    textcoords="offset points",
                    fontsize=9,
                    ha="center",
                    va=va_desc,
                    alpha=0.9,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="none", alpha=0.8))

        # Speedup label
        ax.annotate(f"{speedup:.1f}×",
                    xy=(exp, val),
                    xytext=(0, y_offset_speed),
                    textcoords="offset points",
                    fontsize=9,
                    ha="center",
                    va=va_speed,
                    color="darkgreen",
                    fontweight="bold",
                    alpha=0.9)

    ax.legend(loc="lower left", fontsize=10, framealpha=0.95)
    ax.grid(True, alpha=0.25, which="both", linestyle="-")
    ax.tick_params(axis="both", labelsize=10)

    # Summary text box
    final_best = kept[metric_col].min()
    final_speedup = baseline / final_best
    summary_text = (
        f"Baseline: {baseline:.1f} ms\n"
        f"Best: {final_best:.3f} ms\n"
        f"Speedup: {final_speedup:,.0f}×\n"
        f"({(1 - final_best / baseline) * 100:.1f}% faster)"
    )
    ax.text(0.98, 0.98, summary_text,
            transform=ax.transAxes,
            fontsize=11,
            verticalalignment="top",
            horizontalalignment="right",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#f8f9fa", edgecolor="#27ae60", linewidth=1.5, alpha=0.95))

    # ---------- Bottom panel: per-benchmark breakdown ----------
    ax2 = axes[1]
    ax2.set_facecolor("white")
    ax2.set_title("Benchmark Breakdown (kept experiments)", fontsize=13, pad=10)
    ax2.set_xlabel("Experiment #", fontsize=12)
    ax2.set_ylabel("Time (ms, log scale)", fontsize=12)
    ax2.set_yscale("log")

    bench_cols = [c for c in df.columns if c.endswith("_ms") and c != metric_col]
    labels = {
        "aes_self_ms": "AES self-equiv",
        "random_self_ms": "Random self-equiv",
        "random_nonequiv_ms": "Random non-equivalent",
    }
    colors = {"aes_self_ms": "#e74c3c", "random_self_ms": "#f39c12", "random_nonequiv_ms": "#7f8c8d"}

    if len(kept) > 0:
        for bench in bench_cols:
            if bench in kept.columns:
                label = labels.get(bench, bench)
                color = colors.get(bench, None)
                ax2.plot(kept["experiment"], kept[bench], marker="o",
                         markersize=5, label=label, color=color, linewidth=1.8)
        ax2.legend(loc="upper right", fontsize=10, ncol=3, framealpha=0.95)
        ax2.grid(True, alpha=0.25)
        ax2.tick_params(axis="both", labelsize=10)

    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    plt.savefig(output, bbox_inches="tight", facecolor="white")
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
