# API設計メモ v0.1

## 1. 方針

Coincheck APIはPublic APIとPrivate APIに分けて扱う。

初期実装ではPublic APIのみを使う。Private API、特に注文系はペーパートレードが安定してから実装する。

## 2. Public API

### 2.1 用途

- 現在価格取得
- 板情報取得
- 取引履歴取得
- ローソク足生成の元データ取得

### 2.2 初期実装対象

| 処理 | 用途 | 実装場所 |
|---|---|---|
| ticker取得 | 現在価格、bid、ask、volume取得 | exchange_client.py / market_data_service.py |

### 2.3 DB保存先

`dbo.market_prices`

保存項目：

- exchange
- symbol
- price
- bid
- ask
- volume
- collected_at

## 3. Private API

### 3.1 用途

- 残高取得
- 未約定注文確認
- 注文履歴確認
- 買い注文
- 売り注文
- キャンセル

### 3.2 実装順

```text
1. 残高取得
2. 未約定注文確認
3. 注文履歴確認
4. キャンセル
5. 成行買い
6. 指値売り
7. 成行売り
```

### 3.3 実装しない段階

以下が完成するまでは実注文APIを書かない。

- 価格取得
- DB保存
- ローソク足生成
- シグナル判定
- 仮想注文
- LINE通知
- 二重注文防止
- 緊急停止

## 4. 認証情報

Private APIの認証情報は `.env` に置く。

```env
COINCHECK_ACCESS_KEY=
COINCHECK_SECRET_KEY=
```

`.env` はGitHubにコミットしない。

## 5. エラー処理方針

- API失敗時は例外を発生させる。
- main.py側でログに残す。
- 連続失敗時はrisk_eventsへ記録する。
- 注文系API失敗時は成功扱いしない。
- LINE通知は送信失敗しても売買処理の成功扱いとは分離する。

## 6. 二重注文防止

実注文前に以下を確認する。

- bot_statusが取引有効か
- emergency_stopがOFFか
- open positionがないか
- 未約定注文がないか
- 同一シグナルで直近注文済みではないか

## 7. 現在の実装状態

- `get_ticker()` は実装済み。
- `get_balance()` は骨組みあり。ただしPrivate API認証情報が必要。
- `create_market_buy_order()` は未実装。
- `create_limit_sell_order()` は未実装。
- `create_market_sell_order()` は未実装。
