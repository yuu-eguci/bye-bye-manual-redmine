"""
bye_bye_manual_redmine.fetch_projects
"""

import argparse
import logging

from redminelib import Redmine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def _parse_args():
    parser = argparse.ArgumentParser(description="Redmine に登録されている projects をゲットするスクリプト")

    parser.add_argument("--url", required=True, help="Redmine の URL")
    parser.add_argument("--key", required=True, help="Redmine の API キー")

    return parser.parse_args()


def main(
    redmine_url: str,
    redmine_api_key: str,
) -> None:
    redmine = Redmine(redmine_url, key=redmine_api_key)

    # Redmine から自分の id を取得します。 (/users/current)
    try:
        user = redmine.user.get("current")
        user_id = user.id
        logging.info(f"User ID 見つかったよ: {user_id}")
    except Exception:
        logging.exception(f"User ID 取得に失敗。 API key を確認せよ: '{redmine_api_key}'")
        return

    projects = [project for project in redmine.project.all()]
    project_dict = {project.id: project.name for project in projects}

    for project_id, project_name in project_dict.items():
        logging.info(f"{project_id}: {project_name}")

    return project_dict


if __name__ == "__main__":
    args = _parse_args()
    main(
        redmine_url=args.url,
        redmine_api_key=args.key,
    )
