from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.application.custody_tariffs import SizeTariff, TariffRules


def test_t24_tariff_rounds_blocks_with_decimal_without_database():
    rule = SizeTariff(base_hours=24, block_hours=12, base_amount="12.50", block_amount="2.75")
    assert rule.initial_price(24) == Decimal("12.50")
    assert rule.initial_price(25) == Decimal("15.25")
    assert rule.extension_price(13) == Decimal("5.50")


def test_t24_tariff_rejects_missing_size_and_zero_price():
    block = {"base_hours": 24, "block_hours": 12, "base_amount": "12.50", "block_amount": "2.75"}
    with pytest.raises(ValidationError):
        TariffRules.model_validate({"currency": "BOB", "sizes": {"PEQUENO": block}})
    with pytest.raises(ValidationError):
        SizeTariff(**{**block, "block_amount": "0.00"})
