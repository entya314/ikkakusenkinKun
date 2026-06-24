from __future__ import annotations

import time
from decimal import Decimal

from app.asset.asset_service import AssetService
from app.common.logger import setup_logger
from app.exchange.exchange_client import CoincheckClient
from app.market.market_data_service import MarketDataService
from app.notification.line_notifier import LineNotifier
from app.order.order_service import OrderService
from app.position.position_service import PositionService
from app.risk.risk_service import RiskService
from config import settings


logger = setup_logger()


def run_once() -> None:
    client = CoincheckClient()
    market_data_service = MarketDataService(client)
    asset_service = AssetService(client)
    order_service = OrderService(client)
    position_service = PositionService()
    risk_service = RiskService()

    risk_result = risk_service.check_emergency_stop()
    if not risk_result.can_trade:
        logger.info("取引停止: %s", risk_result.reason)
        return

    current_price: Decimal = market_data_service.collect_current_price()
    logger.info("現在価格取得: %s %s", settings.symbol, current_price)

    has_position = position_service.has_open_position()
    logger.info("保有ポジション: %s", has_position)

    # TODO:
    # 1. CandleServiceでローソク足取得
    # 2. SignalServiceで指標計算
    # 3. StrategyServiceで売買判断
    # 4. OrderServiceで注文実行
    # 現時点では誤発注防止のため、実注文判断は未実装。


def main() -> None:
    logger.info("一攫千金くん 起動")

    notifier = LineNotifier()
    notifier.send_text("【一攫千金くん】システムを起動しました", "SYSTEM_START")

    while True:
        try:
            run_once()
        except KeyboardInterrupt:
            logger.info("手動終了")
            break
        except Exception as e:
            logger.exception("メインループでエラー: %s", e)

        time.sleep(settings.main_loop_interval_seconds)


if __name__ == "__main__":
    main()
