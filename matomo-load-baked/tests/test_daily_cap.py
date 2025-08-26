import time
import importlib.util
import pathlib

# Load the loader module directly from its file path because the package
# directory contains a hyphen and isn't importable as a normal module.
HERE = pathlib.Path(__file__).resolve().parents[1]
LOADER_PATH = str(HERE / 'loader.py')

spec = importlib.util.spec_from_file_location('loader', LOADER_PATH)
loader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loader)


def test_check_daily_cap_disabled():
    now = time.time()
    should_pause, new_start, new_visits = loader.check_daily_cap(now, now - 1000, 5, 0)
    assert should_pause is False
    assert new_start == now - 1000
    assert new_visits == 5


def test_check_daily_cap_window_reset():
    now = time.time()
    old_start = now - 90000  # > 86400
    should_pause, new_start, new_visits = loader.check_daily_cap(now, old_start, 100, 50)
    assert should_pause is False
    assert new_start == now
    assert new_visits == 0


def test_check_daily_cap_reached():
    now = time.time()
    start = now - 1000
    should_pause, new_start, new_visits = loader.check_daily_cap(now, start, 10, 10)
    assert should_pause is True
    assert new_start == start
    assert new_visits == 10


def test_check_daily_cap_not_reached():
    now = time.time()
    start = now - 1000
    should_pause, new_start, new_visits = loader.check_daily_cap(now, start, 5, 10)
    assert should_pause is False
    assert new_start == start
    assert new_visits == 5
