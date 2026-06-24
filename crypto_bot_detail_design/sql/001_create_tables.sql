/*
仮想通貨自動売買システム「一攫千金くん」
SQL Server DDL v0.1

実行順:
1. 001_create_tables.sql
2. 002_insert_initial_settings.sql
*/

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

IF OBJECT_ID('dbo.bot_status', 'U') IS NOT NULL DROP TABLE dbo.bot_status;
IF OBJECT_ID('dbo.notifications', 'U') IS NOT NULL DROP TABLE dbo.notifications;
IF OBJECT_ID('dbo.system_logs', 'U') IS NOT NULL DROP TABLE dbo.system_logs;
IF OBJECT_ID('dbo.risk_events', 'U') IS NOT NULL DROP TABLE dbo.risk_events;
IF OBJECT_ID('dbo.trades', 'U') IS NOT NULL DROP TABLE dbo.trades;
IF OBJECT_ID('dbo.positions', 'U') IS NOT NULL DROP TABLE dbo.positions;
IF OBJECT_ID('dbo.executions', 'U') IS NOT NULL DROP TABLE dbo.executions;
IF OBJECT_ID('dbo.orders', 'U') IS NOT NULL DROP TABLE dbo.orders;
IF OBJECT_ID('dbo.signals', 'U') IS NOT NULL DROP TABLE dbo.signals;
IF OBJECT_ID('dbo.candles', 'U') IS NOT NULL DROP TABLE dbo.candles;
IF OBJECT_ID('dbo.market_prices', 'U') IS NOT NULL DROP TABLE dbo.market_prices;
IF OBJECT_ID('dbo.balances', 'U') IS NOT NULL DROP TABLE dbo.balances;
IF OBJECT_ID('dbo.settings', 'U') IS NOT NULL DROP TABLE dbo.settings;
GO

