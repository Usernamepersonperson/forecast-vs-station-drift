"""Command line: python -m fvsd fetch | score | report."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from fvsd import __version__
from fvsd.http import cached_get, http_get
from fvsd.observations import OBS_COLUMNS, clip_window, obs_urls, parse_obs_csv
from fvsd.providers.base import FORECAST_COLUMNS, VARIABLES
from fvsd.providers.openmeteo import DEFAULT_LEAD_DAYS, FALLBACK_LEAD_DAYS, OpenMeteoProvider
from fvsd.report import write_report
from fvsd.score import LAPSE_K_PER_KM, build_pairs, compute_metrics
from fvsd.stations import (
    DEFAULT_STATIONS,
    META_URL,
    Station,
    decode_text,
    parse_station_meta,
    select_stations,
)

DEFAULT_MODELS = ("meteoswiss_icon_ch2", "ecmwf_ifs025")
FORECAST_KEY = ["provider", "station", "variable", "valid_time", "lead_h"]


def _date(s: str) -> date:
    try:
        return date.fromisoformat(s)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"not an ISO date: {s}") from exc


def _csv_list(s: str) -> list[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="fvsd", description=__doc__)
    p.add_argument("--version", action="version", version=f"fvsd {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="download observations and forecasts into the cache")
    f.add_argument("--start", type=_date, default=None, help="first UTC day (default: 92 days before end)")
    f.add_argument("--end", type=_date, default=None, help="last UTC day (default: 2 days ago)")
    f.add_argument("--stations", type=_csv_list, default=list(DEFAULT_STATIONS))
    f.add_argument("--providers", type=_csv_list, default=["open-meteo"],
                   help="forecast providers (currently: open-meteo)")
    f.add_argument("--models", type=_csv_list, default=list(DEFAULT_MODELS), help="Open-Meteo model ids")
    f.add_argument("--variables", type=_csv_list, default=list(VARIABLES))
    f.add_argument("--cache", type=Path, default=Path("cache"))

    s = sub.add_parser("score", help="pair forecasts with observations, write scores.parquet")
    s.add_argument("--cache", type=Path, default=Path("cache"))
    s.add_argument("--out", type=Path, default=Path("results"))
    s.add_argument("--lead-bin", type=int, default=1, help="floor lead times to multiples of N hours")
    s.add_argument("--lapse-rate", type=float, default=LAPSE_K_PER_KM, help="K/km")

    r = sub.add_parser("report", help="write report.md and figures from scores.parquet")
    r.add_argument("--scores", type=Path, default=Path("results/scores.parquet"))
    r.add_argument("--out", type=Path, default=Path("results"))
    r.add_argument("--docs", type=Path, default=Path("docs"))
    return p


def _load_stations(cache: Path, abbrs: Sequence[str], getter=http_get) -> list[Station]:
    text = decode_text(cached_get(META_URL, cache / "obs" / "ogd-smn_meta_stations.csv", getter))
    return select_stations(parse_station_meta(text), abbrs)


def _save_merge(path: Path, new: pd.DataFrame, key: list[str]) -> pd.DataFrame:
    if path.exists():
        new = pd.concat([pd.read_parquet(path), new], ignore_index=True)
    new = new.drop_duplicates(subset=key, keep="last").reset_index(drop=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    new.to_parquet(path, index=False)
    return new


def cmd_fetch(args, getter=http_get) -> int:
    end = args.end or (date.today() - timedelta(days=2))
    start = args.start or (end - timedelta(days=91))
    if end < start:
        print("error: --end is before --start", file=sys.stderr)
        return 2
    unknown = set(args.providers) - {"open-meteo"}
    if unknown:
        print(f"error: unknown provider(s): {', '.join(sorted(unknown))}", file=sys.stderr)
        return 2
    stations = _load_stations(args.cache, args.stations, getter)
    variables = tuple(args.variables)

    obs_frames = []
    for st in stations:
        for url in obs_urls(st.abbr, start, end):
            body = cached_get(url, args.cache / "obs" / url.rsplit("/", 1)[-1], getter)
            obs_frames.append(clip_window(parse_obs_csv(decode_text(body), variables), start, end))
        print(f"observations {st.abbr}: ok", file=sys.stderr)
    obs = pd.concat(obs_frames, ignore_index=True) if obs_frames else pd.DataFrame(columns=OBS_COLUMNS)
    _save_merge(args.cache / "observations.parquet", obs, ["station", "variable", "time"])
    _save_merge(
        args.cache / "stations.parquet",
        pd.DataFrame([s.__dict__ for s in stations]),
        ["abbr"],
    )

    forecasts = []
    if "open-meteo" in args.providers:
        for model in args.models:
            days = DEFAULT_LEAD_DAYS.get(model, FALLBACK_LEAD_DAYS)
            prov = OpenMeteoProvider(model, cache_dir=args.cache, http_get_fn=getter)
            for st in stations:
                forecasts.append(prov.fetch(st, start, end, variables, [d * 24 for d in days]))
                print(f"{prov.name} {st.abbr}: ok", file=sys.stderr)
    if forecasts:
        fc = pd.concat([f for f in forecasts if not f.empty] or [pd.DataFrame(columns=FORECAST_COLUMNS)],
                       ignore_index=True)
        _save_merge(args.cache / "forecasts.parquet", fc, FORECAST_KEY)
    return 0


def cmd_score(args) -> int:
    cache: Path = args.cache
    needed = [cache / "observations.parquet", cache / "forecasts.parquet", cache / "stations.parquet"]
    missing = [str(p) for p in needed if not p.exists()]
    if missing:
        print(f"error: run `fvsd fetch` first, missing {', '.join(missing)}", file=sys.stderr)
        return 2
    obs = pd.read_parquet(needed[0])
    fc = pd.read_parquet(needed[1])
    stations = {s.abbr: s for s in (Station(**r) for r in pd.read_parquet(needed[2]).to_dict("records"))}
    pairs = build_pairs(obs, fc, stations, lapse_rate=args.lapse_rate)
    if pairs.empty:
        print("error: no forecast/observation pairs; check that the date ranges overlap", file=sys.stderr)
        return 2
    scores = compute_metrics(pairs, lead_bin=args.lead_bin)
    args.out.mkdir(parents=True, exist_ok=True)
    scores.to_parquet(args.out / "scores.parquet", index=False)
    meta = {
        "period_start": str(pairs["valid_time"].min().date()),
        "period_end": str(pairs["valid_time"].max().date()),
        "stations": sorted(pairs["station"].unique()),
        "providers": sorted(pairs["provider"].unique()),
        "n_pairs": int(len(pairs)),
        "lapse_rate": args.lapse_rate,
        "lead_bin": args.lead_bin,
    }
    (args.out / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"scored {len(pairs)} pairs -> {args.out / 'scores.parquet'}", file=sys.stderr)
    return 0


def cmd_report(args) -> int:
    if not args.scores.exists():
        print(f"error: {args.scores} not found, run `fvsd score` first", file=sys.stderr)
        return 2
    paths = write_report(args.scores, args.out, args.docs)
    for k, v in paths.items():
        print(f"{k}: {v}", file=sys.stderr)
    return 0


def main(argv: Sequence[str] | None = None, getter=http_get) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "fetch":
        return cmd_fetch(args, getter)
    return {"score": cmd_score, "report": cmd_report}[args.cmd](args)
