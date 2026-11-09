"""
API キーがログへ出力されないことのテスト。

Redmine はすべてモック。 API キーは合成値。
"""

import logging
from unittest.mock import MagicMock

import pytest

import fetch_projects
import main
import register_monthly_issues

FAKE_URL = "https://redmine.example.invalid"
FAKE_KEY = "synthetic-api-key-0123456789"


def _redmine_whose_user_lookup_fails() -> MagicMock:
    redmine = MagicMock()
    redmine.user.get.side_effect = Exception("synthetic auth error")
    return redmine


@pytest.mark.parametrize(
    "module, extra_kwargs",
    [
        (
            main,
            {
                "freee_csv_path": "unused.csv",
                "redmine_issue_names": ["Issue A"],
                "time_distribution": [1.0],
                "activity_id": 9,
            },
        ),
        (fetch_projects, {}),
        (register_monthly_issues, {"project_id": 10, "issue_prefix": "作業", "month": "2025-01"}),
    ],
)
def test_api_key_is_not_logged_when_user_lookup_fails(monkeypatch, caplog, module, extra_kwargs):
    redmine = _redmine_whose_user_lookup_fails()
    monkeypatch.setattr(module, "Redmine", lambda *args, **kwargs: redmine)

    with caplog.at_level(logging.INFO):
        module.main(redmine_url=FAKE_URL, redmine_api_key=FAKE_KEY, **extra_kwargs)

    assert "User ID 取得に失敗" in caplog.text
    assert FAKE_KEY not in caplog.text
