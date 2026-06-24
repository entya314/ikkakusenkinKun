# 次タスク一覧 v0.1

## 最優先

### 1. GitHub用ファイル整理

- `.env` をGitHubから除外する。
- `.venv/` を除外する。
- `.vs/` を除外する。
- `__pycache__/` を除外する。
- `.gitignore` を確認する。

推奨 `.gitignore`：

```gitignore
.venv/
.env
__pycache__/
*.pyc
*.log
.vs/
```

### 2. PROJECT_CONTEXT.mdをリポジトリ直下へ追加

Codexに最初に読ませるため、リポジトリ直下に置く。

## 次に実装

### 3. Coincheck Public API価格取得確認

目的：`main.py` から `get_ticker()` を呼び、`market_prices` に保存できることを確認する。

完了条件：

```sql
SELECT TOP 10 *
FROM dbo.market_prices
ORDER BY id DESC;
```

で価格データが確認できる。

### 4. CandleService実装

目的：`market_prices` から5分足、15分足を生成する。

完了条件：

```sql
SELECT TOP 10 *
FROM dbo.candles
ORDER BY id DESC;
```

でローソク足が確認できる。

### 5. SignalService連携

目的：ローソク足終値からSMA、RSI、MACDを算出する。

完了条件：

- 5分足指標が出る。
- 15分足指標が出る。
- データ不足時はHOLDになる。

### 6. StrategyService連携

目的：買い条件・売り条件を判定する。

初期買い条件：

- 5分足SMA短期 > SMA長期
- 15分足SMA短期 > SMA長期
- 5分足RSI < 70
- open positionなし

### 7. 仮想注文保存

目的：実注文ではなくordersへ仮想注文を保存する。

注文status例：

```text
PAPER_FILLED
```

purpose例：

```text
ENTRY
TAKE_PROFIT
STOP_LOSS
```

### 8. LINE通知

目的：仮想注文の発生をLINEへ通知する。

## 後回し

- 残高取得
- 未約定注文確認
- 注文履歴確認
- 実注文API
- GUI
- パラメータ自動調整

## Codexへの初回指示文

```text
このリポジトリは仮想通貨自動売買システム「一攫千金くん」です。
まず README.md、PROJECT_CONTEXT.md、docs/配下、config.py、main.py、sql/配下を読んで、現在の実装状況を把握してください。

現時点では実注文APIは実装しないでください。
次の作業は、Coincheck Public APIで価格を取得し、market_pricesテーブルへ保存する処理の確認・改善です。

既存設計に合わせて、最小変更で実装案を出してください。
```
