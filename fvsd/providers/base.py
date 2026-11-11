"""The one interface every forecast provider implements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import date

import pandas as pd

from fvsd.stations import Station

VARIABLES = ("t2m", "precip", "wind")
UNITS = {"t2m": "degC", "precip": "mm/h", "wind": "m/s"}

# provider    : provider/model label, e.g. "open-meteo/meteoswiss_icon_ch2"
# station     : MeteoSwiss station abbreviation
# variable    : one of VARIABLES
# valid_time  : UTC, naive; the instant the forecast is valid for
# lead_h      : hours between forecast issue (model run) and valid_time
# forecast    : value in UNITS
# grid_elevation_m : height of the model grid cell (NaN when the provider does not say)
FORECAST_COLUMNS = [
    "provider",
    "station",
    "variable",
    "valid_time",
    "lead_h",
    "forecast",
    "grid_elevation_m",
]


def empty_forecast() -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype="object") for c in FORECAST_COLUMNS})


class ForecastProvider(ABC):
    """A source of point forecasts at station coordinates."""

    #: label stored in the `provider` column
    name: str

    @abstractmethod
    def fetch(
        self,
        station: Station,
        start: date,
        end: date,
        variables: Sequence[str],
        leads_h: Sequence[int],
    ) -> pd.DataFrame:
        """Forecasts valid in [start, end] (whole UTC days) at the given lead times.

        Returns a DataFrame with FORECAST_COLUMNS. Providers that cannot honour `leads_h`
        document how they define lead time instead.
        """
