import numpy as np
import pandas as pd
import pytest
from conftest import make_fc, make_obs

from fvsd.score import (
    build_pairs,
    compute_metrics,
    hour_mean_forecast,
    lapse_correct,
    summarize,
)


def test_hour_mean_averages_t_and_previous_hour():
    fc = make_fc([10.0, 12.0, 20.0])
    out = hour_mean_forecast(fc).sort_values("valid_time").reset_index(drop=True)
    assert list(out["forecast"]) == [11.0, 16.0]  # first hour has no predecessor and is dropped
    assert out["valid_time"].iloc[0] == pd.Timestamp("2026-01-01 01:00")


def test_hour_mean_leaves_precip_alone():
    fc = make_fc([1.0, 2.0, 3.0], variable="precip")
    assert list(hour_mean_forecast(fc)["forecast"]) == [1.0, 2.0, 3.0]


def test_hour_mean_needs_consecutive_hours():
    fc = make_fc([10.0, 12.0, 20.0, 22.0]).drop(index=1)  # hour 01 missing
    out = hour_mean_forecast(fc)
    assert list(out["forecast"]) == [21.0]


def test_hour_mean_keeps_leads_apart():
    fc = pd.concat([make_fc([0.0, 2.0], lead_h=24), make_fc([10.0, 20.0], lead_h=48)])
    out = hour_mean_forecast(fc).set_index("lead_h")["forecast"]
    assert out[24] == 1.0 and out[48] == 15.0


def test_lapse_correct_known_answer():
    f = pd.Series([10.0])
    # grid 100 m above the station: station is warmer by 0.65 K
    assert lapse_correct(f, pd.Series([700.0]), pd.Series([600.0]))[0] == pytest.approx(10.65)
    # grid below the station: colder
    assert lapse_correct(f, pd.Series([500.0]), pd.Series([600.0]))[0] == pytest.approx(9.35)


def test_lapse_correct_custom_rate():
    out = lapse_correct(pd.Series([0.0]), pd.Series([1100.0]), pd.Series([100.0]), rate_k_per_km=5.0)
    assert out[0] == pytest.approx(5.0)


def test_lapse_correct_nan_and_zero_grid_are_missing():
    out = lapse_correct(pd.Series([5.0, 5.0]), pd.Series([np.nan, 0.0]), pd.Series([600.0, 600.0]))
    assert out.isna().all()


def test_build_pairs_bias_and_lapse_columns(stations):
    fc = make_fc([10.0, 10.0, 10.0], grid=700.0)  # hour means all 10
    obs = make_obs([9.0, 9.0, 9.0])
    p = build_pairs(obs, fc, stations)
    assert len(p) == 2  # first hour dropped by the hour-mean step
    assert (p["error"] == 1.0).all()
    # station 604 m, grid 700 m -> +0.624 K at the station, error 1.624
    assert p["error_lapse"].iloc[0] == pytest.approx(10 + 0.0065 * 96 - 9.0)


def test_build_pairs_no_hour_mean_keeps_all_rows(stations):
    p = build_pairs(make_obs([1.0, 2.0, 3.0]), make_fc([1.0, 2.0, 3.0]), stations, hour_mean=False)
    assert len(p) == 3 and (p["error"] == 0).all()


def test_build_pairs_lapse_only_for_temperature(stations):
    fc = make_fc([1.0, 1.0, 1.0], variable="wind")
    p = build_pairs(make_obs([0.0, 0.0, 0.0], variable="wind"), fc, stations)
    assert p["error_lapse"].isna().all()


def test_build_pairs_inner_join_on_station_and_time(stations):
    fc = make_fc([1.0, 1.0, 1.0], station="SMA")
    obs = make_obs([1.0, 1.0, 1.0], station="JUN")
    assert build_pairs(obs, fc, stations).empty


