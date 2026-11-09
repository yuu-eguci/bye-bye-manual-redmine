"""
register_monthly_issues のテスト。

Redmine はすべてモック。 project・issue はすべて合成データ。
"""

import sys
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import register_monthly_issues


def test_help_describes_monthly_issue_registration(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["register_monthly_issues.py", "--help"])

    with pytest.raises(SystemExit):
        register_monthly_issues._parse_args()

    help_text = capsys.readouterr().out
    assert "月ごとの issue を作成するスクリプト" in help_text
    assert "Freee" not in help_text


@pytest.mark.parametrize(
    "month, first_day, last_day",
    [("2025-01", date(2025, 1, 1), date(2025, 1, 31)), ("2024-02", date(2024, 2, 1), date(2024, 2, 29))],
)
def test_issue_covers_whole_month_and_is_assigned_to_me(monkeypatch, month, first_day, last_day):
    redmine = MagicMock()
    redmine.user.get.return_value = SimpleNamespace(id=5)
    redmine.issue.create.return_value = SimpleNamespace(id=747)
    monkeypatch.setattr(register_monthly_issues, "Redmine", lambda *args, **kwargs: redmine)

    register_monthly_issues.main(
        redmine_url="https://redmine.example.invalid",
        redmine_api_key="synthetic-api-key",
        project_id=10,
        issue_prefix="Project B の作業",
        month=month,
    )

    redmine.issue.create.assert_called_once_with(
        project_id=10,
        subject=f"Project B の作業 {month}",
        description="",
        start_date=first_day,
        due_date=last_day,
        assigned_to_id=5,
        tracker_id=1,
        status_id=1,
    )
