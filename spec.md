設計図
===

## やりてぃこと

- Freee 人事労務の日時データ (csv) をゲットする
- 日ごとの 総勤務時間 を取得する
    - (これを Redmine へ自動で 時間データ として送り込むのが目標)
    - (そのまま送り込むんではなくて、 A project : B project : C project = 80% : 10% : 10% みたいな感じで分配)

## 設計図

- Redmine から自分の id を取得する

```bash
curl --location '.../users/current.json' \
--header 'X-Redmine-API-Key: ••••••'
```

- Redmine から指定した issue を取得する

```bash
curl --location '.../issues.json?assigned_to_id=5&subject=Aproject' \
--header 'X-Redmine-API-Key: ••••••'
```

- 存在しないなら issue を作る
    - ……は、いらねーか。 issue はちゃんと手作業で作ってくらはい。
- Redmine から issue の時間データを取得する

```bash
curl --location '.../time_entries.json?issue_id=721' \
--header 'X-Redmine-API-Key: ••••••'
```

- すでに登録済みかどうかを確認する
    - (Python ちゃんが頑張る)
- Redmine へ時間データを送り込む……前に、 activity_id を取得する

```bash
curl --location '.../enumerations/time_entry_activities.json' \
--header 'X-Redmine-API-Key: ••••••'
```

- Redmine へ時間データを送り込む

```bash
curl --location '.../time_entries.json' \
--header 'Content-Type: application/json' \
--header 'X-Redmine-API-Key: ••••••' \
--data '{
  "time_entry": {
    "issue_id": 721,
    "spent_on": "2025-01-29",
    "hours": 3.5,
    "activity_id": 9,
    "comments": "SAMPLE!"
  }
}'
```
