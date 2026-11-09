"""
main.main の流れのテスト。

Redmine はすべてモック。 CSV・issue・時間データはすべて合成データ。
"""

import logging
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import main

FAKE_URL = "https://redmine.example.invalid"
FAKE_KEY = "synthetic-api-key"


def _write_csv(tmp_path: Path) -> str:
    csv_path = tmp_path / "freee.csv"
    csv_path.write_text("日付,総勤務時間\n2025-01-06,8:00\n2025-01-07,4:00\n", encoding="utf-8")
    return str(csv_path)


def _fake_redmine(issues_by_subject: dict[str, list], existing_entries: list | None = None) -> MagicMock:
    redmine = MagicMock()
    redmine.user.get.return_value = SimpleNamespace(id=5)
    redmine.issue.filter.side_effect = lambda subject, assigned_to_id: issues_by_subject.get(subject, [])
    redmine.time_entry.filter.return_value = existing_entries or []
    return redmine


def _run(monkeypatch, redmine: MagicMock, csv_path: str, issue_names: list[str], ratios: list[float]) -> None:
    monkeypatch.setattr(main, "Redmine", lambda *args, **kwargs: redmine)
    main.main(
        redmine_url=FAKE_URL,
        redmine_api_key=FAKE_KEY,
        freee_csv_path=csv_path,
        redmine_issue_names=issue_names,
        time_distribution=ratios,
        activity_id=9,
    )


def test_time_entries_are_created_by_ratio_and_registered_dates_are_skipped(monkeypatch, tmp_path):
    issue = SimpleNamespace(id=721, subject="Issue A")
    existing = [SimpleNamespace(spent_on=date(2025, 1, 6), hours=6.0)]
    redmine = _fake_redmine({"Issue A": [issue]}, existing_entries=existing)

    _run(monkeypatch, redmine, _write_csv(tmp_path), ["Issue A"], [0.75])

    redmine.time_entry.create.assert_called_once_with(
        issue_id=721, spent_on="2025-01-07", hours=3.0, activity_id=9, comments=""
    )


def test_nothing_is_created_when_issue_is_not_found(monkeypatch, tmp_path, caplog):
    issue_a = SimpleNamespace(id=721, subject="Issue A")
    redmine = _fake_redmine({"Issue A": [issue_a]})

    with caplog.at_level(logging.INFO):
        _run(monkeypatch, redmine, _write_csv(tmp_path), ["Issue A", "Missing"], [0.5, 0.5])

    assert "Issue が見つからない: 'Missing'" in caplog.text
    redmine.time_entry.create.assert_not_called()


def test_nothing_is_created_when_multiple_issues_match(monkeypatch, tmp_path, caplog):
    duplicates = [SimpleNamespace(id=1, subject="Issue A"), SimpleNamespace(id=2, subject="Issue A")]
    redmine = _fake_redmine({"Issue A": duplicates})

    with caplog.at_level(logging.INFO):
        _run(monkeypatch, redmine, _write_csv(tmp_path), ["Issue A"], [1.0])

    assert "Issue が複数見つかった" in caplog.text
    redmine.time_entry.create.assert_not_called()


@pytest.mark.parametrize("issue_names, ratios", [(["Issue A"], [0.5, 0.5]), (["Issue A", "Issue B"], [1.0])])
def test_nothing_is_created_when_issue_and_ratio_counts_differ(monkeypatch, tmp_path, caplog, issue_names, ratios):
    redmine = _fake_redmine({"Issue A": [SimpleNamespace(id=721, subject="Issue A")]})

    with caplog.at_level(logging.INFO):
        _run(monkeypatch, redmine, _write_csv(tmp_path), issue_names, ratios)

    assert "引数がおかしい" in caplog.text
    redmine.time_entry.create.assert_not_called()
