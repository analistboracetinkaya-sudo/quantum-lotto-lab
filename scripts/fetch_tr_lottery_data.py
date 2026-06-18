from __future__ import annotations

import argparse
import json
from datetime import date
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from quantum_lotto_lab.tr_lotteries import tr_lottery_games


DEFAULT_OUTPUT_DIR = Path("data/tr")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch Turkish lottery archive data for model preparation.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for CSV and manifest output.")
    parser.add_argument("--years", type=int, default=10, help="Number of trailing years to keep when dated rows exist.")
    return parser.parse_args()


def normalize_date(value: object) -> date | None:
    parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def as_int(value: object) -> int | None:
    if pd.isna(value):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def read_lotobil_tables(url: str) -> list[pd.DataFrame]:
    last_error: Exception | None = None
    for _ in range(3):
        try:
            response = requests.get(url, timeout=45, headers={"User-Agent": "QuantumLottoLab/0.1"})
            response.raise_for_status()
            return pd.read_html(StringIO(response.text))
        except Exception as exc:  # pragma: no cover - network retry path
            last_error = exc
    if last_error:
        raise last_error
    return []


def filter_dated(df: pd.DataFrame, years: int) -> pd.DataFrame:
    cutoff = date(date.today().year - years, date.today().month, date.today().day)
    dated = df.copy()
    dated["date"] = pd.to_datetime(dated["date"], errors="coerce")
    dated = dated.dropna(subset=["date"])
    dated = dated[dated["date"].dt.date >= cutoff]
    return dated.sort_values(["date", "draw_no"]).reset_index(drop=True)


