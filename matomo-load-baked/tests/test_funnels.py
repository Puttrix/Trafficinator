import importlib.util
import json
import pathlib
import uuid


HERE = pathlib.Path(__file__).resolve().parents[1]
LOADER_PATH = str(HERE / "loader.py")


def load_loader():
    module_name = f"loader_funnels_test_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, LOADER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def test_load_funnels_from_file(tmp_path):
    module = load_loader()

    funnel_data = [
        {
            "name": "Valid Funnel",
            "description": "Test funnel",
            "probability": 1.0,
            "priority": 1,
            "enabled": True,
            "exit_after_completion": True,
            "steps": [
                {
                    "type": "pageview",
                    "url": "https://example.com/landing",
                    "delay_seconds_min": 0,
                    "delay_seconds_max": 1.5,
                },
                {
                    "type": "event",
                    "url": "https://example.com/landing",
                    "event_category": "CTA",
                    "event_action": "Click",
                    "event_name": "Hero Button",
                },
            ],
        },
        {
            "name": "Disabled Funnel",
            "enabled": False,
            "steps": [{"type": "pageview", "url": "https://example.com"}],
        },
        {
            "name": "Invalid Starting Step",
            "enabled": True,
            "steps": [{"type": "event", "event_category": "x", "event_action": "y", "event_name": "z"}],
        },
    ]

    funnels_file = tmp_path / "funnels.json"
    funnels_file.write_text(json.dumps(funnel_data))

    funnels = module.load_funnels_from_file(str(funnels_file))

    assert len(funnels) == 1
    funnel = funnels[0]
    assert funnel["name"] == "Valid Funnel"
    assert funnel["priority"] == 1
    assert len(funnel["steps"]) == 2
    assert funnel["steps"][0]["delay_seconds_max"] == 1.5


def test_select_funnel_probability():
    module = load_loader()
    module.FUNNELS = [
        {
            "name": "Always",
            "probability": 1.0,
            "priority": 0,
            "exit_after_completion": True,
            "steps": [{"type": "pageview", "url": "https://example.com", "delay_seconds_min": 0, "delay_seconds_max": 0}],
        }
    ]

    module.random.seed(1)
    selected = module.select_funnel()
    assert selected is not None
    assert selected["name"] == "Always"

    module.FUNNELS[0]["probability"] = 0.0
    module.random.seed(1)
    assert module.select_funnel() is None
