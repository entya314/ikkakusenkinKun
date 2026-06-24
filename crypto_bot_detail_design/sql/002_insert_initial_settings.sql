/*
初期設定値投入SQL
*/

INSERT INTO dbo.bot_status (status, is_trading_enabled, emergency_stop, reason)
VALUES (N'STOPPED', 0, 0, N'初期状態');
GO

INSERT INTO dbo.settings (setting_key, setting_value, description)
VALUES
(N'exchange_name', N'coincheck', N'対象取引所'),
(N'symbol', N'BTC_JPY', N'対象通貨ペア'),
(N'base_symbol', N'BTC', N'購入対象通貨'),
(N'quote_symbol', N'JPY', N'決済通貨'),
(N'trading_enabled', N'false', N'自動売買有効フラグ'),
(N'order_amount_jpy', N'5000', N'1回あたりの注文金額'),
(N'take_profit_rate', N'0.005', N'利確率'),
(N'stop_loss_rate', N'0.007', N'損切り率'),
(N'max_daily_loss_rate', N'0.03', N'1日最大損失率'),
(N'max_consecutive_losses', N'3', N'連続損切り停止回数'),
(N'api_retry_count', N'3', N'APIリトライ回数'),
(N'api_retry_interval_seconds', N'5', N'APIリトライ間隔'),
(N'main_loop_interval_seconds', N'60', N'メインループ間隔秒'),
(N'price_change_stop_rate_5m', N'0.02', N'5分急変動停止率'),
(N'line_notify_enabled', N'true', N'LINE通知有効フラグ');
GO
