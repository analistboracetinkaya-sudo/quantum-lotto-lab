from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TurkeyLotteryGame:
    """Describes Turkish lottery products for data ingestion and the mobile app."""

    slug: str
    name: str
    draw_kind: str
    source_url: str | None
    main_min: int | None
    main_max: int | None
    drawn_main_count: int | None
    ticket_main_count: int | None
    bonus_min: int | None = None
    bonus_max: int | None = None
    drawn_bonus_count: int | None = None
    ticket_bonus_count: int | None = None
    schedule_note: str = ""
    model_status: str = "ready"
    data_status: str = "public_archive"
    note: str = ""

    def as_dict(self) -> dict:
        """Return a JSON-serializable representation."""
        return asdict(self)


TR_LOTTERY_GAMES: tuple[TurkeyLotteryGame, ...] = (
    TurkeyLotteryGame(
        slug="cilgin-sayisal-loto-tr",
        name="Çılgın Sayısal Loto",
        draw_kind="6/90 + Joker + SüperStar",
        source_url="https://www.lotobil.com/Sayisal-Loto-Butun-Sonuc-Listesi",
        main_min=1,
        main_max=90,
        drawn_main_count=6,
        ticket_main_count=6,
        bonus_min=1,
        bonus_max=90,
        drawn_bonus_count=2,
        ticket_bonus_count=2,
        schedule_note="Haftada 3 çekiliş: Pazartesi, Çarşamba, Cumartesi.",
        note="Last 10 years include old and new Sayısal Loto eras; reports flag regime changes.",
    ),
    TurkeyLotteryGame(
        slug="super-loto-tr",
        name="Süper Loto",
        draw_kind="6/60",
        source_url="https://www.lotobil.com/Super-Loto-Butun-Sonuc-Listesi",
        main_min=1,
        main_max=60,
        drawn_main_count=6,
        ticket_main_count=6,
        schedule_note="Haftada 3 çekiliş: Salı, Perşembe, Pazar.",
    ),
    TurkeyLotteryGame(
        slug="sans-topu-tr",
        name="Şans Topu",
        draw_kind="5/34 + 1/14",
        source_url="https://www.lotobil.com/Sans-Topu-Butun-Sonuc-Listesi",
        main_min=1,
        main_max=34,
        drawn_main_count=5,
        ticket_main_count=5,
        bonus_min=1,
        bonus_max=14,
        drawn_bonus_count=1,
        ticket_bonus_count=1,
        schedule_note="Haftada 2 çekiliş: Çarşamba, Pazar.",
    ),
    TurkeyLotteryGame(
        slug="on-numara-tr",
        name="On Numara",
        draw_kind="22/80 draw, 10/80 coupon",
        source_url="https://www.lotobil.com/On-Numara-Butun-Sonuc-Listesi",
        main_min=1,
        main_max=80,
        drawn_main_count=22,
        ticket_main_count=10,
        schedule_note="Haftada 2 çekiliş: Pazartesi, Cuma.",
        model_status="audit_ready_coupon_adapter",
        data_status="public_archive_missing_dates",
        note="LotoBil archive exposes year/draw number/22 numbers without draw dates; time-series features need official dated rows.",
    ),
    TurkeyLotteryGame(
        slug="hizli-on-numara-tr",
        name="Hızlı On",
        draw_kind="20/80 draw, 1-10/80 coupon",
        source_url="https://www.millipiyangoonline.com/hizli-on-numara/cekilis-sonuclari",
        main_min=1,
        main_max=80,
        drawn_main_count=20,
        ticket_main_count=10,
        schedule_note="5 dakikada bir çekiliş.",
        model_status="adapter_ready_limited_archive",
        data_status="no_10y_archive_new_game",
        note="New fast-draw product; no 10-year public archive exists. App supports connector ingestion when dated API data is available.",
    ),
    TurkeyLotteryGame(
        slug="milli-piyango-tr",
        name="Milli Piyango",
        draw_kind="ticket serial draw",
        source_url="https://www.millipiyangoonline.com/cekilis-sonuclari",
        main_min=None,
        main_max=None,
        drawn_main_count=None,
        ticket_main_count=None,
        model_status="not_lotto_pool",
        data_status="separate_ticket_serial_model",
        note="Not a number-pool lotto coupon; keep separate from pool-based quantum ticket optimization.",
    ),
)


def tr_lottery_games() -> list[TurkeyLotteryGame]:
    """Return supported Turkish lottery product metadata."""
    return list(TR_LOTTERY_GAMES)
