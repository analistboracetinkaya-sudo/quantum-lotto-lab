from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class PoolSpec:
    name: str
    minimum: int
    maximum: int
    pick: int

    @property
    def values(self) -> list[int]:
        return list(range(self.minimum, self.maximum + 1))


@dataclass(frozen=True)
class LotterySpec:
    slug: str
    name: str
    region: str
    main: PoolSpec
    bonus: PoolSpec | None = None
    source_url: str | None = None
    parser: str | None = None
    source_note: str = ""


@dataclass(frozen=True)
class Draw:
    date: date
    main: tuple[int, ...]
    bonus: tuple[int, ...] = field(default_factory=tuple)


@dataclass
class Ticket:
    main: tuple[int, ...]
    bonus: tuple[int, ...] = field(default_factory=tuple)
    source: str = "model"

    def as_dict(self) -> dict:
        return {"main": list(self.main), "bonus": list(self.bonus), "source": self.source}

