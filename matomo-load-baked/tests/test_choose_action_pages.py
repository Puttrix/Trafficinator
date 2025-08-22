import pytest
import random

from loader import choose_action_pages


def test_single_page_disables_actions():
    s, o, d = choose_action_pages(1, True, True, True)
    assert s == -1 and o == -1 and d == -1


def test_actions_never_first_page():
    for _ in range(100):
        num_pvs = random.randint(2, 8)
        s, o, d = choose_action_pages(num_pvs, True, True, True)
        for v in (s, o, d):
            assert v == -1 or (2 <= v <= num_pvs)


def test_actions_respect_wants():
    s, o, d = choose_action_pages(5, True, False, True)
    assert s != -1 and o == -1 and d != -1
