"""Markdown report and figures from the scores table."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from fvsd.providers.base import UNITS  # noqa: E402
from fvsd.score import LAPSE_K_PER_KM, summarize  # noqa: E402
from fvsd.stations import REGIONS  # noqa: E402

VAR_TITLES = {"t2m": "2 m temperature", "precip": "Precipitation (hourly sum)", "wind": "10 m wind speed"}
FIG_SIZE = (16, 9)
FIG_DPI = 100

SOURCES = (
    "Observations: Source: MeteoSwiss, SwissMetNet hourly values (ogd-smn), "
    "https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn (open data, CC BY).",
    "Forecasts: Open-Meteo Previous Runs API, https://open-meteo.com/en/docs/previous-runs-api "
    "(CC BY 4.0, free for non-commercial use); models served: MeteoSwiss ICON-CH2 and ECMWF IFS 0.25 deg.",
)


def _fmt(x: float, nd: int = 2, signed: bool = False) -> str:
    if x is None or pd.isna(x):
        return "-"
    return f"{x:+.{nd}f}" if signed else f"{x:.{nd}f}"


def _md_table(header: list[str], rows: list[list[str]]) -> list[str]:
    text_cols = {"Provider", "Station", "Region"}
    aligns = "|".join("---" if h in text_cols else "---:" for h in header)
    out = ["| " + " | ".join(header) + " |", "|" + aligns + "|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return out


def headline_table(scores: pd.DataFrame, variable: str, leads: list[int] | None = None) -> list[str]:
    """Macro average over stations per provider and lead time."""
    summ = summarize(scores)
    summ = summ[summ["variable"] == variable]
    if leads is not None:
        summ = summ[summ["lead_h"].isin(leads)]
    unit = UNITS[variable]
    header = ["Provider", "Lead (h)", "Stations", f"Bias ({unit})", f"MAE ({unit})", f"RMSE ({unit})"]
    if variable == "t2m":
        header += ["MAE lapse-corr.", "RMSE lapse-corr."]
    rows = []
    for r in summ.itertuples():
        row = [r.provider, str(r.lead_h), str(r.stations), _fmt(r.bias, 2, True), _fmt(r.mae), _fmt(r.rmse)]
        if variable == "t2m":
            row += [_fmt(r.mae_lapse), _fmt(r.rmse_lapse)]
        rows.append(row)
    return _md_table(header, rows)


def station_table(scores: pd.DataFrame, provider: str, variable: str, lead_h: int) -> list[str]:
    s = scores[(scores["provider"] == provider) & (scores["variable"] == variable) & (scores["lead_h"] == lead_h)]
    s = s.sort_values("station_altitude_m")
    unit = UNITS[variable]
    header = ["Station", "Region", "Alt (m)"]
    if variable == "t2m":
        header += ["Grid (m)"]
    header += ["n", f"Bias ({unit})", f"MAE ({unit})", f"RMSE ({unit})"]
    if variable == "t2m":
        header += ["Bias lapse-corr.", "MAE lapse-corr."]
    rows = []
    for r in s.itertuples():
        row = [r.station, REGIONS.get(r.station, ""), f"{r.station_altitude_m:.0f}"]
        if variable == "t2m":
            row += [_fmt(r.grid_elevation_m, 0)]
        row += [str(r.n), _fmt(r.bias, 2, True), _fmt(r.mae), _fmt(r.rmse)]
        if variable == "t2m":
            row += [_fmt(r.bias_lapse, 2, True), _fmt(r.mae_lapse)]
        rows.append(row)
    return _md_table(header, rows)


def altitude_view(scores: pd.DataFrame, provider: str, lead_h: int) -> pd.DataFrame:
    """Per station: height difference grid - station, raw bias vs lapse-corrected bias."""
    s = scores[(scores["provider"] == provider) & (scores["variable"] == "t2m") & (scores["lead_h"] == lead_h)].copy()
    s["dz_m"] = s["grid_elevation_m"] - s["station_altitude_m"]
    return s.sort_values("dz_m").reset_index(drop=True)


def _label(station: str, alt: float) -> str:
    return f"{station} ({alt:.0f} m)"


def plot_bias_vs_lead(scores: pd.DataFrame, path: Path, variable: str = "t2m") -> Path:
    providers = sorted(scores.loc[scores["variable"] == variable, "provider"].unique())
    fig, axes = plt.subplots(1, max(len(providers), 1), figsize=FIG_SIZE, dpi=FIG_DPI, sharey=True, squeeze=False)
    stations = (
        scores[["station", "station_altitude_m"]].drop_duplicates().sort_values("station_altitude_m")
    )
    cmap = plt.get_cmap("tab10")
    colors = {s: cmap(i % 10) for i, s in enumerate(stations["station"])}
    unit = UNITS[variable]
    for ax, prov in zip(axes[0], providers, strict=False):
        sub = scores[(scores["provider"] == prov) & (scores["variable"] == variable) & (scores["n"] >= 24)]
        for st, alt in zip(stations["station"], stations["station_altitude_m"], strict=True):
            d = sub[sub["station"] == st].sort_values("lead_h")
            if d.empty:
                continue
            ax.plot(d["lead_h"], d["bias"], marker="o", lw=2, color=colors[st], label=_label(st, alt))
        ax.axhline(0, color="k", lw=1)
        ax.set_title(prov, fontsize=15)
        ax.set_xlabel("Lead time (h)", fontsize=13)
        ax.grid(alpha=0.3)
        ax.tick_params(labelsize=12)
    axes[0][0].set_ylabel(f"Bias, forecast minus station ({unit})", fontsize=13)
    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=5, fontsize=12, frameon=False)
    fig.suptitle(
        f"{VAR_TITLES[variable]}: forecast bias per station vs lead time (stations sorted by altitude)",
        fontsize=17,
    )
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)
    return path


def plot_altitude(scores: pd.DataFrame, path: Path, lead_h: int = 24) -> Path:
    providers = sorted(scores.loc[scores["variable"] == "t2m", "provider"].unique())
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=FIG_SIZE, dpi=FIG_DPI)
    markers = ["o", "s", "^", "D"]
    for i, prov in enumerate(providers):
        v = altitude_view(scores, prov, lead_h)
        v = v[v["n"] >= 24]
        if v.empty:
            continue
        ax1.scatter(v["dz_m"], v["bias"], marker=markers[i % 4], s=90, label=f"{prov}: raw")
        ax1.scatter(v["dz_m"], v["bias_lapse"], marker=markers[i % 4], s=90, facecolors="none",
                    edgecolors="k", label=f"{prov}: lapse-corrected")
        for r in v.itertuples():
            ax1.annotate(r.station, (r.dz_m, r.bias), fontsize=9, xytext=(4, 4), textcoords="offset points")
    zs = np.array([ax1.get_xlim()[0], ax1.get_xlim()[1]])
    ax1.plot(zs, -LAPSE_K_PER_KM / 1000.0 * zs, "r--", lw=1.5, label=f"-{LAPSE_K_PER_KM} K/km x dz")
    ax1.axhline(0, color="k", lw=1)
    ax1.set_xlabel("Grid height minus station height (m)", fontsize=13)
    ax1.set_ylabel("2 m temperature bias (K)", fontsize=13)
    ax1.set_title(f"Bias follows the height offset (lead {lead_h} h)", fontsize=15)
    ax1.legend(fontsize=10)
    ax1.grid(alpha=0.3)
    # right: MAE raw vs corrected, first provider with data per station
    width = 0.4
    for i, prov in enumerate(providers):
        v = altitude_view(scores, prov, lead_h)
        v = v[v["n"] >= 24]
        if v.empty or i > 0:
            continue
        x = np.arange(len(v))
        ax2.bar(x - width / 2, v["mae"], width, label="raw")
        ax2.bar(x + width / 2, v["mae_lapse"], width, label=f"lapse-corrected ({LAPSE_K_PER_KM} K/km)")
        ax2.set_xticks(x, v["station"], rotation=45)
        ax2.set_title(f"MAE per station, {prov}", fontsize=15)
    ax2.set_ylabel("2 m temperature MAE (K)", fontsize=13)
    if ax2.get_legend_handles_labels()[0]:
        ax2.legend(fontsize=11)
    ax2.grid(alpha=0.3, axis="y")
    fig.suptitle("Altitude error of a gridded forecast and what a lapse-rate correction recovers", fontsize=17)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)
    return path


def build_report(scores: pd.DataFrame, meta: dict) -> str:
    providers = sorted(scores["provider"].unique())
    lines = [
        "# Forecast vs station drift - results",
        "",
        f"Period (UTC): {meta.get('period_start')} to {meta.get('period_end')}. "
        f"Stations: {', '.join(meta.get('stations', []))}. "
        f"Forecast/observation pairs: {meta.get('n_pairs', 'n/a')}.",
        "",
        "error = forecast - observation. Lapse-corrected = forecast shifted from grid height to station "
        f"height with {meta.get('lapse_rate', LAPSE_K_PER_KM)} K/km.",
        "",
        "## 2 m temperature, mean over stations",
        "",
        *headline_table(scores, "t2m"),
        "",
    ]
    for var in ("precip", "wind"):
        if (scores["variable"] == var).any():
            lines += [f"## {VAR_TITLES[var]}, mean over stations", "", *headline_table(scores, var), ""]
    for prov in providers:
        leads = sorted(scores.loc[(scores["provider"] == prov) & (scores["variable"] == "t2m"), "lead_h"].unique())
        if not leads:
            continue
        lead = 24 if 24 in leads else leads[0]
        title = f"## 2 m temperature per station, {prov}, lead {lead} h"
        lines += [title, "", *station_table(scores, prov, "t2m", lead), ""]
    for var in ("precip", "wind"):
        for prov in providers:
            sub = scores[(scores["provider"] == prov) & (scores["variable"] == var) & (scores["lead_h"] == 24)]
            if not sub.empty:
                title = f"## {VAR_TITLES[var]} per station, {prov}, lead 24 h"
                lines += [title, "", *station_table(scores, prov, var, 24), ""]
    lines += ["## Sources", "", *[f"- {s}" for s in SOURCES], ""]
    return "\n".join(lines)


def write_report(scores_path: Path, out_dir: Path, docs_dir: Path) -> dict[str, Path]:
    scores = pd.read_parquet(scores_path)
    meta_path = scores_path.with_name("meta.json")
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    out_dir.mkdir(parents=True, exist_ok=True)
    report = out_dir / "report.md"
    report.write_text(build_report(scores, meta), encoding="utf-8")
    return {
        "report": report,
        "figure": plot_bias_vs_lead(scores, docs_dir / "figure.png"),
        "figure_altitude": plot_altitude(scores, docs_dir / "figure_altitude.png"),
    }
