# Codex引き継ぎ用プロンプト

以下をCodexの最初の指示として使う。

```text
このリポジトリは仮想通貨自動売買システム「一攫千金くん」です。

まず以下のファイルを読んでください。

- README.md
- PROJECT_CONTEXT.md
- docs/requirements_definition.md
- docs/basic_design.md
- docs/detail_design.md
- docs/environment_setup.md
- docs/implementation_status.md
- config.py
- main.py
- sql/001_create_tables.sql
- sql/002_insert_initial_settings.sql

現在の段階では、実注文APIは実装しないでください。
Coincheck Private APIの注文系、つまり成行買い、指値売り、成行売り、キャンセルはまだ触らないでください。

次にやることは、Coincheck Public APIで価格を取得し、market_pricesテーブルに保存する処理の確認・改善です。
その後、CandleServiceで5分足・15分足を生成し、SignalService / StrategyServiceにつなげて、仮想注文をordersテーブルに保存するところまで進めます。

安全方針：
- 実資金の注文は出さない
- 最初はペーパートレードのみ
- .envはGitHubに上げない
- DBはSQL Server、Windows認証、サーバーは MSI\SQLEXPRESS、DB名は CryptoBot
- config.pyはDB_NAMEを読み、Windows認証ではUID/PWDを使わない

まず、現在のコード構成を要約し、次に必要な変更点を小さなステップで提案してください。
```
