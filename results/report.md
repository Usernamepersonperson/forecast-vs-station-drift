# Forecast vs station drift - results

Period (UTC): 2026-08-01 to 2026-10-31. Stations: BAS, BER, DAV, GVE, JUN, LUG, SAE, SIO, SMA, STG. Forecast/observation pairs: 703791.

error = forecast - observation. Lapse-corrected = forecast shifted from grid height to station height with 6.5 K/km.

## 2 m temperature, mean over stations

| Provider | Lead (h) | Stations | Bias (degC) | MAE (degC) | RMSE (degC) | MAE lapse-corr. | RMSE lapse-corr. |
|---|---:|---:|---:|---:|---:|---:|---:|
| open-meteo/ecmwf_ifs025 | 24 | 10 | -0.25 | 2.79 | 3.17 | 1.68 | 2.12 |
| open-meteo/ecmwf_ifs025 | 48 | 10 | -0.28 | 2.83 | 3.22 | 1.71 | 2.16 |
| open-meteo/ecmwf_ifs025 | 72 | 10 | -0.24 | 2.86 | 3.29 | 1.78 | 2.25 |
| open-meteo/ecmwf_ifs025 | 96 | 10 | -0.13 | 2.95 | 3.44 | 1.88 | 2.39 |
| open-meteo/ecmwf_ifs025 | 120 | 10 | -0.18 | 3.13 | 3.71 | 2.12 | 2.70 |
| open-meteo/ecmwf_ifs025 | 144 | 10 | -0.33 | 3.32 | 3.93 | 2.30 | 2.92 |
| open-meteo/ecmwf_ifs025 | 168 | 10 | -0.28 | 3.53 | 4.24 | 2.56 | 3.26 |
| open-meteo/meteoswiss_icon_ch2 | 24 | 9 | +0.66 | 1.70 | 2.04 | 1.16 | 1.52 |
| open-meteo/meteoswiss_icon_ch2 | 48 | 9 | +0.67 | 1.77 | 2.15 | 1.25 | 1.63 |
| open-meteo/meteoswiss_icon_ch2 | 72 | 9 | +0.74 | 1.90 | 2.34 | 1.40 | 1.83 |
| open-meteo/meteoswiss_icon_ch2 | 96 | 9 | +0.90 | 2.11 | 2.60 | 1.61 | 2.11 |

## Precipitation (hourly sum), mean over stations

| Provider | Lead (h) | Stations | Bias (mm/h) | MAE (mm/h) | RMSE (mm/h) |
|---|---:|---:|---:|---:|---:|
| open-meteo/ecmwf_ifs025 | 24 | 9 | +0.01 | 0.15 | 0.67 |
| open-meteo/ecmwf_ifs025 | 48 | 9 | +0.01 | 0.15 | 0.69 |
| open-meteo/ecmwf_ifs025 | 72 | 9 | -0.00 | 0.16 | 0.71 |
| open-meteo/ecmwf_ifs025 | 96 | 9 | +0.00 | 0.16 | 0.73 |
| open-meteo/ecmwf_ifs025 | 120 | 9 | +0.02 | 0.19 | 0.75 |
| open-meteo/ecmwf_ifs025 | 144 | 9 | +0.01 | 0.19 | 0.76 |
| open-meteo/ecmwf_ifs025 | 168 | 9 | +0.00 | 0.19 | 0.76 |
| open-meteo/meteoswiss_icon_ch2 | 24 | 9 | -0.02 | 0.14 | 0.80 |
| open-meteo/meteoswiss_icon_ch2 | 48 | 9 | -0.01 | 0.15 | 0.84 |
| open-meteo/meteoswiss_icon_ch2 | 72 | 9 | -0.02 | 0.15 | 0.84 |
| open-meteo/meteoswiss_icon_ch2 | 96 | 9 | +0.02 | 0.19 | 1.06 |

## 10 m wind speed, mean over stations

| Provider | Lead (h) | Stations | Bias (m/s) | MAE (m/s) | RMSE (m/s) |
|---|---:|---:|---:|---:|---:|
| open-meteo/ecmwf_ifs025 | 24 | 10 | -1.17 | 1.62 | 2.12 |
| open-meteo/ecmwf_ifs025 | 48 | 10 | -1.19 | 1.63 | 2.14 |
| open-meteo/ecmwf_ifs025 | 72 | 10 | -1.22 | 1.65 | 2.17 |
| open-meteo/ecmwf_ifs025 | 96 | 10 | -1.25 | 1.67 | 2.20 |
| open-meteo/ecmwf_ifs025 | 120 | 10 | -1.24 | 1.72 | 2.28 |
| open-meteo/ecmwf_ifs025 | 144 | 10 | -1.25 | 1.76 | 2.34 |
| open-meteo/ecmwf_ifs025 | 168 | 10 | -1.29 | 1.82 | 2.41 |
| open-meteo/meteoswiss_icon_ch2 | 24 | 10 | -0.44 | 1.11 | 1.51 |
| open-meteo/meteoswiss_icon_ch2 | 48 | 10 | -0.46 | 1.15 | 1.58 |
| open-meteo/meteoswiss_icon_ch2 | 72 | 10 | -0.51 | 1.20 | 1.64 |
| open-meteo/meteoswiss_icon_ch2 | 96 | 10 | -0.49 | 1.27 | 1.74 |

## 2 m temperature per station, open-meteo/ecmwf_ifs025, lead 24 h

| Station | Region | Alt (m) | Grid (m) | n | Bias (degC) | MAE (degC) | RMSE (degC) | Bias lapse-corr. | MAE lapse-corr. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LUG | Southern Alps | 273 | 746 | 2207 | -3.20 | 3.23 | 3.58 | -0.13 | 1.27 |
| BAS | Northern lowland | 316 | 419 | 2207 | -0.96 | 1.42 | 1.76 | -0.29 | 1.19 |
| GVE | Lake Geneva | 411 | 470 | 2207 | -0.07 | 1.33 | 1.69 | +0.31 | 1.37 |
| SIO | Rhone valley | 482 | 1531 | 2207 | -5.35 | 5.37 | 5.87 | +1.47 | 2.20 |
| BER | Northern plateau | 553 | 557 | 2207 | -0.52 | 1.11 | 1.46 | -0.49 | 1.10 |
| SMA | Northern plateau | 604 | 461 | 2207 | -0.27 | 1.32 | 1.67 | -1.20 | 1.63 |
| STG | Northeast hills | 776 | 498 | 2207 | +1.35 | 1.72 | 2.07 | -0.46 | 1.30 |
| DAV | Alpine valley | 1594 | 2053 | 2207 | -2.57 | 2.69 | 3.09 | +0.41 | 1.37 |
| SAE | Prealpine summit | 2501 | 1198 | 2207 | +7.08 | 7.09 | 7.49 | -1.39 | 2.24 |
| JUN | High Alpine summit | 3571 | 2799 | 2207 | +1.96 | 2.64 | 3.07 | -3.06 | 3.13 |

## 2 m temperature per station, open-meteo/meteoswiss_icon_ch2, lead 24 h

| Station | Region | Alt (m) | Grid (m) | n | Bias (degC) | MAE (degC) | RMSE (degC) | Bias lapse-corr. | MAE lapse-corr. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LUG | Southern Alps | 273 | 0 | 2207 | +1.16 | 1.36 | 1.73 | - | - |
| BAS | Northern lowland | 316 | 299 | 2207 | -0.10 | 1.08 | 1.41 | -0.21 | 1.09 |
| GVE | Lake Geneva | 411 | 413 | 2207 | +0.38 | 1.03 | 1.38 | +0.40 | 1.04 |
| SIO | Rhone valley | 482 | 542 | 2207 | +0.54 | 1.55 | 2.08 | +0.93 | 1.67 |
| BER | Northern plateau | 553 | 558 | 2207 | -0.03 | 1.02 | 1.37 | +0.00 | 1.02 |
| SMA | Northern plateau | 604 | 418 | 2207 | +1.33 | 1.63 | 2.03 | +0.12 | 1.19 |
| STG | Northeast hills | 776 | 842 | 2207 | -0.57 | 1.14 | 1.49 | -0.14 | 1.00 |
| DAV | Alpine valley | 1594 | 1761 | 2207 | -1.53 | 1.71 | 2.06 | -0.45 | 1.13 |
| SAE | Prealpine summit | 2501 | 1700 | 2207 | +4.92 | 4.92 | 5.11 | -0.29 | 1.08 |
| JUN | High Alpine summit | 3571 | 3254 | 2207 | +1.01 | 1.22 | 1.47 | -1.05 | 1.24 |

## Precipitation (hourly sum) per station, open-meteo/ecmwf_ifs025, lead 24 h

