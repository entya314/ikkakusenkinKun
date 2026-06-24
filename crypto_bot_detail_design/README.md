# 仮想通貨自動売買システム「一攫千金くん」雛形

## 内容

- `docs/detail_design.md`：詳細設計書
- `sql/001_create_tables.sql`：SQL Serverテーブル作成SQL
- `sql/002_insert_initial_settings.sql`：初期設定INSERT SQL
- `app/`：Python実装用の雛形

## 初期セットアップ

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

`.env` にSQL Server、Coincheck、LINEの設定を入れる。

## DB作成

SQL Server上で対象DBを作成後、以下の順で実行する。

```text
sql/001_create_tables.sql
sql/002_insert_initial_settings.sql
```

## 実行

```bash
python main.py
```

## 注意

この雛形はまだ実注文を完成させていない。  
本番注文処理は `app/exchange/exchange_client.py` と `app/order/order_service.py` の TODO を実装し、少額で検証してから有効化すること。

初期状態では `.env` の `TRADING_ENABLED=false` を推奨する。
