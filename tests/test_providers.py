import urllib.error
from datetime import date

import pandas as pd
import pytest

from fvsd.http import cached_get, http_get
from fvsd.providers import (
    FORECAST_COLUMNS,
    ForecastProvider,
    OpenMeteoProvider,
)
from fvsd.providers.openmeteo import lead_hours_to_days

# ---------------------------------------------------------------- http


class _Resp:
    def __init__(self, body):
        self._b = body

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_http_get_retries_on_429_then_succeeds():
    calls = []

    def opener(req, timeout):
        calls.append(1)
        if len(calls) < 3:
            raise urllib.error.HTTPError(req.full_url, 429, "slow down", {}, None)
        return _Resp(b"ok")

    sleeps = []
    assert http_get("http://x", opener=opener, sleep=sleeps.append) == b"ok"
    assert len(calls) == 3 and sleeps == [2.0, 4.0]


def test_http_get_does_not_retry_404():
    def opener(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 404, "nope", {}, None)

    with pytest.raises(urllib.error.HTTPError):
        http_get("http://x", opener=opener, sleep=lambda s: None)


def test_http_get_gives_up_after_retries():
    def opener(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 503, "down", {}, None)

    with pytest.raises(urllib.error.HTTPError):
        http_get("http://x", retries=2, opener=opener, sleep=lambda s: None)


def test_cached_get_downloads_once(tmp_path):
    calls = []

    def getter(url, headers):
        calls.append(url)
        return b"body"

    p = tmp_path / "a" / "f.bin"
    assert cached_get("u", p, getter) == b"body"
    assert cached_get("u", p, getter) == b"body"
    assert len(calls) == 1


# ---------------------------------------------------------------- Open-Meteo


def test_openmeteo_lead_hours_to_days():
    assert lead_hours_to_days([24, 72]) == [1, 3]
    with pytest.raises(ValueError):
        lead_hours_to_days([36])
    with pytest.raises(ValueError):
        lead_hours_to_days([192])


def test_openmeteo_build_url(sma):
    url = OpenMeteoProvider("meteoswiss_icon_ch2").build_url(sma, date(2026, 8, 1), date(2026, 8, 3), ["t2m"], [1, 2])
    assert url.startswith("https://previous-runs-api.open-meteo.com/v1/forecast?")
    assert "models=meteoswiss_icon_ch2" in url
    assert "elevation=nan" in url  # raw grid cell, no downscaling
    assert "timezone=UTC" in url and "wind_speed_unit=ms" in url
    assert "temperature_2m_previous_day1,temperature_2m_previous_day2" in url
    assert "start_date=2026-08-01" in url and "end_date=2026-08-03" in url


def test_openmeteo_parse_real_sample(fixtures, sma):
    prov = OpenMeteoProvider("meteoswiss_icon_ch2")
    df = prov.parse((fixtures / "openmeteo_icon_ch2_sample.json").read_bytes(), sma, ["t2m", "precip", "wind"], [1, 2])
    assert list(df.columns) == FORECAST_COLUMNS
    assert set(df["lead_h"]) == {24, 48}
    assert (df["grid_elevation_m"] == 418.0).all()
    assert (df["provider"] == "open-meteo/meteoswiss_icon_ch2").all()
    t1 = df[(df["variable"] == "t2m") & (df["lead_h"] == 24)].reset_index(drop=True)
    assert t1.loc[0, "forecast"] == pytest.approx(20.2)
    assert t1.loc[0, "valid_time"] == pd.Timestamp("2026-08-01 00:00")


def test_openmeteo_parse_drops_nulls(fixtures, sma):
    prov = OpenMeteoProvider()
    df = prov.parse((fixtures / "openmeteo_icon_ch2_sample.json").read_bytes(), sma, ["t2m"], [2])
    assert len(df) == 5  # one of six hours was null
    assert pd.Timestamp("2026-08-01 03:00") not in set(df["valid_time"])


def test_openmeteo_parse_error_payload(sma):
    with pytest.raises(RuntimeError, match="bad model"):
        OpenMeteoProvider().parse(b'{"error": true, "reason": "bad model"}', sma, ["t2m"], [1])


def test_openmeteo_fetch_uses_cache(fixtures, sma, tmp_path):
    body = (fixtures / "openmeteo_icon_ch2_sample.json").read_bytes()
    calls = []

    def getter(url, headers):
        calls.append(url)
        return body

    prov = OpenMeteoProvider(cache_dir=tmp_path, http_get_fn=getter)
    a = prov.fetch(sma, date(2026, 8, 1), date(2026, 8, 1), ["t2m"], [24, 48])
    b = prov.fetch(sma, date(2026, 8, 1), date(2026, 8, 1), ["t2m"], [24, 48])
    assert len(calls) == 1
    pd.testing.assert_frame_equal(a, b)


def test_openmeteo_is_a_provider():
    assert issubclass(OpenMeteoProvider, ForecastProvider)


# ---------------------------------------------------------------- generic provider interface


class _ConstantProvider(ForecastProvider):
    """Minimal adapter: proves a new provider only has to implement fetch()."""

    name = "const/test"

    def fetch(self, station, start, end, variables, leads_h):
        rows = [
            {
                "provider": self.name,
                "station": station.abbr,
                "variable": v,
                "valid_time": pd.Timestamp(start),
                "lead_h": lead,
                "forecast": 1.0,
                "grid_elevation_m": float("nan"),
            }
            for v in variables
            for lead in leads_h
        ]
        return pd.DataFrame(rows, columns=FORECAST_COLUMNS)


def test_custom_provider_implements_interface(sma):
    df = _ConstantProvider().fetch(sma, date(2026, 11, 8), date(2026, 11, 8), ["t2m", "wind"], [24, 48])
    assert list(df.columns) == FORECAST_COLUMNS
    assert len(df) == 4


def test_provider_interface_is_abstract():
    with pytest.raises(TypeError):
        ForecastProvider()
