"""
bye_bye_manual_redmine.register_monthly_issues
"""

import argparse
import logging
from datetime import datetime, timedelta

from redminelib import Redmine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def _parse_args():
    parser = argparse.ArgumentParser(description="Redmine に Freee の勤怠データを同期するスクリプト")

    parser.add_argument("--url", required=True, help="Redmine の URL")
    parser.add_argument("--key", required=True, help="Redmine の API キー")
    parser.add_argument("--project", type=int, required=True, help="Redmine の project ID")
    parser.add_argument("--prefix", type=str, required=True, help="作りたい issue の名前")
    parser.add_argument("--month", type=str, required=True, help="作りたい issue の年月 yyyy-mm 形式のみ")

    return parser.parse_args()


def _fetch_user_id(redmine: Redmine) -> int:
    user = redmine.user.get("current")
    return user.id


def main(
    redmine_url: str,
    redmine_api_key: str,
    project_id: int,
    issue_prefix: str,
    month: str,  # yyyy-mm 形式
) -> None:
    redmine = Redmine(redmine_url, key=redmine_api_key)

    # Redmine から自分の id を取得します。 (/users/current)
    try:
        user_id = _fetch_user_id(redmine)
        logging.info(f"User ID 見つかったよ: {user_id}")
    except Exception:
        logging.exception(f"User ID 取得に失敗。 API key を確認せよ: '{redmine_api_key}'")
        return

    # month の初日と末日を作成します。
    try:
        first_day = datetime.strptime(month, "%Y-%m").replace(day=1)
        last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        logging.info(f"Issue の範囲: {first_day.date()} ～ {last_day.date()}")
    except Exception:
        logging.exception("month の初日と末日を作成するところでエラー。")
        return

    # month の初日から末日までを、開始日から期日とする issue を作成します。
    try:
        issue = redmine.issue.create(
            project_id=project_id,
            subject=f"{issue_prefix} {month}",
            description="",
            start_date=first_day.date(),
            due_date=last_day.date(),
            assigned_to_id=user_id,
            tracker_id=1,
            status_id=1,
        )
        logging.info(f"登録終わり。 Issue 確認する?: {redmine_url}/issues/{issue.id}")

    except Exception:
        logging.exception("Issue 作成に失敗したわ。")


if __name__ == "__main__":
    args = _parse_args()
    main(
        redmine_url=args.url,
        redmine_api_key=args.key,
        project_id=args.project,
        issue_prefix=args.prefix,
        month=args.month,
    )
