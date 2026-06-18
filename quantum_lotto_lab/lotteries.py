from __future__ import annotations

from .models import LotterySpec, PoolSpec


BUILTINS: dict[str, LotterySpec] = {
    "powerball": LotterySpec(
        slug="powerball",
        name="US Powerball",
        region="United States",
        main=PoolSpec("white balls", 1, 69, 5),
        bonus=PoolSpec("Powerball", 1, 26, 1),
        source_url="https://data.ny.gov/api/views/d6yy-54nr/rows.csv?accessType=DOWNLOAD",
        parser="ny_powerball",
        source_note="NY Open Data mirrors Powerball winning numbers beginning 2010.",
    ),
    "mega-millions": LotterySpec(
        slug="mega-millions",
        name="US Mega Millions",
        region="United States",
        main=PoolSpec("white balls", 1, 70, 5),
        bonus=PoolSpec("Mega Ball", 1, 25, 1),
        source_url="https://data.ny.gov/api/views/5xaw-6ayf/rows.csv?accessType=DOWNLOAD",
        parser="ny_mega_millions",
        source_note="NY Open Data mirrors Mega Millions winning numbers.",
    ),
    "euromillions": LotterySpec(
        slug="euromillions",
        name="EuroMillions",
        region="Europe",
        main=PoolSpec("numbers", 1, 50, 5),
        bonus=PoolSpec("lucky stars", 1, 12, 2),
        source_url="https://euromillions.api.pedromealha.dev/draws",
        parser="euromillions_api",
        source_note="Community API. It can rate-limit; use --csv fallback if needed.",
    ),
    "eurojackpot": LotterySpec(
        slug="eurojackpot",
        name="EuroJackpot",
        region="Europe",
        main=PoolSpec("numbers", 1, 50, 5),
        bonus=PoolSpec("euro numbers", 1, 12, 2),
        source_url=None,
        parser=None,
        source_note="Use --csv with a downloaded EuroJackpot history file if no local source is configured.",
    ),
    "super-loto-tr": LotterySpec(
        slug="super-loto-tr",
        name="Turkey Super Loto",
        region="Turkey",
        main=PoolSpec("numbers", 1, 60, 6),
        source_url="https://www.lotobil.com/Super-Loto-Butun-Sonuc-Listesi",
        parser="lotobil_super_loto",
        source_note="HTML source can change; --csv is recommended for reproducible research.",
    ),
    "cilgin-sayisal-loto-tr": LotterySpec(
        slug="cilgin-sayisal-loto-tr",
        name="Turkey Çılgın Sayısal Loto",
        region="Turkey",
        main=PoolSpec("numbers", 1, 90, 6),
        bonus=PoolSpec("joker/superstar", 1, 90, 2),
        source_url=None,
        parser=None,
        source_note=(
            "Use scripts/fetch_tr_lottery_data.py for dated LotoBil archive CSV. "
            "The last 10 years cross old and new Sayısal Loto rule eras."
        ),
    ),
    "sans-topu-tr": LotterySpec(
        slug="sans-topu-tr",
        name="Turkey Şans Topu",
        region="Turkey",
        main=PoolSpec("numbers", 1, 34, 5),
        bonus=PoolSpec("plus ball", 1, 14, 1),
        source_url=None,
        parser=None,
        source_note="Use scripts/fetch_tr_lottery_data.py for dated LotoBil archive CSV.",
    ),
    "on-numara-tr-draw": LotterySpec(
        slug="on-numara-tr-draw",
        name="Turkey On Numara Draw Field",
        region="Turkey",
        main=PoolSpec("drawn numbers", 1, 80, 22),
        source_url=None,
        parser=None,
        source_note=(
            "Draw-audit spec only. On Numara coupons pick 10 numbers, while draws expose 22 winning numbers. "
            "Use the mobile adapter/metadata for coupon generation."
        ),
    ),
    "uk-lotto": LotterySpec(
        slug="uk-lotto",
        name="UK Lotto",
        region="United Kingdom",
        main=PoolSpec("numbers", 1, 59, 6),
        bonus=PoolSpec("bonus ball", 1, 59, 1),
        source_url=None,
        parser=None,
        source_note="Use --csv with official or trusted draw history export.",
    ),
    "france-loto": LotterySpec(
        slug="france-loto",
        name="France Loto",
        region="France",
        main=PoolSpec("numbers", 1, 49, 5),
        bonus=PoolSpec("lucky number", 1, 10, 1),
        source_url=None,
        parser=None,
        source_note="Use --csv with FDJ/open-data history export.",
    ),
    "germany-6aus49": LotterySpec(
        slug="germany-6aus49",
        name="Germany Lotto 6aus49",
        region="Germany",
        main=PoolSpec("numbers", 1, 49, 6),
        bonus=PoolSpec("superzahl", 0, 9, 1),
        source_url=None,
        parser=None,
        source_note="Use --csv with official or trusted draw history export.",
    ),
    "superenalotto": LotterySpec(
        slug="superenalotto",
        name="Italy SuperEnalotto",
        region="Italy",
        main=PoolSpec("numbers", 1, 90, 6),
        source_url=None,
        parser=None,
        source_note="Use --csv with official or trusted draw history export.",
    ),
}


def list_lotteries() -> list[LotterySpec]:
    return list(BUILTINS.values())


def get_lottery(slug: str) -> LotterySpec:
    try:
        return BUILTINS[slug]
    except KeyError as exc:
        choices = ", ".join(sorted(BUILTINS))
        raise SystemExit(f"Unknown lottery '{slug}'. Available: {choices}") from exc
