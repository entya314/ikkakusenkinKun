# 実装状況メモ v0.1

## 1. 完了済み

- プロジェクト雛形作成
- app配下の機能別フォルダ作成
- requirements.txt作成
- .env / .env.example作成
- SQL Serverテーブル作成SQL作成
- 初期設定INSERT SQL作成
- DB接続テスト作成
- テーブルSELECTテスト作成
- system_logs INSERTテスト作成
- main.py起動確認
- bot_statusによる取引停止確認
- SignalServiceのSMA / RSI / MACD雛形
- StrategyServiceの買い判定・決済判定雛形
- pytest用テスト一部作成

## 2. 動作確認済み

### 2.1 DB接続

Windows認証で `MSI\SQLEXPRESS` の `CryptoBot` へ接続確認済み。

### 2.2 system_logs INSERT

`system_logs` へINSERT成功済み。

### 2.3 main.py起動

以下のログが出ている。

```text
一攫千金くん 起動
取引停止: DB上で自動売買が無効
```

これは正常。DB上の `bot_status.is_trading_enabled` が0のため停止している。

## 3. 修正済みまたは修正方針あり

### 3.1 config.py

元のconfig.pyは `.env` の `DB_NAME` ではなく `DB_DATABASE` を読んでいた。

現在の方針は以下。

```env
DB_SERVER=MSI\SQLEXPRESS
DB_NAME=CryptoBot
DB_AUTH=windows
```

Windows認証時は `UID` / `PWD` を接続文字列に入れない。

## 4. 未実装

- CandleServiceによるローソク足生成
- Coincheck Public API価格取得後の安定保存確認
- シグナル判定結果のDB保存
- 仮想注文保存処理
- LINE通知の本格確認
- 残高取得
- 約定確認
- 実注文API
- 注文キャンセルAPI
- 二重注文防止
- 日次損失停止
- 連続損切り停止
- 急変動停止

## 5. Coincheck API実装状態

- Public API `get_ticker()` は実装済み。
- Private API `get_balance()` は骨組みあり。
- 実注文APIは未実装。

未実装メソッド：

```text
create_market_buy_order
create_limit_sell_order
create_market_sell_order
```

## 6. 次にやること

```text
1. config.pyをDB_NAME / Windows認証対応版に差し替える
2. main.py起動確認
3. bot_statusを検証用にONにする
4. Coincheck Public APIで価格取得
5. market_pricesへのINSERT確認
6. CandleService実装
7. SignalService / StrategyServiceをmain.pyへ組み込む
8. 仮想注文をordersへ保存
9. LINE通知
```

## 7. やってはいけないこと

- いきなり実注文APIを実装して本番投入しない。
- `.env` をGitHubへ上げない。
- `.venv` をGitHubへ上げない。
- 自動売買ONのまま未検証コードを動かさない。
