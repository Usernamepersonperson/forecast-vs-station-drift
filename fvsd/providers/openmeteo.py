"""Open-Meteo Previous Runs API adapter (no account, no key).

Docs: https://open-meteo.com/en/docs/previous-runs-api

`<var>_previous_day<N>` is "the value that was predicted N*24 hours before valid time", so lead
times are multiples of 24 h. `elevation=nan` switches off Open-Meteo's own height downscaling,
so the value is the raw grid-cell value and `elevation` in the response is the grid-cell height.

Open-Meteo data is free for non-commercial use with attribution (CC BY 4.0); see their terms.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd

from fvsd.http import Getter, cached_get, http_get
from fvsd.providers.base import FORECAST_COLUMNS, ForecastProvider, empty_forecast
from fvsd.stations import Station

BASE_URL = "https://previous-runs-api.open-meteo.com/v1/forecast"

VAR_MAP = {"t2m": "temperature_2m", "precip": "precipitation", "wind": "wind_speed_10m"}

# Lead days with data in the archive (checked 2026-11-08 for Aug-Oct 2026).
DEFAULT_LEAD_DAYS = {
    "meteoswiss_icon_ch2": (1, 2, 3, 4),
    "ecmwf_ifs025": (1, 2, 3, 4, 5, 6, 7),
}
FALLBACK_LEAD_DAYS = (1, 2, 3)


def lead_hours_to_days(leads_h: Sequence[int]) -> list[int]:
    days = []
    for h in leads_h:
        if h % 24 != 0 or not 24 <= h <= 168:
            raise ValueError(f"Open-Meteo previous runs only offer lead times 24..168 h in 24 h steps, got {h}")
        days.append(h // 24)
    return days


class OpenMeteoProvider(ForecastProvider):
    def __init__(
        self,
        model: str = "meteoswiss_icon_ch2",
        *,
        cache_dir: Path | None = None,
        http_get_fn: Getter = http_get,
    ) -> None:
        self.model = model
        self.name = f"open-meteo/{model}"
        self.cache_dir = cache_dir
        self._get = http_get_fn

    def build_url(
        self, station: Station, start: date, end: date, variables: Sequence[str], days: Sequence[int]
    ) -> str:
        names = [f"{VAR_MAP[v]}_previous_day{d}" for v in variables for d in days]
        query = {
            "latitude": f"{station.lat:.5f}",
            "longitude": f"{station.lon:.5f}",
            "hourly": ",".join(names),
            "models": self.model,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "timezone": "UTC",
            "wind_speed_unit": "ms",
            "elevation": "nan",
        }
        return f"{BASE_URL}?{urlencode(query, safe=',')}"

    def parse(self, body: bytes | str, station: Station, variables: Sequence[str],
              days: Sequence[int]) -> pd.DataFrame:
        payload = json.loads(body)
        if "hourly" not in payload:
            raise RuntimeError(f"Open-Meteo error: {payload.get('reason', payload)}")
        hourly = payload["hourly"]
        grid = payload.get("elevation")
        times = pd.to_datetime(hourly["time"])
        frames = []
        for v in variables:
            for d in days:
                key = f"{VAR_MAP[v]}_previous_day{d}"
                if key not in hourly:
                    continue
                part = pd.DataFrame(
                    {
                        "provider": self.name,
                        "station": station.abbr,
                        "variable": v,
                        "valid_time": times,
                        "lead_h": d * 24,
                        "forecast": pd.to_numeric(pd.Series(hourly[key]), errors="coerce"),
                        "grid_elevation_m": float(grid) if grid is not None else float("nan"),
                    }
                ).dropna(subset=["forecast"])
                frames.append(part)
        if not frames:
            return empty_forecast()
        return pd.concat(frames, ignore_index=True)[FORECAST_COLUMNS]

    def fetch(self, station, start, end, variables, leads_h) -> pd.DataFrame:
        days = lead_hours_to_days(leads_h)
        url = self.build_url(station, start, end, variables, days)
        if self.cache_dir is not None:
            tag = f"{self.model}_{station.abbr}_{start}_{end}_{'-'.join(variables)}_d{'-'.join(map(str, days))}"
            body = cached_get(url, self.cache_dir / "openmeteo" / f"{tag}.json", self._get)
        else:
            body = self._get(url, None)
        return self.parse(body, station, variables, days)
