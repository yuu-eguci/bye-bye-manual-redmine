"""
bye_bye_manual_redmine.fetch_activities
"""

import argparse
import logging

from redminelib import Redmine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def _parse_args():
    parser = argparse.ArgumentParser(description="Redmine に登録されている activities をゲットするスクリプト")

    parser.add_argument("--url", required=True, help="Redmine の URL")
    parser.add_argument("--key", required=True, help="Redmine の API キー")

    return parser.parse_args()


def main(
    redmine_url: str,
    redmine_api_key: str,
) -> None:
    try:
        redmine = Redmine(redmine_url, key=redmine_api_key)

        # アクティビティを取得 (/enumerations/time_entry_activities)
        activities = redmine.enumeration.filter(resource="time_entry_activities")

        # {id: name} の形式で。
        active_activities = {activity.id: activity.name for activity in activities if getattr(activity, "active", True)}

        logging.info(
            "ステータスがアクティブであるアクティビティ一覧を取得したよ。こっから id をコピーして、 main.py に使ってね:"
        )
        for activity_id, activity_name in active_activities.items():
            logging.info(f"{activity_id}: {activity_name}")

        return active_activities

    except Exception:
        logging.exception("アクティビティ一覧の取得に失敗。 Redmine の設定を確認して。")


if __name__ == "__main__":
    args = _parse_args()
    main(
        redmine_url=args.url,
        redmine_api_key=args.key,
    )
