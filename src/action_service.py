import time

from .logger import create_logger
from .binance_account import BinanceAccount
from .config import Config
from .binance_model import *

logger = create_logger(__name__)

class SymbolHaveOrderException(Exception):
    pass

class Balance:
    client: BinanceAccount
    data: dict
    
    def __init__(self, client: BinanceAccount) -> None:
        self.client = client
        self.data = {}

    async def refresh_balance(self, bsymbol: str) -> float:
        data = await self.client.get_asset_balance(bsymbol)
        self.data[bsymbol] = data.free

        logger.info(f"account balance {data.free}")
        
        return data.free
    

class ActionService:
    client: BinanceAccount
    config: Config
    balance: Balance

    async def wait_filled(self, symbol: str, orderId: int) -> Order:
        while True:
            last_order = await self.client.get_order(symbol, orderId)
            if last_order.status == ORDER_FILLED:
                return last_order
            time.sleep(1)


    async def place_buy(self, symbol: str) -> Order:
        orders = await self.client.get_open_orders(symbol)
        if orders > 0:
            raise SymbolHaveOrderException(f"{symbol} have order")
        
        await self.balance.refresh_balance(symbol[-4:])
        placeord = await self.client.order_market_buy(symbol=symbol, quoteOrderQty=self.config.amount)
        logger.info(f"[ {symbol} ] place order {placeord.orderId}")

        orderfilled = await self.wait_filled(symbol, placeord.orderId)
        logger.info(f"[ {symbol} ] place order {placeord.orderId} FILLED")

        return orderfilled

