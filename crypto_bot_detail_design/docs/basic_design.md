# 仮想通貨自動売買システム「一攫千金くん」基本設計書 v0.1

## 1. システム概要

「一攫千金くん」は、Coincheckから仮想通貨価格を取得し、複数時間足のシグナルをもとに売買判断を行うPython製の自動売買システムである。

初期版では、実注文ではなくペーパートレードを優先する。価格取得、DB保存、シグナル判定、仮想注文、LINE通知までを先に完成させる。

## 2. 全体構成

```text
[Coincheck Public API]
        |
        v
[exchange_client.py]
        |
        v
[market_data_service.py]
        |
        v
[SQL Server: market_prices]
        |
        v
[candle_service.py]
        |
        v
[signal_service.py]
        |
        v
[strategy_service.py]
        |
        v
[order_service.py]
        |
        v
[SQL Server: orders / positions / trades]
        |
        v
[line_notifier.py]
```

## 3. 技術構成

| 分類 | 採用技術 |
|---|---|
| 言語 | Python |
| DB | Microsoft SQL Server |
| DB接続 | pyodbc |
| 設定管理 | .env / python-dotenv |
| HTTP通信 | requests |
| テスト | pytest |
| 通知 | LINE Messaging API |
| 取引所API | Coincheck API |

## 4. フォルダ構成

```text
crypto_bot_detail_design/
├─ app/
│  ├─ asset/
│  ├─ common/
│  ├─ database/
│  ├─ exchange/
│  ├─ market/
│  ├─ notification/
│  ├─ order/
│  ├─ position/
│  ├─ risk/
│  └─ strategy/
├─ docs/
├─ sql/
├─ tests/
├─ config.py
├─ main.py
├─ requirements.txt
├─ README.md
├─ .env.example
└─ .gitignore
```

## 5. モジュール一覧

| モジュール | 役割 |
|---|---|
| main.py | 起動、メインループ、各サービス呼び出し |
| config.py | .envから設定を読み込む |
| app/database/db.py | DB接続、execute、fetch処理 |
| app/exchange/exchange_client.py | Coincheck API通信 |
| app/market/market_data_service.py | 現在価格取得、DB保存 |
| app/market/candle_service.py | ローソク足生成・取得 |
| app/strategy/signal_service.py | SMA、RSI、MACDなどの指標計算 |
| app/strategy/strategy_service.py | 売買判断 |
| app/order/order_service.py | 注文作成、注文記録 |
| app/position/position_service.py | 保有ポジション確認 |
| app/risk/risk_service.py | 取引停止、緊急停止判定 |
| app/asset/asset_service.py | 残高・総資産取得 |
| app/notification/line_notifier.py | LINE通知 |
| app/common/logger.py | ログ出力 |
| app/common/exceptions.py | 独自例外 |

## 6. DB構成

| テーブル | 用途 |
|---|---|
| bot_status | 自動売買ON/OFF、緊急停止状態 |
| market_prices | 取得した現在価格 |
| candles | ローソク足 |
| signals | シグナル履歴 |
| orders | 注文履歴。初期版では仮想注文も保存 |
| executions | 約定履歴 |
| positions | 保有ポジション |
| trades | 決済済み取引履歴 |
| balances | 残高・総資産履歴 |
| risk_events | リスク検知履歴 |
| notifications | 通知履歴 |
| system_logs | システムログ |
| settings | 各種設定値 |

## 7. 起動時処理

```text
1. .env読み込み
2. logger初期化
3. LINE起動通知
4. メインループ開始
5. risk_serviceで取引可否判定
6. 取引不可ならログ出力してその回は終了
7. 取引可能なら価格取得へ進む
```

## 8. 通常処理フロー

```text
1. bot_status確認
2. emergency_stop確認
3. Coincheck Public APIから価格取得
4. market_pricesへ保存
5. 保有ポジション確認
6. ローソク足生成
7. 指標計算
8. 売買判断
9. 仮想注文保存
10. LINE通知
```

## 9. 安全設計

- 初期状態では自動売買OFF。
- bot_status.is_trading_enabled = 0なら取引しない。
- bot_status.emergency_stop = 1なら取引しない。
- 実注文APIは未実装のままにする。
- 実注文を実装する前に、ペーパートレードでDB保存と通知を検証する。
- Private APIの書き込み系は最後に実装する。

## 10. API方針

### Public API

初期実装対象。

- ticker取得
- 板情報取得
- ローソク足CSV取込によるバックテストデータ作成

### Private API

後続実装対象。

- 残高取得
- 未約定注文一覧
- 注文履歴
- 買い注文
- 売り注文
- キャンセル

## 11. 初期開発順序

```text
1. DB接続確認
2. system_logs INSERT確認
3. bot_status確認
4. main.py起動確認
5. Coincheck Public API価格取得
6. market_prices INSERT
7. CandleService実装
8. SignalServiceとStrategyService接続
9. PaperOrderServiceまたはOrderServiceで仮想注文保存
10. LINE通知
```
