"""Pair forecasts with observations and compute bias / MAE / RMSE.

Conventions
-----------
* error = forecast - observation, so a positive bias means the forecast is too high / too wet.
* MeteoSwiss hourly values are means (or sums) over the hour ENDING at the timestamp. Open-Meteo
  temperature and wind are instantaneous values, so they are converted to an
  hour mean by averaging the values at T-1h and T (trapezoid rule). Precipitation is already a
  sum over the preceding hour and is used as is.
* Lapse-rate correction (2 m temperature only): the model grid cell sits at height z_grid, the
  station at z_station, so T_station ~ T_grid + 6.5 K/km * (z_grid - z_station).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from fvsd.stations import Station

LAPSE_K_PER_KM = 6.5
INSTANT_VARIABLES = ("t2m", "wind")
KEYS = ["provider", "station", "variable", "lead_h"]


def hour_mean_forecast(fc: pd.DataFrame) -> pd.DataFrame:
    """Turn instantaneous t2m / wind forecasts into means over the hour ending at valid_time.

    A value needs its predecessor one hour earlier (same provider/station/variable/lead);
    rows without it are dropped.
    """
    inst = fc["variable"].isin(INSTANT_VARIABLES)
    cur = fc[inst]
    prev = cur[[*KEYS, "valid_time", "forecast"]].copy()
    prev["valid_time"] = prev["valid_time"] + pd.Timedelta(hours=1)
    prev = prev.rename(columns={"forecast": "forecast_prev"})
    merged = cur.merge(prev, on=[*KEYS, "valid_time"], how="inner")
    merged["forecast"] = (merged["forecast"] + merged["forecast_prev"]) / 2.0
    merged = merged.drop(columns="forecast_prev")
    return pd.concat([fc[~inst], merged], ignore_index=True)


def lapse_correct(
    forecast: pd.Series, grid_elevation_m: pd.Series, station_altitude_m: pd.Series,
    rate_k_per_km: float = LAPSE_K_PER_KM,
) -> pd.Series:
    """Shift a grid-height temperature to station height.

    NaN where the grid height is unknown or not plausible: a height <= 0 m is treated as missing,
    because no Swiss station is near sea level and Open-Meteo reports 0 m for ICON-CH2 lake cells
    (seen for Lugano), which would give a bogus correction of several kelvin.
    """
    grid = grid_elevation_m.where(grid_elevation_m > 0)
    return forecast + rate_k_per_km / 1000.0 * (grid - station_altitude_m)


def build_pairs(
    obs: pd.DataFrame,
    fc: pd.DataFrame,
    stations: dict[str, Station],
    *,
    hour_mean: bool = True,
    lapse_rate: float = LAPSE_K_PER_KM,
) -> pd.DataFrame:
    """Join forecasts to observations (station, variable, valid time) and add error columns."""
    f = hour_mean_forecast(fc) if hour_mean else fc.copy()
    pairs = f.merge(
        obs.rename(columns={"time": "valid_time"}),
        on=["station", "variable", "valid_time"],
        how="inner",
    )
    if pairs.empty:
        for col in ("station_altitude_m", "error", "error_lapse"):
            pairs[col] = pd.Series(dtype="float64")
        return pairs
    pairs["station_altitude_m"] = pairs["station"].map({a: s.altitude_m for a, s in stations.items()})
    pairs["error"] = pairs["forecast"] - pairs["obs"]
    is_t = pairs["variable"] == "t2m"
    corrected = lapse_correct(
        pairs["forecast"], pairs["grid_elevation_m"], pairs["station_altitude_m"], lapse_rate
    )
    pairs["error_lapse"] = np.where(is_t, corrected - pairs["obs"], np.nan)
    return pairs


def compute_metrics(pairs: pd.DataFrame, lead_bin: int = 1) -> pd.DataFrame:
    """Bias, MAE, RMSE per provider x station x variable x lead (hours, floored to `lead_bin`)."""
    if lead_bin < 1:
        raise ValueError("lead_bin must be >= 1")
    p = pairs.copy()
    p["lead_h"] = (p["lead_h"] // lead_bin) * lead_bin
    p["abs_error"] = p["error"].abs()
    p["sq_error"] = p["error"] ** 2
    p["abs_error_lapse"] = p["error_lapse"].abs()
    p["sq_error_lapse"] = p["error_lapse"] ** 2
    g = p.groupby(KEYS, sort=True)
    out = g.agg(
        n=("error", "size"),
        bias=("error", "mean"),
        mae=("abs_error", "mean"),
        mse=("sq_error", "mean"),
        bias_lapse=("error_lapse", "mean"),
        mae_lapse=("abs_error_lapse", "mean"),
        mse_lapse=("sq_error_lapse", "mean"),
        station_altitude_m=("station_altitude_m", "first"),
        grid_elevation_m=("grid_elevation_m", "mean"),
    ).reset_index()
    out["rmse"] = np.sqrt(out.pop("mse"))
    out["rmse_lapse"] = np.sqrt(out.pop("mse_lapse"))
    cols = [
        *KEYS, "n", "bias", "mae", "rmse", "bias_lapse", "mae_lapse", "rmse_lapse",
        "station_altitude_m", "grid_elevation_m",
    ]
    return out[cols]


def summarize(scores: pd.DataFrame, min_n: int = 24) -> pd.DataFrame:
    """Macro average over stations (each station counts once) per provider x variable x lead.

    For 2 m temperature only stations with a usable grid height are kept, so the raw and the
    lapse-corrected columns are averages over the same stations and can be compared directly.
    """
    s = scores[scores["n"] >= min_n].copy()
    s = s[(s["variable"] != "t2m") | s["mae_lapse"].notna()]
    s["abs_bias"] = s["bias"].abs()
    s["abs_bias_lapse"] = s["bias_lapse"].abs()
    g = s.groupby(["provider", "variable", "lead_h"], sort=True)
    out = g.agg(
        stations=("station", "nunique"),
        n=("n", "sum"),
        bias=("bias", "mean"),
        abs_bias=("abs_bias", "mean"),
        mae=("mae", "mean"),
        rmse=("rmse", "mean"),
        abs_bias_lapse=("abs_bias_lapse", "mean"),
        mae_lapse=("mae_lapse", "mean"),
        rmse_lapse=("rmse_lapse", "mean"),
    ).reset_index()
    return out
