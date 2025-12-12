"""
bye_bye_manual_redmine
"""

import argparse
import logging

import pandas as pd
from redminelib import Redmine
from redminelib.resources.standard import Issue

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def _parse_args():
    parser = argparse.ArgumentParser(description="Redmine に Freee の勤怠データを同期するスクリプト")

    parser.add_argument("--url", required=True, help="Redmine の URL")
    parser.add_argument("--key", required=True, help="Redmine の API キー")
    parser.add_argument("--issues", nargs="+", required=True, help="Redmine の Issue 名 (複数可)")
    parser.add_argument("--time", nargs="+", type=float, required=True, help="Issue ごとの時間分配率 (複数可)")
    parser.add_argument("--activity", type=int, required=True, help="Redmine のアクティビティ ID")
    parser.add_argument("--freee", required=True, help="Freee の CSV ファイルパス")

    return parser.parse_args()


def _fetch_user_id(redmine: Redmine) -> int:
    user = redmine.user.get("current")
    return user.id


def _get_daily_work_hours(freee_csv_path: str) -> dict[str, float]:

    df = pd.read_csv(freee_csv_path)

    # `hh:mm` 形式の時間を h（小数）に変換
    def time_to_hours(time_str: str) -> float:
        if not isinstance(time_str, str):
            return 0.0
        try:
            hours, minutes = map(int, time_str.split(":"))
            return hours + minutes / 60
        except Exception:
            return 0.0

    df["総勤務時間"] = df["総勤務時間"].apply(time_to_hours)

    # 日付を 'YYYY-MM-DD' 形式に変換
    def normalize_date(date_str: str) -> str:
        from datetime import datetime
        # 例: '2025/8/21' や '2025-8-21' などを '2025-08-21' に
        for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        # どれにも合わなければそのまま返す（API でエラーになるはず）
        return date_str

    df["日付"] = df["日付"].apply(normalize_date)
    daily_work_hours = df.groupby("日付")["総勤務時間"].sum().to_dict()
    return daily_work_hours


def _get_issues(redmine: Redmine, issue_names: list[str], user_id: int) -> list[Issue]:
    issues = []
    for issue_name in issue_names:
        matching_issues = redmine.issue.filter(subject=issue_name, assigned_to_id=user_id)
        if len(matching_issues) == 0:
            # 見つからん -> メッセージ出して終了 (このプログラムは issue の作成を請け負わないから自分で作って)。
            logging.error(f"Issue が見つからない: '{issue_name}'")
            logging.info(f"このプログラムは issue の作成を請け負わないから自分で作って: {redmine.url}/projects")
            return
        elif len(matching_issues) > 1:
            # 想定外に複数の Issue が見つかった場合
            # english
            logging.error(f"Issue が複数見つかった。非想定だからやり直して: '{issue_name}'")
            for issue in matching_issues:
                logging.info(f"Matching: {redmine.url}/issues/{issue.id} : {issue.subject}")
            return
        # 1つだけ見つかった -> OK
        issues.append(matching_issues[0])
    return issues


def _fetch_existing_time_entries(redmine: Redmine, issue: Issue) -> dict[str, float]:
    # Issue に登録済みの時間を取得。
    # daily_work_hours と同じく {yyyy-mm-dd: hours} の形式で取得する。
    existing_time_entries = {}
    for entry in redmine.time_entry.filter(issue_id=issue.id):
        entry_date = entry.spent_on.strftime("%Y-%m-%d")
        existing_time_entries[entry_date] = existing_time_entries.get(entry_date, 0) + entry.hours
    return existing_time_entries


def main(
    redmine_url: str,
    redmine_api_key: str,
    freee_csv_path: str,
    redmine_issue_names: list[str],
    time_distribution: list[float],
    activity_id: int,
    dry_run: bool = False,
) -> None:
    redmine = Redmine(redmine_url, key=redmine_api_key)

    # Redmine から自分の id を取得します。 (/users/current)
    try:
        user_id = _fetch_user_id(redmine)
        logging.info(f"User ID 見つかったよ: {user_id}")
    except Exception:
        logging.exception(f"User ID 取得に失敗。 API key を確認せよ: '{redmine_api_key}'")
        return

    # 見つからん -> メッセージ出して終了。
    # NOTE: と思ったが API key を指定しているのだからユーザは絶対あるはず。

    # Freee の CSV を読み込みます。
    # 日付 : 勤務時間 を取得します。
    try:
        daily_work_hours = _get_daily_work_hours(freee_csv_path)
        logging.info("CSV から、日付と総勤務時間を取得成功。")
    except Exception:
        logging.exception(f"CSV からの情報取得に失敗。 CSV フォーマットを確認して: '{freee_csv_path}'")
        return

    # Issue の数と時間の数が一致することを引数チェック。
    if len(redmine_issue_names) != len(time_distribution):
        logging.error(
            f"引数がおかしい。 Redmine issue names: {len(redmine_issue_names)};"
            f" Time distributions: {len(time_distribution)}"
        )
        return

    # Issue を取得する。
    issues = _get_issues(redmine, redmine_issue_names, user_id)

    # さて、 issue 1個ずつ、時間を登録していく。
    for issue, ratio in zip(issues, time_distribution):
        # Issue に登録済みの時間を取得。
        # daily_work_hours と同じく {yyyy-mm-dd: hours} の形式で取得する。
        existing_time_entries = _fetch_existing_time_entries(redmine, issue)

        # CSV のデータ、1件目から順番に処理。
        for date, work_hours in daily_work_hours.items():
            # Issue に時間が登録済み -> スキップ。
            # NOTE: このプログラムはあくまで空っぽのところを埋める自動化スクリプト。
            if date in existing_time_entries:
                logging.info(f"Issue {issue.id} : {date} : すでに時間が登録済み -> スキップ。")
                continue

            # この issue に登録する時間は work_hours * time_distribution で計算。
            allocated_hours = round(work_hours * ratio, 2)
            if allocated_hours <= 0:
                logging.info(f"Issue {issue.id} : {date} : 0時間 -> スキップ")
                continue

            # 登録する。
            if dry_run:
                logging.info(f"[DRY RUN] Issue {issue.id} : {date} : {allocated_hours} 時間を登録予定。")
                continue
            redmine.time_entry.create(
                issue_id=issue.id, spent_on=date, hours=allocated_hours, activity_id=activity_id, comments=""
            )
            logging.info(f"Issue {issue.id} : {date} : {allocated_hours} 時間を登録したよ。")

    # 扱った issue の URL を出力して、「ここで確認できるよ」って示す。
    for issue in issues:
        logging.info(f"登録終わり。 Issue 確認する?: {redmine_url}/issues/{issue.id}")


if __name__ == "__main__":
    args = _parse_args()
    main(
        redmine_url=args.url,
        redmine_api_key=args.key,
        freee_csv_path=args.freee,
        redmine_issue_names=args.issues,
        time_distribution=args.time,
        activity_id=args.activity,
        dry_run=False,
    )
