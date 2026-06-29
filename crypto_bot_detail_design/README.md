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

`.env.example` が更新された場合は、以下のBATで `.env` を作り直せる。
既存の `COINCHECK_ACCESS_KEY` と `COINCHECK_SECRET_KEY` は自動で引き継ぐ。

```text
refresh_env_from_example.bat
```

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

## GUIで実行

以下で操作パネルを起動できる。

```bash
python gui.py
```

GUIでは、DB接続確認、Coincheck価格取得、Coincheck残高取得、テスト実行、少額実注文テスト、CSVローソク足取込、ローソク足バックテスト、1回だけ実行、定期実行の開始・停止ができる。
実注文を許可する `TRADING_ENABLED=true` の場合は画面上に警告表示される。

バックテストでは、CSVなどで用意したローソク足データをDBへ保存し、DB上のローソク足で仮想売買を行う。
バックテスト処理は注文APIを呼ばない。

GUIでの基本手順:

1. `CSVローソク足取込` でOHLCV CSVをDBへ保存する。
2. `ローソク足件数` で保存件数と期間を確認する。
3. 戦略を選択する。
4. `ローソク足BT` でDB上のローソク足データを使って検証する。

選択できる戦略:

- `sma_rsi_trend`: 現在の標準戦略。5分足・15分足SMA上向き、かつ5分足RSI 70未満で買う。
- `sma_cross_only`: RSI条件を外し、5分足・15分足SMA上向きだけで買う。
- `rsi_oversold`: 5分足RSI 30以下で買う逆張り戦略。

`.env` の `STRATEGY_NAME` でも標準戦略を切り替えられる。

コマンドでバックテストする場合:

```bash
python import_historical_candles.py path\to\candles.csv --timeframe 5m
python backtest.py
```

CSV形式は以下を想定する。

```csv
started_at,open,high,low,close,volume
2026-06-01 00:00:00,15000000,15050000,14980000,15020000,12.34
```

初回のみ、SQL Serverにバックテスト用テーブルを追加するSQLも用意している。
GUIまたは `import_historical_candles.py` 実行時にも自動作成される。

```text
sql/004_create_historical_candles.sql
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

現在の `main.py` は、Coincheck価格を `market_prices` に保存し、そのデータから5分足・15分足を `candles` に作成して、選択中の戦略で売買判断する。
ただし実注文送信には `.env` の `TRADING_ENABLED=true` と、DBの `dbo.bot_status.is_trading_enabled=1` の両方が必要。

### 実運用前の推奨テスト順序

1. `.env` は `TRADING_ENABLED=false` のまま、GUIの `テスト実行` を押す。
2. GUIの `Coincheck価格` と `Coincheck残高` が成功することを確認する。
3. GUIの `1回だけ実行` を複数回実行し、`market_prices` と `candles` にデータが保存されることを確認する。
4. バックテスト用CSVを取り込み、`ローソク足BT` で戦略ごとの損益を確認する。
5. 実注文テストをする場合だけ `.env` の `TRADING_ENABLED=true`、DBの `bot_status.is_trading_enabled=1` にする。
6. GUIの `少額実注文テスト` で `LIVE_TEST_ORDER_AMOUNT_JPY` 円の成行買いを1回だけ試す。
7. 問題がなければ `ORDER_AMOUNT_JPY`、`TAKE_PROFIT_RATE`、`STOP_LOSS_RATE`、`STRATEGY_NAME` を調整してから定期実行を開始する。

追加された安全ガード:

- `MIN_ORDER_AMOUNT_JPY` 未満の買い注文は送信しない。
- `ORDER_COOLDOWN_SECONDS` 秒以内の同種注文は送信しない。
- 実注文前にJPY残高またはBTC残高を確認する。
- 売り注文時、DB上の保有数量が実残高より大きい場合は実残高まで自動で下げる。
- `MAX_DAILY_LOSS_JPY` を超える日次損失、または `MAX_CONSECUTIVE_LOSSES` 回の連敗で自動売買を止める。

## 注意

実注文は必ず小額で検証してから有効化すること。
`.env` はGitHubにコミットしないこと。
