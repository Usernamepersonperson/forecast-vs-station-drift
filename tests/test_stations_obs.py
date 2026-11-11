from datetime import date

import pandas as pd
import pytest

from fvsd.observations import BASE_URL, clip_window, obs_urls, parse_obs_csv
from fvsd.stations import DEFAULT_STATIONS, REGIONS, decode_text, parse_station_meta, select_stations


def test_default_stations_are_ten_and_have_regions():
    assert len(DEFAULT_STATIONS) == 10
    assert set(DEFAULT_STATIONS) <= set(REGIONS)


def test_parse_station_meta_cp1252(fixtures):
    meta = parse_station_meta(decode_text((fixtures / "stations_meta.csv").read_bytes()))
    assert set(meta) == {"SMA", "SAE", "JUN"}
    assert meta["JUN"].altitude_m == 3571.0
    assert meta["SMA"].lat == pytest.approx(47.381003)
    assert "ntis" in meta["SAE"].name  # umlaut decoded, not mojibake


def test_decode_text_prefers_utf8():
    assert decode_text("Zürich".encode()) == "Zürich"
    assert decode_text("Zürich".encode("cp1252")) == "Zürich"


def test_parse_station_meta_rejects_wrong_file():
    with pytest.raises(ValueError):
        parse_station_meta("a;b\n1;2\n")


def test_parse_station_meta_skips_rows_without_coordinates():
    text = (
        "station_abbr;station_name;station_height_masl;station_coordinates_wgs84_lat;"
        "station_coordinates_wgs84_lon\nXXX;Broken;;;\nYYY;Ok;500;46.0;8.0\n"
    )
    assert list(parse_station_meta(text)) == ["YYY"]


def test_select_stations_unknown_raises(fixtures):
    meta = parse_station_meta(decode_text((fixtures / "stations_meta.csv").read_bytes()))
    assert [s.abbr for s in select_stations(meta, ["JUN", "SMA"])] == ["JUN", "SMA"]
    with pytest.raises(KeyError, match="NOPE"):
        select_stations(meta, ["SMA", "NOPE"])


def test_obs_urls_current_year_is_recent_file():
    urls = obs_urls("SMA", date(2026, 8, 1), date(2026, 10, 31), today=date(2026, 11, 8))
    assert urls == [f"{BASE_URL}/sma/ogd-smn_sma_h_recent.csv"]


def test_obs_urls_spans_decades_and_recent():
    urls = obs_urls("JUN", date(2019, 12, 1), date(2026, 2, 1), today=date(2026, 11, 8))
    assert urls == [
        f"{BASE_URL}/jun/ogd-smn_jun_h_historical_2010-2019.csv",
        f"{BASE_URL}/jun/ogd-smn_jun_h_historical_2020-2029.csv",
        f"{BASE_URL}/jun/ogd-smn_jun_h_recent.csv",
    ]


def test_obs_urls_past_year_only_historical():
    urls = obs_urls("BER", date(2024, 1, 1), date(2024, 3, 1), today=date(2026, 11, 8))
    assert urls == [f"{BASE_URL}/ber/ogd-smn_ber_h_historical_2020-2029.csv"]


def test_obs_urls_rejects_reversed_range():
    with pytest.raises(ValueError):
        obs_urls("SMA", date(2026, 2, 1), date(2026, 1, 1))


def test_parse_obs_csv_real_excerpt(fixtures):
    df = parse_obs_csv((fixtures / "ogd-smn_sma_h_excerpt.csv").read_text(encoding="utf-8"))
    assert set(df["variable"]) == {"t2m", "precip", "wind"}
    t = df[df["variable"] == "t2m"].reset_index(drop=True)
    assert len(t) == 25
    assert t.loc[0, "time"] == pd.Timestamp("2026-10-30 00:00")
    assert t.loc[0, "obs"] == pytest.approx(5.3)
    assert t["time"].is_monotonic_increasing


def test_parse_obs_csv_drops_missing_values():
    text = (
        "station_abbr;reference_timestamp;tre200h0;rre150h0;fkl010h0\n"
        "AAA;01.01.2026 00:00;1.5;;2.0\n"
        "AAA;01.01.2026 01:00;;0.2;\n"
    )
    df = parse_obs_csv(text)
    assert len(df[df["variable"] == "t2m"]) == 1
    assert len(df[df["variable"] == "precip"]) == 1
    assert len(df[df["variable"] == "wind"]) == 1


def test_parse_obs_csv_variable_subset():
    text = "station_abbr;reference_timestamp;tre200h0;rre150h0;fkl010h0\nAAA;01.01.2026 00:00;1.5;0;2\n"
    assert set(parse_obs_csv(text, ("t2m",))["variable"]) == {"t2m"}


def test_parse_obs_csv_rejects_wrong_layout():
    with pytest.raises(ValueError):
        parse_obs_csv("a;b\n1;2\n")


def test_clip_window_whole_days_end_of_interval():
    t = pd.date_range("2026-01-01 00:00", "2026-01-03 00:00", freq="h")
    df = pd.DataFrame({"station": "A", "variable": "t2m", "time": t, "obs": 1.0})
    out = clip_window(df, date(2026, 1, 1), date(2026, 1, 2))
    # hour ending 2026-01-01 00:00 belongs to Dec 31; hour ending 2026-01-03 00:00 is Jan 2
    assert out["time"].min() == pd.Timestamp("2026-01-01 01:00")
    assert out["time"].max() == pd.Timestamp("2026-01-03 00:00")
    assert len(out) == 48
