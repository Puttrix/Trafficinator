import importlib.util
import pathlib
import random
import sys
import uuid

HERE = pathlib.Path(__file__).resolve().parents[1]
LOADER_PATH = str(HERE / "loader.py")


def load_loader():
    module_name = f"loader_for_actions_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, LOADER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    sys.modules.pop(module_name, None)
    return module


loader = load_loader()
choose_action_pages = loader.choose_action_pages


def test_single_page_disables_actions():
    s, o, d, c, r = choose_action_pages(1, True, True, True, True, True)
    assert all(value == -1 for value in (s, o, d, c, r))


def test_actions_never_first_page():
    for _ in range(100):
        num_pvs = random.randint(2, 8)
        s, o, d, c, r = choose_action_pages(num_pvs, True, True, True, True, True)
        for v in (s, o, d, c, r):
            assert v == -1 or (2 <= v <= num_pvs)


def test_actions_respect_wants():
    s, o, d, c, r = choose_action_pages(5, True, False, True, False, True)
    assert s != -1 and o == -1 and d != -1 and c == -1 and r != -1
