"""Station metadata from the MeteoSwiss SwissMetNet (ogd-smn) station list."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass

META_URL = "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/ogd-smn_meta_stations.csv"

# 10 stations across regions and altitudes (abbreviations as used by MeteoSwiss).
DEFAULT_STATIONS = ("SMA", "BER", "BAS", "GVE", "SIO", "LUG", "STG", "DAV", "SAE", "JUN")

REGIONS = {
    "SMA": "Northern plateau",
    "BER": "Northern plateau",
    "BAS": "Northern lowland",
    "GVE": "Lake Geneva",
    "SIO": "Rhone valley",
    "LUG": "Southern Alps",
    "STG": "Northeast hills",
    "DAV": "Alpine valley",
    "SAE": "Prealpine summit",
    "JUN": "High Alpine summit",
}


@dataclass(frozen=True)
class Station:
    abbr: str
    name: str
    lat: float
    lon: float
    altitude_m: float


def decode_text(raw: bytes) -> str:
    """MeteoSwiss CSV files are not always UTF-8; fall back to cp1252."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252")


def parse_station_meta(text: str) -> dict[str, Station]:
    """Parse ogd-smn_meta_stations.csv (semicolon separated) into Station objects."""
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    required = {
        "station_abbr",
        "station_name",
        "station_height_masl",
        "station_coordinates_wgs84_lat",
        "station_coordinates_wgs84_lon",
    }
    if reader.fieldnames is None or not required <= set(reader.fieldnames):
        raise ValueError(f"station metadata is missing columns: {sorted(required)}")
    out: dict[str, Station] = {}
    for row in reader:
        try:
            out[row["station_abbr"]] = Station(
                abbr=row["station_abbr"],
                name=row["station_name"],
                lat=float(row["station_coordinates_wgs84_lat"]),
                lon=float(row["station_coordinates_wgs84_lon"]),
                altitude_m=float(row["station_height_masl"]),
            )
        except (TypeError, ValueError):
            continue  # skip rows with missing coordinates or height
    return out


def select_stations(meta: dict[str, Station], abbrs: list[str] | tuple[str, ...]) -> list[Station]:
    missing = [a for a in abbrs if a not in meta]
    if missing:
        raise KeyError(f"unknown station(s): {', '.join(missing)}")
    return [meta[a] for a in abbrs]
