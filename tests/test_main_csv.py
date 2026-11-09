"""
main._get_daily_work_hours のテスト。

CSV はすべて合成データ。
"""

from pathlib import Path

import pytest

import main


def _write_csv(tmp_path: Path, rows: list[tuple[str, str]]) -> str:
    lines = ["日付,総勤務時間"] + [f"{date},{hours}" for date, hours in rows]
    csv_path = tmp_path / "freee.csv"
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(csv_path)


def test_hh_mm_is_converted_to_decimal_hours(tmp_path):
    csv_path = _write_csv(tmp_path, [("2025-01-06", "8:30"), ("2025-01-07", "7:45")])

    assert main._get_daily_work_hours(csv_path) == {"2025-01-06": 8.5, "2025-01-07": 7.75}


def test_slash_date_is_normalized_to_iso_format(tmp_path):
    csv_path = _write_csv(tmp_path, [("2025/8/1", "8:00"), ("2025-8-21", "1:00")])

    assert main._get_daily_work_hours(csv_path) == {"2025-08-01": 8.0, "2025-08-21": 1.0}


def test_same_date_rows_are_summed(tmp_path):
    csv_path = _write_csv(tmp_path, [("2025-01-06", "4:00"), ("2025/1/6", "3:30")])

    assert main._get_daily_work_hours(csv_path) == {"2025-01-06": 7.5}


@pytest.mark.parametrize("hours", ["", "-", "abc"])
def test_empty_or_invalid_hours_are_treated_as_zero(tmp_path, hours):
    csv_path = _write_csv(tmp_path, [("2025-01-06", hours)])

    assert main._get_daily_work_hours(csv_path) == {"2025-01-06": 0.0}


def test_other_columns_are_ignored(tmp_path):
    csv_path = tmp_path / "freee.csv"
    csv_path.write_text("従業員名,日付,出勤時刻,総勤務時間\n合成 太郎,2025-01-06,09:00,8:00\n", encoding="utf-8")

    assert main._get_daily_work_hours(str(csv_path)) == {"2025-01-06": 8.0}
