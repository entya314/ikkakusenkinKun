/*
バックテスト用 取引履歴テーブル追加SQL

実行対象DB:
CryptoBot

用途:
Coincheck Public APIから取得した取引履歴を保存し、
バックテスト実行時にAPIではなくDBから高速に読み込む。
*/

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

IF OBJECT_ID('dbo.historical_trades', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.historical_trades (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        exchange NVARCHAR(50) NOT NULL,
        symbol NVARCHAR(20) NOT NULL,
        exchange_trade_id BIGINT NOT NULL,
        price DECIMAL(18, 8) NOT NULL,
        amount DECIMAL(18, 8) NOT NULL,
        side NVARCHAR(20) NULL,
        traded_at DATETIME2 NOT NULL,
        fetched_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        CONSTRAINT UQ_historical_trades_exchange_symbol_trade_id
            UNIQUE(exchange, symbol, exchange_trade_id)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_historical_trades_symbol_traded_at'
      AND object_id = OBJECT_ID('dbo.historical_trades')
)
BEGIN
    CREATE INDEX IX_historical_trades_symbol_traded_at
    ON dbo.historical_trades(symbol, traded_at);
END;
GO
