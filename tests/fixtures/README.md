# Test fixtures

All tests run offline from these files.

| File | What it is |
|---|---|
| `stations_meta.csv` | Three rows (SMA, SAE, JUN) of the MeteoSwiss `ogd-smn_meta_stations.csv`, cp1252 encoded as served. Source: MeteoSwiss. |
| `ogd-smn_sma_h_excerpt.csv` | 25 hourly rows (2026-10-30 00:00 to 2026-10-31 00:00 UTC) of `ogd-smn_sma_h_recent.csv`, Zurich/Fluntern, all columns. Source: MeteoSwiss. |
| `openmeteo_icon_ch2_sample.json` | A real Open-Meteo Previous Runs response (ICON-CH2, Zurich/Fluntern) trimmed to 6 hours and lead days 1-2, with one value set to null by hand to test gap handling. |
