# DB設計書 v0.1

## 1. DB基本情報

| 項目 | 内容 |
|---|---|
| DBMS | Microsoft SQL Server |
| サーバー | MSI\SQLEXPRESS |
| DB名 | CryptoBot |
| 認証 | Windows認証 |

## 2. テーブル一覧

| テーブル | 概要 |
|---|---|
| bot_status | Bot稼働状態、取引有効フラグ、緊急停止 |
| market_prices | 取得した現在価格 |
| candles | ローソク足 |
| signals | シグナル履歴 |
| orders | 注文履歴、仮想注文履歴 |
| executions | 約定履歴 |
| positions | 保有ポジション |
| trades | 決済済み取引 |
| balances | 残高・推定総資産 |
| risk_events | リスク検知イベント |
| notifications | LINEなどの通知履歴 |
| system_logs | システムログ |
| settings | DB管理の設定値 |

## 3. 初期データ

`sql/002_insert_initial_settings.sql` で以下を登録する。

### bot_status

| status | is_trading_enabled | emergency_stop | reason |
|---|---:|---:|---|
| STOPPED | 0 | 0 | 初期状態 |

### settings主要値

| key | value | 内容 |
|---|---|---|
| exchange_name | coincheck | 対象取引所 |
| symbol | BTC_JPY | 対象通貨ペア |
| order_amount_jpy | 5000 | 1回あたり注文金額 |
| take_profit_rate | 0.005 | 利確率 |
| stop_loss_rate | 0.007 | 損切り率 |
| max_daily_loss_rate | 0.03 | 1日最大損失率 |
| max_consecutive_losses | 3 | 連続損切り停止回数 |
| main_loop_interval_seconds | 60 | メインループ間隔 |
| line_notify_enabled | true | LINE通知有効 |

## 4. 重要テーブル仕様

### 4.1 bot_status

Bot全体の稼働制御に使う。

- `is_trading_enabled = 0` の場合、取引処理を止める。
- `emergency_stop = 1` の場合、緊急停止扱いにする。

### 4.2 market_prices

Public APIで取得した価格を保存する。

ローソク足生成の元データになる。

### 4.3 candles

時間足別のOHLCVを保存する。

ユニークキー：`symbol`, `timeframe`, `started_at`

### 4.4 orders

注文履歴を保存する。

初期版では実注文ではなく仮想注文もここに保存する方針。

### 4.5 positions

保有中ポジションを保存する。

`status = OPEN` のものが存在する場合、新規買いは原則見送る。

### 4.6 trades

決済済み取引を保存する。

損益、手数料、利益率を保持する。

### 4.7 system_logs

システムログをDBに保存する。

現在のカラムは以下。

- id
- log_level
- category
- message
- detail
- created_at

注意：以前 `module_name` を使ったINSERTで失敗している。現在の正しいカラムは `category`。

## 5. SQL実行順

```text
1. sql/001_create_tables.sql
2. sql/002_insert_initial_settings.sql
```

## 6. 確認用SQL

```sql
SELECT * FROM dbo.bot_status;
SELECT COUNT(*) FROM dbo.market_prices;
SELECT TOP 10 * FROM dbo.system_logs ORDER BY id DESC;
```