CREATE TABLE dbo.bot_status (
    id INT IDENTITY(1,1) PRIMARY KEY,
    status NVARCHAR(50) NOT NULL,
    is_trading_enabled BIT NOT NULL DEFAULT 0,
    emergency_stop BIT NOT NULL DEFAULT 0,
    reason NVARCHAR(255) NULL,
    updated_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

CREATE TABLE dbo.market_prices (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    exchange NVARCHAR(50) NOT NULL,
    symbol NVARCHAR(20) NOT NULL,
    price DECIMAL(18, 8) NOT NULL,
    bid DECIMAL(18, 8) NULL,
    ask DECIMAL(18, 8) NULL,
    volume DECIMAL(18, 8) NULL,
    collected_at DATETIME2 NOT NULL
);
GO

CREATE INDEX IX_market_prices_symbol_collected_at
ON dbo.market_prices(symbol, collected_at DESC);
GO

CREATE TABLE dbo.candles (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    exchange NVARCHAR(50) NOT NULL,
    symbol NVARCHAR(20) NOT NULL,
    timeframe NVARCHAR(10) NOT NULL,
    open_price DECIMAL(18, 8) NOT NULL,
    high_price DECIMAL(18, 8) NOT NULL,
    low_price DECIMAL(18, 8) NOT NULL,
    close_price DECIMAL(18, 8) NOT NULL,
    volume DECIMAL(18, 8) NULL,
    started_at DATETIME2 NOT NULL,
    ended_at DATETIME2 NOT NULL,
    CONSTRAINT UQ_candles_symbol_timeframe_started_at UNIQUE(symbol, timeframe, started_at)
);
GO

CREATE INDEX IX_candles_symbol_timeframe_started_at
ON dbo.candles(symbol, timeframe, started_at DESC);
GO

CREATE TABLE dbo.signals (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    symbol NVARCHAR(20) NOT NULL,
    timeframe NVARCHAR(10) NOT NULL,
    signal_type NVARCHAR(50) NOT NULL,
    signal_value DECIMAL(18, 8) NULL,
    direction NVARCHAR(20) NOT NULL,
    strength INT NOT NULL,
    reason NVARCHAR(500) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

CREATE INDEX IX_signals_symbol_created_at
ON dbo.signals(symbol, created_at DESC);
GO

CREATE TABLE dbo.orders (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    exchange NVARCHAR(50) NOT NULL,
    exchange_order_id NVARCHAR(100) NULL,
    symbol NVARCHAR(20) NOT NULL,
    side NVARCHAR(10) NOT NULL,
    order_type NVARCHAR(20) NOT NULL,
    price DECIMAL(18, 8) NULL,
    amount DECIMAL(18, 8) NOT NULL,
    status NVARCHAR(50) NOT NULL,
    purpose NVARCHAR(50) NOT NULL,
    raw_response NVARCHAR(MAX) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_at DATETIME2 NULL
);
GO

CREATE INDEX IX_orders_symbol_status_created_at
ON dbo.orders(symbol, status, created_at DESC);
GO

CREATE TABLE dbo.executions (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    order_id BIGINT NOT NULL,
    exchange_execution_id NVARCHAR(100) NULL,
    symbol NVARCHAR(20) NOT NULL,
    side NVARCHAR(10) NOT NULL,
    price DECIMAL(18, 8) NOT NULL,
    amount DECIMAL(18, 8) NOT NULL,
    fee DECIMAL(18, 8) NULL,
    executed_at DATETIME2 NOT NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT FK_executions_orders FOREIGN KEY(order_id) REFERENCES dbo.orders(id)
);
GO

CREATE INDEX IX_executions_order_id
ON dbo.executions(order_id);
GO

CREATE TABLE dbo.positions (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    symbol NVARCHAR(20) NOT NULL,
    status NVARCHAR(20) NOT NULL,
    entry_order_id BIGINT NULL,
    exit_order_id BIGINT NULL,
    entry_price DECIMAL(18, 8) NOT NULL,
    amount DECIMAL(18, 8) NOT NULL,
    take_profit_price DECIMAL(18, 8) NULL,
    stop_loss_price DECIMAL(18, 8) NULL,
    opened_at DATETIME2 NOT NULL,
    closed_at DATETIME2 NULL,
    CONSTRAINT FK_positions_entry_order FOREIGN KEY(entry_order_id) REFERENCES dbo.orders(id),
    CONSTRAINT FK_positions_exit_order FOREIGN KEY(exit_order_id) REFERENCES dbo.orders(id)
);
GO

CREATE INDEX IX_positions_symbol_status
ON dbo.positions(symbol, status);
GO

CREATE TABLE dbo.trades (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    position_id BIGINT NOT NULL,
    symbol NVARCHAR(20) NOT NULL,
    entry_price DECIMAL(18, 8) NOT NULL,
    exit_price DECIMAL(18, 8) NOT NULL,
    amount DECIMAL(18, 8) NOT NULL,
    gross_profit_jpy DECIMAL(18, 2) NOT NULL,
    fee_jpy DECIMAL(18, 2) NULL,
    net_profit_jpy DECIMAL(18, 2) NOT NULL,
    profit_rate DECIMAL(10, 6) NOT NULL,
    exit_reason NVARCHAR(50) NOT NULL,
    opened_at DATETIME2 NOT NULL,
    closed_at DATETIME2 NOT NULL,
    CONSTRAINT FK_trades_positions FOREIGN KEY(position_id) REFERENCES dbo.positions(id)
);
GO

CREATE INDEX IX_trades_symbol_closed_at
ON dbo.trades(symbol, closed_at DESC);
GO

CREATE TABLE dbo.balances (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    jpy_balance DECIMAL(18, 2) NOT NULL,
    crypto_symbol NVARCHAR(20) NULL,
    crypto_amount DECIMAL(18, 8) NULL,
    estimated_total_jpy DECIMAL(18, 2) NOT NULL,
    collected_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

CREATE INDEX IX_balances_collected_at
ON dbo.balances(collected_at DESC);
GO

CREATE TABLE dbo.risk_events (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    event_type NVARCHAR(50) NOT NULL,
    severity NVARCHAR(20) NOT NULL,
    message NVARCHAR(500) NOT NULL,
    action_taken NVARCHAR(100) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

CREATE INDEX IX_risk_events_created_at
ON dbo.risk_events(created_at DESC);
GO

CREATE TABLE dbo.notifications (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    notification_type NVARCHAR(50) NOT NULL,
    destination NVARCHAR(50) NOT NULL,
    title NVARCHAR(100) NULL,
    message NVARCHAR(MAX) NOT NULL,
    status NVARCHAR(20) NOT NULL,
    sent_at DATETIME2 NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

CREATE INDEX IX_notifications_created_at
ON dbo.notifications(created_at DESC);
GO

CREATE TABLE dbo.system_logs (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    log_level NVARCHAR(20) NOT NULL,
    category NVARCHAR(50) NOT NULL,
    message NVARCHAR(MAX) NOT NULL,
    detail NVARCHAR(MAX) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

CREATE INDEX IX_system_logs_created_at
ON dbo.system_logs(created_at DESC);
GO

CREATE TABLE dbo.settings (
    id INT IDENTITY(1,1) PRIMARY KEY,
    setting_key NVARCHAR(100) NOT NULL UNIQUE,
    setting_value NVARCHAR(500) NOT NULL,
    description NVARCHAR(500) NULL,
    updated_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO
