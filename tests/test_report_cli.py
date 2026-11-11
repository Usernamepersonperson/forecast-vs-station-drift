import json
import struct

import pandas as pd
import pytest

from fvsd.cli import build_parser, main
from fvsd.report import altitude_view, build_report, headline_table, plot_altitude, plot_bias_vs_lead, station_table
from fvsd.score import compute_metrics


def _scores():
    rows = []
    for prov in ("p/a", "p/b"):
        for st, alt, grid in (("SMA", 604.0, 418.0), ("JUN", 3571.0, 3254.0)):
            for lead in (24, 48):
                for var in ("t2m", "precip", "wind"):
                    rows.append(
                        {
                            "provider": prov, "station": st, "variable": var, "lead_h": lead, "n": 500,
                            "bias": 0.5 + lead / 100, "mae": 1.0, "rmse": 1.4,
                            "bias_lapse": 0.1 if var == "t2m" else float("nan"),
                            "mae_lapse": 0.8 if var == "t2m" else float("nan"),
                            "rmse_lapse": 1.1 if var == "t2m" else float("nan"),
                            "station_altitude_m": alt, "grid_elevation_m": grid,
                        }
                    )
    return pd.DataFrame(rows)


def test_headline_table_markdown_shape():
    lines = headline_table(_scores(), "t2m", leads=[24])
    assert lines[0].startswith("| Provider |") and "MAE lapse-corr." in lines[0]
    assert len(lines) == 2 + 2  # header, rule, two providers
    assert "p/a" in lines[2] and "+0.74" in lines[2]


def test_headline_table_other_variable_has_no_lapse_columns():
    assert "lapse" not in headline_table(_scores(), "wind")[0]


def test_station_table_sorted_by_altitude():
    lines = station_table(_scores(), "p/a", "t2m", 24)
    assert lines[2].startswith("| SMA") and lines[3].startswith("| JUN")
    assert "418" in lines[2]


def test_altitude_view_dz():
    v = altitude_view(_scores(), "p/a", 24)
    assert dict(zip(v["station"], v["dz_m"], strict=True)) == {"JUN": -317.0, "SMA": -186.0}


def test_build_report_contains_sections_and_sources():
    md = build_report(_scores(), {"period_start": "2026-08-01", "period_end": "2026-10-31", "stations": ["JUN", "SMA"]})
    assert "2026-08-01 to 2026-10-31" in md
    assert "## 2 m temperature, mean over stations" in md
    assert "Source: MeteoSwiss" in md and "open-meteo.com" in md


def _png_size(path):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


def test_figure_is_1600x900(tmp_path):
    out = plot_bias_vs_lead(_scores(), tmp_path / "f.png")
    assert _png_size(out) == (1600, 900)


def test_altitude_figure_is_1600x900(tmp_path):
    out = plot_altitude(_scores(), tmp_path / "a.png")
    assert _png_size(out) == (1600, 900)


# ---------------------------------------------------------------- CLI


def test_parser_requires_command():
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_parser_rejects_bad_date():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["fetch", "--start", "yesterday"])


def test_score_without_cache_fails_cleanly(tmp_path, capsys):
    assert main(["score", "--cache", str(tmp_path / "none"), "--out", str(tmp_path)]) == 2
    assert "fvsd fetch" in capsys.readouterr().err


def test_report_without_scores_fails_cleanly(tmp_path, capsys):
    assert main(["report", "--scores", str(tmp_path / "x.parquet")]) == 2
    assert "fvsd score" in capsys.readouterr().err


def test_fetch_unknown_provider(tmp_path, capsys, fixtures):
    rc = main(["fetch", "--providers", "nope", "--cache", str(tmp_path)], getter=_offline_getter(fixtures))
    assert rc == 2
    assert "unknown provider" in capsys.readouterr().err


def test_fetch_rejects_reversed_dates(tmp_path):
    assert main(["fetch", "--start", "2026-02-01", "--end", "2026-01-01", "--cache", str(tmp_path)]) == 2


def _offline_getter(fixtures):
    """Serves committed fixtures for every URL the pipeline asks for."""
    meta = (fixtures / "stations_meta.csv").read_bytes()
    obs = (fixtures / "ogd-smn_sma_h_excerpt.csv").read_bytes()
    om = json.loads((fixtures / "openmeteo_icon_ch2_sample.json").read_text())

    def getter(url, headers=None):
        if url.endswith("ogd-smn_meta_stations.csv"):
            return meta
        if "ogd-smn_sma_h_recent.csv" in url:
            return obs
        if "previous-runs-api.open-meteo.com" in url:
            # shift the sample's six hours onto the observation excerpt's first day
            body = json.loads(json.dumps(om))
            body["hourly"]["time"] = [f"2026-10-30T0{i}:00" for i in range(6)]
            return json.dumps(body).encode()
        raise AssertionError(f"unexpected URL {url}")

    return getter


def test_end_to_end_fetch_score_report_offline(tmp_path, fixtures):
    cache, out, docs = tmp_path / "cache", tmp_path / "results", tmp_path / "docs"
    g = _offline_getter(fixtures)
    rc = main(["fetch", "--stations", "SMA", "--models", "meteoswiss_icon_ch2", "--variables", "t2m,precip,wind",
               "--start", "2026-10-30", "--end", "2026-10-30", "--cache", str(cache)], getter=g)
    assert rc == 0
    for name in ("observations", "forecasts", "stations"):
        assert (cache / f"{name}.parquet").exists()
    assert main(["score", "--cache", str(cache), "--out", str(out)]) == 0
    scores = pd.read_parquet(out / "scores.parquet")
    assert set(scores["station"]) == {"SMA"}
    assert {24, 48} <= set(scores["lead_h"])
    meta = json.loads((out / "meta.json").read_text())
    assert meta["stations"] == ["SMA"] and meta["period_start"] == "2026-10-30"
    assert main(["report", "--scores", str(out / "scores.parquet"), "--out", str(out), "--docs", str(docs)]) == 0
    assert (out / "report.md").read_text(encoding="utf-8").startswith("# Forecast vs station drift")
    assert (docs / "figure.png").exists()


def test_fetch_is_idempotent_for_parquet(tmp_path, fixtures):
    cache = tmp_path / "cache"
    args = ["fetch", "--stations", "SMA", "--models", "meteoswiss_icon_ch2", "--start", "2026-10-30",
            "--end", "2026-10-30", "--cache", str(cache)]
    g = _offline_getter(fixtures)
    main(args, getter=g)
    first = pd.read_parquet(cache / "forecasts.parquet")
    main(args, getter=g)
    assert len(pd.read_parquet(cache / "forecasts.parquet")) == len(first)


def test_compute_metrics_roundtrips_through_parquet(tmp_path, stations):
    from conftest import make_fc, make_obs

    from fvsd.score import build_pairs

    m = compute_metrics(build_pairs(make_obs([1.0] * 4), make_fc([2.0] * 4), stations))
    m.to_parquet(tmp_path / "s.parquet", index=False)
    pd.testing.assert_frame_equal(pd.read_parquet(tmp_path / "s.parquet"), m)


def test_fetch_defaults_are_resolved_at_run_time():
    args = build_parser().parse_args(["fetch"])
    assert args.start is None and args.end is None and args.providers == ["open-meteo"]
