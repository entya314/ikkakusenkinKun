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

## Coincheck実注文の有効化

注文APIは `app/exchange/exchange_client.py` に実装済み。
初期状態では誤発注防止のため `.env` の `TRADING_ENABLED=false` を推奨する。

実注文を出すには、以下をすべて満たすこと。

1. CoincheckでAPIキーを作成し、注文と残高参照に必要な権限を付与する。
2. 可能であればAPIキーに接続元IP制限を設定する。
3. `.env` に `COINCHECK_ACCESS_KEY` と `COINCHECK_SECRET_KEY` を設定する。
4. 注文金額を `ORDER_AMOUNT_JPY` で小額に設定する。
5. `.env` の `TRADING_ENABLED=true` にする。
6. DBの `dbo.bot_status.is_trading_enabled` を `1` にする。

注意: `main.py` は現時点では売買判断を注文実行へ接続していない。
`OrderService` が呼ばれた場合のみ、`TRADING_ENABLED=true` で実注文が送信される。

## 注意

実注文は必ず小額で検証してから有効化すること。
`.env` はGitHubにコミットしないこと。
