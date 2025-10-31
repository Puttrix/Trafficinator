import importlib.util
import json
import os
import pathlib
import random
import sys
import uuid

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
LOADER_PATH = str(HERE / "loader.py")


def load_loader_module(env_overrides):
    """Load loader.py with specific environment overrides."""
    module_name = f"loader_for_test_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, LOADER_PATH)
    module = importlib.util.module_from_spec(spec)

    original_env = {key: os.environ.get(key) for key in env_overrides}
    try:
        for key, value in env_overrides.items():
            os.environ[key] = str(value)
        spec.loader.exec_module(module)  # type: ignore[attr-defined]
    finally:
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        sys.modules.pop(module_name, None)

    return module


def test_generate_ecommerce_order_respects_probability_zero():
    loader = load_loader_module({"ECOMMERCE_PROBABILITY": "0"})
    assert loader.generate_ecommerce_order() is None


def test_generate_ecommerce_order_within_configured_bounds():
    overrides = {
        "ECOMMERCE_PROBABILITY": "1",
        "ECOMMERCE_ORDER_VALUE_MIN": "50.0",
        "ECOMMERCE_ORDER_VALUE_MAX": "150.0",
        "ECOMMERCE_ITEMS_MIN": "1",
        "ECOMMERCE_ITEMS_MAX": "2",
        "ECOMMERCE_SHIPPING_RATES": "0",
        "ECOMMERCE_TAX_RATE": "0.05",
    }
    loader = load_loader_module(overrides)

    loader.random.seed(12345)
    order = loader.generate_ecommerce_order()
    assert order is not None, "Expected ecommerce order when probability forced to 1"

    order_id, items_json, revenue, subtotal, tax, shipping = order

    assert len(order_id) == 8

    min_revenue = float(overrides["ECOMMERCE_ORDER_VALUE_MIN"])
    max_revenue = float(overrides["ECOMMERCE_ORDER_VALUE_MAX"])
    assert min_revenue <= revenue <= max_revenue

    assert subtotal >= 0
    assert tax >= 0
    assert shipping == 0

    items = json.loads(items_json)
    assert len(items) >= 1
    for item in items:
        sku, name, category, price, quantity = item
        assert isinstance(sku, str) and sku
        assert isinstance(name, str) and name
        assert isinstance(category, str) and category
        assert price > 0
        assert quantity >= 1

    calculated_subtotal = sum(item[3] * item[4] for item in items)
    calculated_tax = round((calculated_subtotal + shipping) * 0.05, 2)
    calculated_revenue = round(calculated_subtotal + shipping + calculated_tax, 2)

    assert pytest.approx(calculated_subtotal, rel=1e-6) == subtotal
    assert pytest.approx(calculated_tax, rel=1e-6) == tax
    assert pytest.approx(calculated_revenue, rel=1e-6) == revenue