def test_compute_metrics_known_answer(stations):
    fc = make_fc([1.0, 2.0, 3.0, 4.0], variable="precip", grid=np.nan)
    obs = make_obs([0.0, 4.0, 3.0, 2.0], variable="precip")
    m = compute_metrics(build_pairs(obs, fc, stations))
    r = m.iloc[0]
    # errors: +1, -2, 0, +2
    assert r["n"] == 4
    assert r["bias"] == pytest.approx(0.25)
    assert r["mae"] == pytest.approx(1.25)
    assert r["rmse"] == pytest.approx(np.sqrt((1 + 4 + 0 + 4) / 4))
    assert np.isnan(r["bias_lapse"])


def test_compute_metrics_groups_by_lead_and_station(stations):
    fc = pd.concat([make_fc([2.0] * 4, lead_h=24), make_fc([3.0] * 4, lead_h=48)])
    obs = make_obs([1.0] * 4)
    m = compute_metrics(build_pairs(obs, fc, stations)).set_index("lead_h")
    assert m.loc[24, "bias"] == 1.0 and m.loc[48, "bias"] == 2.0


def test_compute_metrics_lead_bin(stations):
    fc = pd.concat([make_fc([1.0] * 3, lead_h=24), make_fc([1.0] * 3, lead_h=30), make_fc([1.0] * 3, lead_h=50)])
    m = compute_metrics(build_pairs(make_obs([0.0] * 3), fc, stations), lead_bin=24)
    assert sorted(m["lead_h"]) == [24, 48]
    assert m.set_index("lead_h").loc[24, "n"] == 4  # 2 + 2 pairs after hour-mean


def test_compute_metrics_rejects_bad_bin(stations):
    p = build_pairs(make_obs([0.0] * 3), make_fc([0.0] * 3), stations)
    with pytest.raises(ValueError):
        compute_metrics(p, lead_bin=0)


def test_lapse_correction_removes_pure_altitude_bias(stations):
    # a "forecast" that is the truth shifted only by the grid height offset
    obs = make_obs([10.0] * 6)
    grid = 1604.0  # 1000 m above the station
    fc = make_fc([10.0 - 6.5] * 6, grid=grid)
    m = compute_metrics(build_pairs(obs, fc, stations)).iloc[0]
    assert m["bias"] == pytest.approx(-6.5)
    assert m["bias_lapse"] == pytest.approx(0.0, abs=1e-9)
    assert m["mae_lapse"] < m["mae"]


def test_summarize_is_station_macro_average_and_respects_min_n(stations):
    base = {"provider": "p", "variable": "t2m", "lead_h": 24, "rmse": 1.0, "bias_lapse": 0.0,
            "mae_lapse": 0.5, "rmse_lapse": 0.6, "station_altitude_m": 1.0, "grid_elevation_m": 1.0}
    scores = pd.DataFrame(
        [
            {**base, "station": "A", "n": 100, "bias": 1.0, "mae": 1.0},
            {**base, "station": "B", "n": 10000, "bias": -3.0, "mae": 3.0},
            {**base, "station": "C", "n": 5, "bias": 50.0, "mae": 50.0},  # too few pairs
        ]
    )
    s = summarize(scores, min_n=24).iloc[0]
    assert s["stations"] == 2
    assert s["bias"] == pytest.approx(-1.0)
    assert s["abs_bias"] == pytest.approx(2.0)
    assert s["mae"] == pytest.approx(2.0)


def test_summarize_t2m_only_pairs_stations_with_lapse_values():
    base = {"provider": "p", "variable": "t2m", "lead_h": 24, "n": 100, "rmse": 1.0, "bias_lapse": 0.0,
            "rmse_lapse": 0.6, "station_altitude_m": 1.0, "grid_elevation_m": 1.0}
    scores = pd.DataFrame(
        [
            {**base, "station": "A", "bias": 1.0, "mae": 1.0, "mae_lapse": 0.5},
            {**base, "station": "B", "bias": 1.0, "mae": 9.0, "mae_lapse": float("nan")},
        ]
    )
    s = summarize(scores).iloc[0]
    assert s["stations"] == 1 and s["mae"] == pytest.approx(1.0)
