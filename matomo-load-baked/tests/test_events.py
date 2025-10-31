import importlib.util
import pathlib
import sys
import uuid

HERE = pathlib.Path(__file__).resolve().parents[1]
LOADER_PATH = str(HERE / "loader.py")


def load_loader():
    module_name = f"loader_for_events_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, LOADER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    sys.modules.pop(module_name, None)
    return module


def test_click_event_definitions_complete():
    loader = load_loader()
    assert len(loader.CLICK_EVENTS) > 0
    for event in loader.CLICK_EVENTS:
        assert all(key in event for key in ("category", "action", "name"))


def test_random_event_definitions_complete():
    loader = load_loader()
    assert len(loader.RANDOM_EVENTS) > 0
    for event in loader.RANDOM_EVENTS:
        assert all(key in event for key in ("category", "action", "name"))
