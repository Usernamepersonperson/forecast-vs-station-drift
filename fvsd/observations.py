"""MeteoSwiss SwissMetNet hourly observations from the federal open-data STAC.

Collection: https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn
Files:      https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/<abbr>/ogd-smn_<abbr>_h_<period>.csv
Source: MeteoSwiss (open data, the source must be cited).

Timestamps are UTC and mark the END of the hourly interval (mean of the last six 10-minute values).
"""

from __future__ import annotations

import io
from datetime import date

import pandas as pd

BASE_URL = "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn"

# our variable -> MeteoSwiss parameter id (hourly)
OBS_PARAMS = {"t2m": "tre200h0", "precip": "rre150h0", "wind": "fkl010h0"}

OBS_COLUMNS = ["station", "variable", "time", "obs"]


def obs_urls(abbr: str, start: date, end: date, today: date | None = None) -> list[str]:
    """URLs of the hourly files covering [start, end].

    Years before the current one live in 10-year `historical` files, the current year up to
    yesterday in `recent` (the `now` file only holds the last ~36 h and is not used).
    """
    if end < start:
        raise ValueError("end before start")
    today = today or date.today()
    low = abbr.lower()
    urls: list[str] = []
    decades = sorted({y // 10 * 10 for y in range(start.year, end.year + 1) if y < today.year})
    for d in decades:
        urls.append(f"{BASE_URL}/{low}/ogd-smn_{low}_h_historical_{d}-{d + 9}.csv")
    if end.year >= today.year:
        urls.append(f"{BASE_URL}/{low}/ogd-smn_{low}_h_recent.csv")
    return urls


def parse_obs_csv(text: str, variables: tuple[str, ...] = tuple(OBS_PARAMS)) -> pd.DataFrame:
    """Parse one MeteoSwiss hourly CSV into long layout (station, variable, time, obs)."""
    wanted = {OBS_PARAMS[v]: v for v in variables}
    df = pd.read_csv(io.StringIO(text), sep=";", dtype=str)
    need = {"station_abbr", "reference_timestamp"}
    if not need <= set(df.columns):
        raise ValueError(
            f"unexpected observation file, missing columns {sorted(need - set(df.columns))}"
        )
    time = pd.to_datetime(df["reference_timestamp"], format="%d.%m.%Y %H:%M")
    frames = []
    for pid, var in wanted.items():
        if pid not in df.columns:
            continue
        part = pd.DataFrame(
            {
                "station": df["station_abbr"],
                "variable": var,
                "time": time,
                "obs": pd.to_numeric(df[pid], errors="coerce"),
            }
        ).dropna(subset=["obs"])
        frames.append(part)
    if not frames:
        return pd.DataFrame(columns=OBS_COLUMNS)
    return pd.concat(frames, ignore_index=True)[OBS_COLUMNS]


def clip_window(df: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    """Keep start 00:00 < time <= end+1 day 00:00 (UTC): hourly values ending inside whole days."""
    lo = pd.Timestamp(start)
    hi = pd.Timestamp(end) + pd.Timedelta(days=1)
    return df[(df["time"] > lo) & (df["time"] <= hi)].reset_index(drop=True)