| Station | Region | Alt (m) | n | Bias (mm/h) | MAE (mm/h) | RMSE (mm/h) |
|---|---|---:|---:|---:|---:|---:|
| LUG | Southern Alps | 273 | 2207 | +0.01 | 0.28 | 1.41 |
| BAS | Northern lowland | 316 | 2207 | +0.02 | 0.09 | 0.50 |
| GVE | Lake Geneva | 411 | 2207 | +0.03 | 0.11 | 0.55 |
| SIO | Rhone valley | 482 | 2207 | +0.05 | 0.10 | 0.36 |
| BER | Northern plateau | 553 | 2207 | -0.01 | 0.11 | 0.61 |
| SMA | Northern plateau | 604 | 2207 | +0.00 | 0.10 | 0.53 |
| STG | Northeast hills | 776 | 2207 | +0.02 | 0.16 | 0.66 |
| DAV | Alpine valley | 1594 | 2207 | +0.05 | 0.16 | 0.55 |
| SAE | Prealpine summit | 2501 | 2207 | -0.06 | 0.23 | 0.84 |

## Precipitation (hourly sum) per station, open-meteo/meteoswiss_icon_ch2, lead 24 h

| Station | Region | Alt (m) | n | Bias (mm/h) | MAE (mm/h) | RMSE (mm/h) |
|---|---|---:|---:|---:|---:|---:|
| LUG | Southern Alps | 273 | 2207 | -0.09 | 0.23 | 1.47 |
| BAS | Northern lowland | 316 | 2207 | +0.01 | 0.10 | 0.69 |
| GVE | Lake Geneva | 411 | 2207 | +0.03 | 0.12 | 0.73 |
| SIO | Rhone valley | 482 | 2207 | +0.01 | 0.07 | 0.42 |
| BER | Northern plateau | 553 | 2207 | -0.03 | 0.10 | 0.65 |
| SMA | Northern plateau | 604 | 2207 | -0.01 | 0.10 | 0.64 |
| STG | Northeast hills | 776 | 2207 | +0.01 | 0.17 | 1.01 |
| DAV | Alpine valley | 1594 | 2207 | +0.01 | 0.14 | 0.66 |
| SAE | Prealpine summit | 2501 | 2207 | -0.08 | 0.21 | 0.91 |

## 10 m wind speed per station, open-meteo/ecmwf_ifs025, lead 24 h

| Station | Region | Alt (m) | n | Bias (m/s) | MAE (m/s) | RMSE (m/s) |
|---|---|---:|---:|---:|---:|---:|
| LUG | Southern Alps | 273 | 2207 | -0.61 | 0.75 | 1.08 |
| BAS | Northern lowland | 316 | 2207 | +0.44 | 0.78 | 1.04 |
| GVE | Lake Geneva | 411 | 2207 | -0.53 | 0.81 | 1.14 |
| SIO | Rhone valley | 482 | 2207 | -1.19 | 1.33 | 2.10 |
| BER | Northern plateau | 553 | 2207 | +0.13 | 0.71 | 0.96 |
| SMA | Northern plateau | 604 | 2200 | +0.16 | 0.70 | 0.91 |
| STG | Northeast hills | 776 | 2207 | -0.19 | 0.91 | 1.21 |
| DAV | Alpine valley | 1594 | 2207 | -1.03 | 1.20 | 1.72 |
| SAE | Prealpine summit | 2501 | 2207 | -4.47 | 4.57 | 5.73 |
| JUN | High Alpine summit | 3571 | 2207 | -4.40 | 4.43 | 5.35 |

## 10 m wind speed per station, open-meteo/meteoswiss_icon_ch2, lead 24 h

| Station | Region | Alt (m) | n | Bias (m/s) | MAE (m/s) | RMSE (m/s) |
|---|---|---:|---:|---:|---:|---:|
| LUG | Southern Alps | 273 | 2207 | -0.26 | 0.66 | 0.94 |
| BAS | Northern lowland | 316 | 2207 | +0.21 | 0.58 | 0.78 |
| GVE | Lake Geneva | 411 | 2207 | +0.19 | 0.69 | 0.94 |
| SIO | Rhone valley | 482 | 2207 | -0.69 | 1.04 | 1.55 |
| BER | Northern plateau | 553 | 2207 | +0.14 | 0.63 | 0.90 |
| SMA | Northern plateau | 604 | 2200 | -0.42 | 0.76 | 1.04 |
| STG | Northeast hills | 776 | 2207 | +0.26 | 0.71 | 0.99 |
| DAV | Alpine valley | 1594 | 2207 | -0.39 | 1.03 | 1.42 |
| SAE | Prealpine summit | 2501 | 2207 | -2.71 | 3.08 | 3.88 |
| JUN | High Alpine summit | 3571 | 2207 | -0.72 | 1.97 | 2.71 |

## Sources

- Observations: Source: MeteoSwiss, SwissMetNet hourly values (ogd-smn), https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn (open data, CC BY).
- Forecasts: Open-Meteo Previous Runs API, https://open-meteo.com/en/docs/previous-runs-api (CC BY 4.0, free for non-commercial use); models served: MeteoSwiss ICON-CH2 and ECMWF IFS 0.25 deg.
