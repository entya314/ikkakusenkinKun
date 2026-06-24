# 環境構築手順書 v0.1

## 1. 前提

この手順書は、Windows環境で仮想通貨自動売買システム「一攫千金くん」を動かすための手順である。

## 2. 使用環境

| 項目 | 内容 |
|---|---|
| OS | Windows |
| 言語 | Python |
| DB | Microsoft SQL Server Express |
| DBサーバー | MSI\SQLEXPRESS |
| DB名 | CryptoBot |
| 認証 | Windows認証 |
| 仮想環境 | venv |

## 3. 事前準備

以下をインストールしておく。

- Python
- Microsoft SQL Server Express
- SQL Server Management Studio
- ODBC Driver 17 または 18 for SQL Server
- Git

## 4. プロジェクト取得

GitHubからリポジトリを取得する。

```bash
cd D:\MyWorkSpace\Programing\AIPython
git clone <repository-url> crypto_bot_detail_design
cd crypto_bot_detail_design
```

すでに取得済みの場合は、対象フォルダへ移動する。

```bash
cd D:\MyWorkSpace\Programing\AIPython\crypto_bot_detail_design
```

## 5. Python仮想環境作成

```bash
python -m venv .venv
```

仮想環境を有効化する。

```bash
.venv\Scripts\activate
```

有効化されると、プロンプト先頭に以下のように表示される。

```text
(.venv) D:\MyWorkSpace\Programing\AIPython\crypto_bot_detail_design>
```

## 6. ライブラリインストール

```bash
pip install -r requirements.txt
```

## 7. .env作成

`.env.example` をコピーして `.env` を作成する。

```bash
copy .env.example .env
```

Windows認証で `MSI\SQLEXPRESS` に接続する場合、`.env` は以下を基本形とする。

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

注意：`.env` はGitHubへコミットしない。

## 8. DB作成

SQL Server Management Studioで以下を実行し、DBを作成する。

```sql
CREATE DATABASE CryptoBot;
```

作成後、対象DBを `CryptoBot` に切り替える。

## 9. テーブル作成

以下の順番でSQLを実行する。

```text
sql/001_create_tables.sql
sql/002_insert_initial_settings.sql
```

## 10. DB接続確認

```bash
python tests/test_db_connection.py
```

成功例：

```text
DB接続成功
サーバー名: MSI\SQLEXPRESS
DB名: CryptoBot
```

## 11. テーブルSELECT確認

```bash
python tests/test_table_select.py
```

成功例：

```text
テーブルSELECT確認開始
balances: 0件
bot_status: 1件
...
全テーブルSELECT成功
```

## 12. system_logs INSERT確認

```bash
python tests/test_insert_system_log.py
```

成功例：

```text
system_logs INSERT成功
```

## 13. main.py起動確認

```bash
python main.py
```

自動売買OFFの場合は以下のような表示になる。

```text
一攫千金くん 起動
取引停止: DB上で自動売買が無効
```

これは正常。DBの `bot_status.is_trading_enabled` が0のため停止している。

## 14. 自動売買フラグ確認

```sql
SELECT * FROM dbo.bot_status;
```

検証でONにする場合：

```sql
UPDATE dbo.bot_status
SET is_trading_enabled = 1,
    status = N'RUNNING',
    reason = N'検証用に有効化',
    updated_at = SYSDATETIME()
WHERE id = 1;
```

ただし、実注文APIが完成するまでは、実注文を出さない設計にすること。

## 15. よくある注意点

### DB_NAMEとDB_DATABASEの不一致

現在の.envは `DB_NAME=CryptoBot` を使う方針。config.py側も `DB_NAME` を読むように合わせる。

### Windows認証の場合

`DB_USER` と `DB_PASSWORD` は不要。接続文字列には `Trusted_Connection=yes;` を使う。

### ODBC Driver 18の場合

証明書エラーが出る場合は `TrustServerCertificate=yes;` を付ける。

## 16. GitHubに入れないもの

```gitignore
.venv/
.env
__pycache__/
*.pyc
*.log
.vs/
```
