import importlib.util
import pathlib
import sys
import uuid
from datetime import date, timedelta

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
LOADER_PATH = str(HERE / "loader.py")


def load_loader():
    """Load a fresh copy of loader.py to avoid shared globals across tests."""
    module_name = f"loader_for_backfill_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, LOADER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    sys.modules.pop(module_name, None)
    return module


def test_compute_backfill_window_absolute():
    loader = load_loader()
    loader.BACKFILL_START_DATE = "2024-10-01"
    loader.BACKFILL_END_DATE = "2024-10-03"
    loader.BACKFILL_DAYS_BACK = None
    loader.BACKFILL_DURATION_DAYS = None

    tz = loader.resolve_timezone()
    days = loader.compute_backfill_window(tz)
    assert len(days) == 3
    assert str(days[0]) == "2024-10-01"
    assert str(days[-1]) == "2024-10-03"


def test_compute_backfill_window_rejects_future_end():
    loader = load_loader()
    today = date.today()
    tomorrow = today + timedelta(days=1)
    loader.BACKFILL_START_DATE = today.strftime("%Y-%m-%d")
    loader.BACKFILL_END_DATE = tomorrow.strftime("%Y-%m-%d")
    loader.BACKFILL_DAYS_BACK = None
    loader.BACKFILL_DURATION_DAYS = None

    tz = loader.resolve_timezone()
    with pytest.raises(ValueError):
        loader.compute_backfill_window(tz)


def test_compute_backfill_window_rejects_long_window():
    loader = load_loader()
    today = date.today()
    too_far = today - timedelta(days=181)
    loader.BACKFILL_START_DATE = too_far.strftime("%Y-%m-%d")
    loader.BACKFILL_END_DATE = today.strftime("%Y-%m-%d")
    loader.BACKFILL_DAYS_BACK = None
    loader.BACKFILL_DURATION_DAYS = None

    tz = loader.resolve_timezone()
    with pytest.raises(ValueError):
        loader.compute_backfill_window(tz)


@pytest.mark.asyncio
async def test_run_backfill_respects_caps_and_seed(monkeypatch):
    loader = load_loader()
    loader.BACKFILL_START_DATE = "2024-10-01"
    loader.BACKFILL_END_DATE = "2024-10-02"  # two days
    loader.BACKFILL_DAYS_BACK = None
    loader.BACKFILL_DURATION_DAYS = None
    loader.BACKFILL_MAX_VISITS_PER_DAY = 100
    loader.BACKFILL_MAX_VISITS_TOTAL = 150
    loader.BACKFILL_RPS_LIMIT = 5.0
    loader.BACKFILL_SEED = 10

    captured = []

    async def fake_run_backfill_day(session, urls, day_range, visits_target, rps_limit):
        captured.append((day_range, visits_target, rps_limit))
        return visits_target  # pretend we sent everything

    monkeypatch.setattr(loader, "run_backfill_day", fake_run_backfill_day)
    summary = await loader.run_backfill(session=None, urls=["https://example.com"])

    assert len(summary) == 2
    assert summary[0]["target"] == 100
    assert summary[1]["target"] == 50  # total cap enforced
    assert captured[0][1] == 100
    assert captured[1][1] == 50
    assert captured[0][2] == 5.0
