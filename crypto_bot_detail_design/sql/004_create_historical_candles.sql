/*
バックテスト用 ローソク足テーブル追加SQL

用途:
CSVなどで取得したOHLCVデータを保存し、
約定履歴ではなくローソク足ベースでバックテストする。
*/

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

IF OBJECT_ID('dbo.historical_candles', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.historical_candles (
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
        imported_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        CONSTRAINT UQ_historical_candles_symbol_timeframe_started_at
            UNIQUE(exchange, symbol, timeframe, started_at)
    );
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_historical_candles_symbol_timeframe_started_at'
      AND object_id = OBJECT_ID('dbo.historical_candles')
)
BEGIN
    CREATE INDEX IX_historical_candles_symbol_timeframe_started_at
    ON dbo.historical_candles(symbol, timeframe, started_at);
END;
GO
