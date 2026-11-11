"""Write docs/post-figure.png (960x700, dark) from results/scores.parquet."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BG, GRID, TEXT, MUTED = "#16213A", "#2A3750", "#F8FAFC", "#A9B6CB"
ACCENT, GREEN, AMBER = "#38BDF8", "#34D399", "#FBBF24"
plt.rcParams["font.family"] = ["Segoe UI", "DejaVu Sans"]


def main() -> None:
    s = pd.read_parquet(ROOT / "results" / "scores.parquet")
    t = s[(s["variable"] == "t2m") & s["mae_lapse"].notna()]
    out = {}
    for prov, g in t.groupby("provider"):
        g = g[g["lead_h"].isin([24, 48, 72, 96])]
        out[prov] = g.groupby("lead_h")[["mae", "mae_lapse"]].mean()
    fig, ax = plt.subplots(figsize=(9.6, 7.0), dpi=100, facecolor=BG)
    fig.subplots_adjust(left=0.10, right=0.96, top=0.74, bottom=0.14)
    ax.set_facecolor(BG)
    styles = {
        "open-meteo/ecmwf_ifs025": ("ECMWF IFS (25 km)", AMBER),
        "open-meteo/meteoswiss_icon_ch2": ("ICON-CH2 (2 km)", ACCENT),
    }
    for prov, (label, col) in styles.items():
        d = out[prov]
        ax.plot(d.index, d["mae"], color=col, lw=3.5, marker="o", ms=8, label=f"{label}, raw")
        ax.plot(d.index, d["mae_lapse"], color=col, lw=3.5, ls="--", marker="o", ms=8,
                label=f"{label}, height-corrected")
    ax.set_xticks([24, 48, 72, 96])
    ax.set_xlabel("Forecast lead time (hours)", color=MUTED, fontsize=15)
    ax.set_ylabel("2 m temperature error, MAE (K)", color=MUTED, fontsize=15)
    ax.set_ylim(0, 3.6)
    ax.grid(color=GRID, lw=1)
    ax.tick_params(colors=TEXT, labelsize=15)
    for sp in ax.spines.values():
        sp.set_color(GRID)
    leg = ax.legend(loc="lower right", fontsize=15, facecolor=BG, edgecolor=GRID, labelcolor=TEXT)
    leg.get_frame().set_alpha(0.9)
    fig.text(0.04, 0.93, "Station height matters more than model skill", color=TEXT, fontsize=19,
             fontweight="bold", ha="left")
    fig.text(0.04, 0.885, "Open data: MeteoSwiss stations, Open-Meteo forecasts, Aug-Oct 2026",
             color=MUTED, fontsize=15, ha="left")
    fig.text(0.04, 0.83, "Dashed = forecast shifted from grid height to station height (6.5 K/km)",
             color=MUTED, fontsize=15, ha="left")
    fig.savefig(ROOT / "docs" / "post-figure.png", facecolor=BG)


if __name__ == "__main__":
    main()
