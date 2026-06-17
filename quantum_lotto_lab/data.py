from __future__ import annotations

import csv
import json
import re
from datetime import date
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests

from .models import Draw, LotterySpec


DATE_COLUMNS = ("date", "draw date", "draw_date", "tarih", "drawdate")
MAIN_COLUMNS = ("main", "numbers", "winning numbers", "winning_numbers", "nums", "number")
BONUS_COLUMNS = ("bonus", "bonus numbers", "bonus_numbers", "mega ball", "powerball", "lucky stars", "stars")


def parse_ints(value: object) -> tuple[int, ...]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ()
    return tuple(int(x) for x in re.findall(r"\d+", str(value)))


def normalize_date(value: object) -> date:
    parsed = pd.to_datetime(value, errors="raise")
    return parsed.date()


def _find_column(columns: Iterable[str], choices: tuple[str, ...]) -> str | None:
    normalized = {str(col).strip().lower(): str(col) for col in columns}
    for choice in choices:
        if choice in normalized:
            return normalized[choice]
    for col in columns:
        low = str(col).strip().lower()
        if any(choice in low for choice in choices):
            return str(col)
    return None


def parse_generic_csv(path_or_url: str | Path, spec: LotterySpec) -> list[Draw]:
    df = pd.read_csv(path_or_url)
    date_col = _find_column(df.columns, DATE_COLUMNS)
    main_col = _find_column(df.columns, MAIN_COLUMNS)
    bonus_col = _find_column(df.columns, BONUS_COLUMNS)
    if date_col is None:
        raise ValueError("CSV needs a date column. Accepted names include: date, draw_date, Draw Date.")
    if main_col is None:
        numbered = [str(i) for i in range(1, spec.main.pick + 1)]
        if all(col in df.columns for col in numbered):
            rows = []
            for _, row in df.iterrows():
                main = tuple(sorted(int(row[col]) for col in numbered))
                rows.append(Draw(normalize_date(row[date_col]), main, ()))
            return sorted(rows, key=lambda item: item.date)
        raise ValueError("CSV needs a main numbers column or numeric columns 1..pick.")

    draws: list[Draw] = []
    for _, row in df.iterrows():
        main = parse_ints(row[main_col])
        bonus = parse_ints(row[bonus_col]) if bonus_col else ()
        if len(main) < spec.main.pick:
            continue
        if len(main) > spec.main.pick and spec.bonus and not bonus:
            bonus = main[spec.main.pick :]
            main = main[: spec.main.pick]
        main = tuple(sorted(main[: spec.main.pick]))
        bonus = tuple(sorted(bonus[: spec.bonus.pick])) if spec.bonus else ()
        draws.append(Draw(normalize_date(row[date_col]), main, bonus))
    return sorted(draws, key=lambda item: item.date)


def parse_ny_powerball(url: str, spec: LotterySpec) -> list[Draw]:
    df = pd.read_csv(url)
    draws: list[Draw] = []
    for _, row in df.iterrows():
        nums = parse_ints(row["Winning Numbers"])
        if len(nums) < 6:
            continue
        draws.append(Draw(normalize_date(row["Draw Date"]), tuple(sorted(nums[:5])), (nums[5],)))
    return sorted(draws, key=lambda item: item.date)


def parse_ny_mega_millions(url: str, spec: LotterySpec) -> list[Draw]:
    df = pd.read_csv(url)
    draws: list[Draw] = []
    for _, row in df.iterrows():
        nums = parse_ints(row["Winning Numbers"])
        if len(nums) < 5:
            continue
        draws.append(Draw(normalize_date(row["Draw Date"]), tuple(sorted(nums[:5])), (int(row["Mega Ball"]),)))
    return sorted(draws, key=lambda item: item.date)


def parse_euromillions_api(url: str, spec: LotterySpec) -> list[Draw]:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict):
        items = payload.get("draws") or payload.get("data") or payload.get("results") or []
    else:
        items = payload
    draws: list[Draw] = []
    for item in items:
        raw_date = item.get("date") or item.get("draw_date") or item.get("drawDate")
        main = item.get("numbers") or item.get("main") or item.get("balls") or item.get("draw")
        stars = item.get("stars") or item.get("luckyStars") or item.get("bonus") or item.get("lucky_stars")
        if raw_date is None or main is None:
            continue
        main_nums = tuple(sorted(int(x) for x in (main if isinstance(main, list) else parse_ints(main))[:5]))
        bonus_nums = tuple(sorted(int(x) for x in (stars if isinstance(stars, list) else parse_ints(stars))[:2]))
        if len(main_nums) == 5:
            draws.append(Draw(normalize_date(raw_date), main_nums, bonus_nums))
    return sorted(draws, key=lambda item: item.date)


def parse_lotobil_super_loto(url: str, spec: LotterySpec) -> list[Draw]:
    tables = pd.read_html(url)
    draws: list[Draw] = []
    for table in tables:
        columns = [str(col).lower() for col in table.columns]
        if not any("tarih" in col or "date" in col for col in columns):
            continue
        for _, row in table.iterrows():
            values = " ".join(str(v) for v in row.to_list())
            nums = parse_ints(values)
            if len(nums) < 7:
                continue
            # Avoid using year/month/day as draw numbers by taking the final six
            # valid 1..60 values in the row.
            valid = [num for num in nums if 1 <= num <= 60]
            if len(valid) >= 6:
                main = tuple(sorted(valid[-6:]))
                try:
                    draw_date = normalize_date(row.iloc[0])
                except Exception:
                    continue
                draws.append(Draw(draw_date, main, ()))
    return sorted(set(draws), key=lambda item: item.date)


PARSERS = {
    "ny_powerball": parse_ny_powerball,
    "ny_mega_millions": parse_ny_mega_millions,
    "euromillions_api": parse_euromillions_api,
    "lotobil_super_loto": parse_lotobil_super_loto,
}


def load_draws(spec: LotterySpec, csv_path: str | Path | None = None) -> list[Draw]:
    if csv_path:
        return parse_generic_csv(csv_path, spec)
    if not spec.source_url or not spec.parser:
        raise SystemExit(
            f"{spec.name} has no built-in live source. Pass --csv with draw history, "
            "or add a custom lottery JSON spec."
        )
    parser = PARSERS.get(spec.parser)
    if parser is None:
        raise SystemExit(f"No parser registered for {spec.parser}.")
    return parser(spec.source_url, spec)


def load_custom_spec(path: str | Path) -> LotterySpec:
    from .models import PoolSpec, LotterySpec

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    main = PoolSpec(
        payload.get("main", {}).get("name", "numbers"),
        int(payload["main"]["min"]),
        int(payload["main"]["max"]),
        int(payload["main"]["pick"]),
    )
    bonus_payload = payload.get("bonus")
    bonus = None
    if bonus_payload:
        bonus = PoolSpec(
            bonus_payload.get("name", "bonus"),
            int(bonus_payload["min"]),
            int(bonus_payload["max"]),
            int(bonus_payload["pick"]),
        )
    return LotterySpec(
        slug=payload["slug"],
        name=payload["name"],
        region=payload.get("region", "custom"),
        main=main,
        bonus=bonus,
        source_url=payload.get("source_url"),
        parser=payload.get("parser"),
        source_note=payload.get("source_note", "custom user spec"),
    )