def parse_number_table(
    url: str,
    *,
    main_count: int,
    main_prefix: str = "n",
    include_bonus: bool = False,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    required = {"Tarih", "Hft", *(f"T{i}" for i in range(1, main_count + 1))}
    for table in read_lotobil_tables(url):
        columns = [str(col).strip() for col in table.columns]
        if not required.issubset(set(columns)):
            continue
        frame = table.copy()
        frame.columns = columns
        for _, row in frame.iterrows():
            draw_date = normalize_date(row["Tarih"])
            draw_no = as_int(row["Hft"])
            nums = [as_int(row[f"T{i}"]) for i in range(1, main_count + 1)]
            if draw_date is None or draw_no is None or any(num is None for num in nums):
                continue
            item: dict[str, Any] = {"date": draw_date.isoformat(), "draw_no": draw_no}
            for idx, num in enumerate(nums, 1):
                item[f"{main_prefix}{idx}"] = num
            if include_bonus:
                for col in ("Joker", "Super"):
                    if col in frame.columns:
                        item[col.lower()] = as_int(row[col])
            rows.append(item)
    return pd.DataFrame(rows)


def parse_sans_topu(url: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    required = {"Tarih", "Hft", "T1", "T2", "T3", "T4", "T5", "T6"}
    for table in read_lotobil_tables(url):
        columns = [str(col).strip() for col in table.columns]
        if not required.issubset(set(columns)):
            continue
        frame = table.copy()
        frame.columns = columns
        for _, row in frame.iterrows():
            draw_date = normalize_date(row["Tarih"])
            draw_no = as_int(row["Hft"])
            main = [as_int(row[f"T{i}"]) for i in range(1, 6)]
            bonus = as_int(row["T6"])
            if draw_date is None or draw_no is None or any(num is None for num in main) or bonus is None:
                continue
            rows.append(
                {
                    "date": draw_date.isoformat(),
                    "draw_no": draw_no,
                    "n1": main[0],
                    "n2": main[1],
                    "n3": main[2],
                    "n4": main[3],
                    "n5": main[4],
                    "bonus": bonus,
                }
            )
    return pd.DataFrame(rows)


def parse_on_numara_year_draws(url: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    tables = read_lotobil_tables(url)
    # LotoBil exposes one table per year. The rows do not include draw dates,
    # so this file is raw year/draw-number history and should not be used for
    # recency/calendar analysis until a dated source is joined.
    current_year = date.today().year
    year = current_year
    for table in tables:
        columns = [str(col).strip() for col in table.columns]
        if not {"Hft", *(f"T{i}" for i in range(1, 23))}.issubset(set(columns)):
            continue
        frame = table.copy()
        frame.columns = columns
        for _, row in frame.iterrows():
            draw_no = as_int(row["Hft"])
            nums = [as_int(row[f"T{i}"]) for i in range(1, 23)]
            if draw_no is None or any(num is None for num in nums):
                continue
            item: dict[str, Any] = {"year": year, "draw_no": draw_no}
            for idx, num in enumerate(nums, 1):
                item[f"n{idx}"] = num
            rows.append(item)
        year -= 1
    return pd.DataFrame(rows)


def quality_summary(df: pd.DataFrame, *, main_cols: list[str], min_num: int, max_num: int) -> dict[str, Any]:
    if df.empty:
        return {"rows": 0, "issues": ["empty"]}
    issues: list[str] = []
    nums = df[main_cols]
    out_of_range = ((nums < min_num) | (nums > max_num)).any(axis=1)
    duplicate_numbers = nums.apply(lambda row: len(set(int(x) for x in row)) != len(main_cols), axis=1)
    if bool(out_of_range.any()):
        issues.append(f"{int(out_of_range.sum())} rows have numbers outside {min_num}..{max_num}")
    if bool(duplicate_numbers.any()):
        issues.append(f"{int(duplicate_numbers.sum())} rows have repeated main numbers")
    if "date" in df.columns:
        dup_dates = int(df.duplicated(["date", "draw_no"]).sum())
        if dup_dates:
            issues.append(f"{dup_dates} duplicate date/draw rows")
    return {
        "rows": int(len(df)),
        "first": str(df["date"].min()) if "date" in df.columns and not df.empty else None,
        "last": str(df["date"].max()) if "date" in df.columns and not df.empty else None,
        "issues": issues,
    }


def split_valid_rows(
    df: pd.DataFrame,
    *,
    main_cols: list[str],
    min_num: int,
    max_num: int,
    duplicate_key: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty:
        return df.copy(), df.copy()
    nums = df[main_cols]
    out_of_range = ((nums < min_num) | (nums > max_num)).any(axis=1)
    duplicate_numbers = nums.apply(lambda row: len(set(int(x) for x in row)) != len(main_cols), axis=1)
    duplicate_rows = pd.Series(False, index=df.index)
    if duplicate_key:
        duplicate_rows = df.duplicated(duplicate_key, keep="first")
    invalid = out_of_range | duplicate_numbers | duplicate_rows
    return df.loc[~invalid].reset_index(drop=True), df.loc[invalid].reset_index(drop=True)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def add_numbers_column(df: pd.DataFrame, main_cols: list[str]) -> pd.DataFrame:
    enriched = df.copy()
    if not enriched.empty:
        enriched["numbers"] = enriched[main_cols].apply(lambda row: " ".join(str(int(value)) for value in row), axis=1)
    return enriched


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "generated_at": date.today().isoformat(),
        "window_years": args.years,
        "games": {},
    }
    games = {game.slug: game for game in tr_lottery_games()}

    sayisal_raw = filter_dated(
        parse_number_table(games["cilgin-sayisal-loto-tr"].source_url or "", main_count=6, include_bonus=True),
        args.years,
    )
    sayisal, sayisal_excluded = split_valid_rows(
        sayisal_raw,
        main_cols=[f"n{i}" for i in range(1, 7)],
        min_num=1,
        max_num=90,
        duplicate_key=["date", "draw_no"],
    )
    sayisal = add_numbers_column(sayisal, [f"n{i}" for i in range(1, 7)])
    if not sayisal.empty:
        sayisal["bonus"] = sayisal[["joker", "super"]].apply(
            lambda row: " ".join(str(int(value)) for value in row if pd.notna(value) and 1 <= int(value) <= 90),
            axis=1,
        )
    write_csv(sayisal, output_dir / "cilgin_sayisal_loto_tr_10y.csv")
    write_csv(sayisal_excluded, output_dir / "cilgin_sayisal_loto_tr_10y_excluded.csv")
    manifest["games"]["cilgin-sayisal-loto-tr"] = {
        **games["cilgin-sayisal-loto-tr"].as_dict(),
        "csv": "cilgin_sayisal_loto_tr_10y.csv",
        "excluded_csv": "cilgin_sayisal_loto_tr_10y_excluded.csv",
        "quality": quality_summary(sayisal, main_cols=[f"n{i}" for i in range(1, 7)], min_num=1, max_num=90),
    }

    super_loto_raw = filter_dated(
        parse_number_table(games["super-loto-tr"].source_url or "", main_count=6),
        args.years,
    )
    # Known public-source typo: 2023-10-29 draw 130 is published by
    # several result pages as 7 12 20 25 47 48; LotoBil currently repeats 48.
    correction = (super_loto_raw["date"].astype(str) == "2023-10-29") & (super_loto_raw["draw_no"] == 130)
    if bool(correction.any()):
        super_loto_raw.loc[correction, ["n1", "n2", "n3", "n4", "n5", "n6"]] = [7, 12, 20, 25, 47, 48]
    super_loto, super_loto_excluded = split_valid_rows(
        super_loto_raw,
        main_cols=[f"n{i}" for i in range(1, 7)],
        min_num=1,
        max_num=60,
        duplicate_key=["date", "draw_no"],
    )
    super_loto = add_numbers_column(super_loto, [f"n{i}" for i in range(1, 7)])
    write_csv(super_loto, output_dir / "super_loto_tr_10y.csv")
    write_csv(super_loto_excluded, output_dir / "super_loto_tr_10y_excluded.csv")
    manifest["games"]["super-loto-tr"] = {
        **games["super-loto-tr"].as_dict(),
        "csv": "super_loto_tr_10y.csv",
        "excluded_csv": "super_loto_tr_10y_excluded.csv",
        "quality": quality_summary(super_loto, main_cols=[f"n{i}" for i in range(1, 7)], min_num=1, max_num=60),
    }

    sans_topu_raw = filter_dated(parse_sans_topu(games["sans-topu-tr"].source_url or ""), args.years)
    sans_topu, sans_topu_excluded = split_valid_rows(
        sans_topu_raw,
        main_cols=[f"n{i}" for i in range(1, 6)],
        min_num=1,
        max_num=34,
        duplicate_key=["date", "draw_no"],
    )
    sans_topu = add_numbers_column(sans_topu, [f"n{i}" for i in range(1, 6)])
    write_csv(sans_topu, output_dir / "sans_topu_tr_10y.csv")
    write_csv(sans_topu_excluded, output_dir / "sans_topu_tr_10y_excluded.csv")
    manifest["games"]["sans-topu-tr"] = {
        **games["sans-topu-tr"].as_dict(),
        "csv": "sans_topu_tr_10y.csv",
        "excluded_csv": "sans_topu_tr_10y_excluded.csv",
        "quality": quality_summary(sans_topu, main_cols=[f"n{i}" for i in range(1, 6)], min_num=1, max_num=34),
    }

    on_numara = parse_on_numara_year_draws(games["on-numara-tr"].source_url or "")
    min_year = date.today().year - args.years
    on_numara = on_numara[on_numara["year"] >= min_year].sort_values(["year", "draw_no"]).reset_index(drop=True)
    on_numara, on_numara_excluded = split_valid_rows(
        on_numara,
        main_cols=[f"n{i}" for i in range(1, 23)],
        min_num=1,
        max_num=80,
        duplicate_key=["year", "draw_no"],
    )
    on_numara = add_numbers_column(on_numara, [f"n{i}" for i in range(1, 23)])
    write_csv(on_numara, output_dir / "on_numara_tr_10y_undated.csv")
    write_csv(on_numara_excluded, output_dir / "on_numara_tr_10y_undated_excluded.csv")
    manifest["games"]["on-numara-tr"] = {
        **games["on-numara-tr"].as_dict(),
        "csv": "on_numara_tr_10y_undated.csv",
        "excluded_csv": "on_numara_tr_10y_undated_excluded.csv",
        "quality": quality_summary(on_numara, main_cols=[f"n{i}" for i in range(1, 23)], min_num=1, max_num=80),
    }

    for slug in ("hizli-on-numara-tr", "milli-piyango-tr"):
        manifest["games"][slug] = {
            **games[slug].as_dict(),
            "csv": None,
            "quality": {"rows": 0, "issues": [games[slug].data_status]},
        }

    manifest_path = output_dir / "turkey_lottery_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
