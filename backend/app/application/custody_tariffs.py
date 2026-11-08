from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


SizeCategory = Literal["PEQUENO", "MEDIANO", "GRANDE"]
SIZE_CATEGORIES = frozenset(("PEQUENO", "MEDIANO", "GRANDE"))
Money = Annotated[str, Field(pattern=r"^[0-9]{1,10}\.[0-9]{2}$")]
PositiveHours = Annotated[int, Field(strict=True, gt=0)]
MAX_AMOUNT = Decimal("9999999999.99")


class SizeTariff(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_hours: PositiveHours
    block_hours: PositiveHours
    base_amount: Money
    block_amount: Money

    @model_validator(mode="after")
    def validate_amounts(self):
        if Decimal(self.base_amount) <= 0 or Decimal(self.block_amount) <= 0:
            raise ValueError("Los importes de la tarifa deben ser positivos.")
        return self

    def initial_price(self, hours: int) -> Decimal:
        extra = max(0, hours - self.base_hours)
        return Decimal(self.base_amount) + self.extension_price(extra)

    def extension_price(self, hours: int) -> Decimal:
        blocks = (hours + self.block_hours - 1) // self.block_hours
        return blocks * Decimal(self.block_amount)


class TariffRules(BaseModel):
    model_config = ConfigDict(extra="forbid")

    currency: Literal["BOB"]
    sizes: dict[SizeCategory, SizeTariff]

    @model_validator(mode="after")
    def validate_sizes(self):
        if self.sizes.keys() != SIZE_CATEGORIES:
            raise ValueError("Define una tarifa para cada tamaño admitido.")
        return self
