"""
main.py の --dry-run のテスト。

Redmine はすべてモック。 CSV・issue はすべて合成データ。
"""

import logging
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import redminelib

import main

REQUIRED_ARGS = [
    "--url", "https://redmine.example.invalid",
    "--key", "synthetic-api-key",
    "--issues", "Issue A",
    "--time", "1.0",
    "--activity", "9",
    "--freee", "freee.csv",
]  # fmt: skip


def test_dry_run_is_disabled_by_default():
    assert main._parse_args(REQUIRED_ARGS).dry_run is False


def test_dry_run_flag_enables_dry_run():
    assert main._parse_args([*REQUIRED_ARGS, "--dry-run"]).dry_run is True


def test_dry_run_logs_planned_entries_without_creating(monkeypatch, tmp_path, caplog):
    csv_path = tmp_path / "freee.csv"
    csv_path.write_text("日付,総勤務時間\n2025-01-06,8:00\n", encoding="utf-8")
    redmine = MagicMock()
    redmine.user.get.return_value = SimpleNamespace(id=5)
    redmine.issue.filter.return_value = [SimpleNamespace(id=721, subject="Issue A")]
    redmine.time_entry.filter.return_value = []
    monkeypatch.setattr(main, "Redmine", lambda *args, **kwargs: redmine)

    with caplog.at_level(logging.INFO):
        main.main(
            redmine_url="https://redmine.example.invalid",
            redmine_api_key="synthetic-api-key",
            freee_csv_path=str(csv_path),
            redmine_issue_names=["Issue A"],
            time_distribution=[0.5],
            activity_id=9,
            dry_run=True,
        )

    assert "[DRY RUN] Issue 721 : 2025-01-06 : 4.0 時間を登録予定。" in caplog.text
    redmine.time_entry.create.assert_not_called()


def test_dry_run_flag_is_passed_from_command_line(monkeypatch, tmp_path):
    csv_path = tmp_path / "freee.csv"
    csv_path.write_text("日付,総勤務時間\n2025-01-06,8:00\n", encoding="utf-8")
    redmine = MagicMock()
    redmine.user.get.return_value = SimpleNamespace(id=5)
    redmine.issue.filter.return_value = [SimpleNamespace(id=721, subject="Issue A")]
    redmine.time_entry.filter.return_value = []
    # スクリプトとして実行したときの `from redminelib import Redmine` もモックにする。
    monkeypatch.setattr(redminelib, "Redmine", lambda *args, **kwargs: redmine)
    argv = [arg if arg != "freee.csv" else str(csv_path) for arg in REQUIRED_ARGS]
    monkeypatch.setattr(sys, "argv", ["main.py", *argv, "--dry-run"])

    runpy.run_path(str(Path(main.__file__)), run_name="__main__")

    redmine.time_entry.create.assert_not_called()
