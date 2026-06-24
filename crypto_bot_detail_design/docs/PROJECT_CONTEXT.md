# PROJECT_CONTEXT

## プロジェクト概要

このリポジトリは、仮想通貨自動売買システム「一攫千金くん」です。

Python、Microsoft SQL Server、Coincheck API、LINE Messaging APIを使い、価格取得、シグナル判定、注文管理、ポジション管理、LINE通知を行うことを目指します。

## 現在の開発段階

要件定義、基本設計、詳細設計、環境構築、DB接続確認は完了済み。

現在は、実注文ではなくペーパートレード実装に進む段階です。

## 現在できていること

- Python仮想環境の作成
- SQL ServerへのWindows認証接続
- `system_logs` へのINSERT確認
- 全テーブルSELECT確認
- `bot_status` の読み取り
- `main.py` の起動確認
- 自動売買OFF時に停止する処理
- Coincheck Public API `get_ticker()` の実装雛形
- SMA / RSI / MACDの計算雛形
- 売買判断ロジックの雛形

## 重要な環境情報

| 項目 | 内容 |
|---|---|
| OS | Windows |
| DB | Microsoft SQL Server Express |
| DBサーバー | MSI\SQLEXPRESS |
| DB名 | CryptoBot |
| DB認証 | Windows認証 |
| Python仮想環境 | .venv |
| 初期対象通貨 | BTC_JPY |
| 取引所 | Coincheck |

## .env方針

現在の想定：

```env
DB_DRIVER=ODBC Driver 17 for SQL Server
DB_SERVER=MSI\SQLEXPRESS
DB_NAME=CryptoBot
DB_AUTH=windows

COINCHECK_BASE_URL=https://coincheck.com
COINCHECK_ACCESS_KEY=
COINCHECK_SECRET_KEY=

LINE_CHANNEL_ACCESS_TOKEN=
LINE_USER_ID=

TRADING_ENABLED=false
ORDER_AMOUNT_JPY=5000
TAKE_PROFIT_RATE=0.005
STOP_LOSS_RATE=0.007
MAIN_LOOP_INTERVAL_SECONDS=60
```

`.env` はGitHubにコミットしない。

## まだ実装しないこと

以下はまだ実装・実行しない。

- Coincheck Private APIによる実注文
- 成行買い注文
- 成行売り注文
- 指値利確注文
- 注文キャンセル
- 実資金での自動売買

## 次に実装すること

```text
1. Coincheck Public APIで価格取得
2. market_pricesテーブルへ保存
3. ローソク足生成
4. 売買シグナル判定
5. 仮想注文としてDB保存
6. LINE通知
```

## 安全方針

- 最初は必ずペーパートレード。
- 実注文APIは最後まで作らない。
- APIキーやトークンは.envに置き、GitHubには上げない。
- bot_status.is_trading_enabledが0なら処理停止。
- emergency_stopが1なら処理停止。
- 注文系APIは、二重注文防止と約定確認ができるまで実装しない。

## Codexへの注意

このプロジェクトでは、実注文APIの実装を急がないこと。
まずはPublic API、DB保存、ローソク足、シグナル、仮想注文、通知を完成させること。
