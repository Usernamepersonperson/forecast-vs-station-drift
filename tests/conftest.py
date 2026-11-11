from pathlib import Path

import pandas as pd
import pytest

from fvsd.stations import Station

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures() -> Path:
    return FIXTURES


@pytest.fixture
def sma() -> Station:
    return Station("SMA", "Zuerich / Fluntern", 47.381003, 8.567194, 604.0)


@pytest.fixture
def stations(sma) -> dict[str, Station]:
    return {"SMA": sma, "JUN": Station("JUN", "Jungfraujoch", 46.547556, 7.985444, 3571.0)}


def make_fc(values, *, provider="p", station="SMA", variable="t2m", lead_h=24, grid=604.0,
            start="2026-01-01 00:00"):
    t = pd.date_range(start, periods=len(values), freq="h")
    return pd.DataFrame(
        {
            "provider": provider,
            "station": station,
            "variable": variable,
            "valid_time": t,
            "lead_h": lead_h,
            "forecast": values,
            "grid_elevation_m": grid,
        }
    )


def make_obs(values, *, station="SMA", variable="t2m", start="2026-01-01 00:00"):
    t = pd.date_range(start, periods=len(values), freq="h")
    return pd.DataFrame({"station": station, "variable": variable, "time": t, "obs": values})
