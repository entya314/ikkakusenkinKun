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

GUIでは、DB接続確認、Coincheck価格取得、Coincheck残高取得、APIテスト実行、履歴取得/保存、DBバックテスト、1回だけ実行、定期実行の開始・停止ができる。
実注文を許可する `TRADING_ENABLED=true` の場合は画面上に警告表示される。

バックテストでは、先にCoincheckの公開取引履歴をDBへ保存し、DB上の履歴データで仮想売買を行う。
バックテスト処理は注文APIを呼ばない。

GUIでの基本手順:

1. `履歴取得/保存` でCoincheck公開取引履歴をDBへ保存する。
2. `DB履歴件数` で保存件数と期間を確認する。
3. 戦略を選択する。
4. `DBバックテスト` でDB上の履歴データを使って検証する。

選択できる戦略:

- `sma_rsi_trend`: 現在の標準戦略。5分足・15分足SMA上向き、かつ5分足RSI 70未満で買う。
- `sma_cross_only`: RSI条件を外し、5分足・15分足SMA上向きだけで買う。
- `rsi_oversold`: 5分足RSI 30以下で買う逆張り戦略。

`.env` の `STRATEGY_NAME` でも標準戦略を切り替えられる。

コマンドでバックテストする場合:

```bash
python fetch_historical_trades.py
python backtest.py
```

APIからDBへ保存する取得件数は `.env` の `BACKTEST_TRADE_LIMIT` で調整する。
Coincheckの現在の取引履歴APIではページング指定が使えないため、直近取得分で検証する。

初回のみ、SQL Serverにバックテスト用テーブルを追加するSQLも用意している。
GUIまたは `fetch_historical_trades.py` 実行時にも自動作成される。

```text
sql/003_create_historical_trades.sql
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
