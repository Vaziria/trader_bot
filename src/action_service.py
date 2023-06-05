import asyncio

from .logger import create_logger
from .binance_account import BinanceAccount
from .config import Config
from .models.binance_model import *
from .models.exchange_model import *
from .storages.order_storage import OrderStorage
from .helper import cache_time_func

logger = create_logger(__name__)

class SymbolHaveOrderException(Exception):
    pass

class Balance:
    client: BinanceAccount
    data: dict
    
    def __init__(self, client: BinanceAccount) -> None:
        self.client = client
        self.data = {}

    async def refresh_balance(self, bsymbol: str) -> AssetBalance:
        data = await self.client.get_asset_balance(bsymbol)
        self.data[bsymbol] = data

        logger.info(f"account balance {data}")
        
        return data
    

class ActionService:
    client: BinanceAccount
    config: Config
    balance: Balance
    order_storage: OrderStorage

    @cache_time_func(60 * 60)
    async def get_exchange_info(self) -> ExchangeInfo:
        return await self.client.get_exchange_info()


    async def wait_filled(self, symbol: str, orderId: int) -> Order:
        while True:
            last_order = await self.client.get_order(symbol, orderId)
            if last_order.status == ORDER_FILLED:
                return last_order
            await asyncio.sleep(1)


    async def place_buy(self, symbol: str) -> Order:
        orders = await self.client.get_open_orders(symbol)
        if orders > 0:
            raise SymbolHaveOrderException(f"{symbol} have order")
        
        await self.balance.refresh_balance(symbol[-4:])
        placeord = await self.client.order_market_buy(symbol=symbol, quoteOrderQty=self.config.amount)
        logger.info(f"[ {symbol} ] place order {placeord.orderId}")

        orderfilled = await self.wait_filled(symbol, placeord.orderId)
        self.order_storage.Add(orderfilled)

        logger.info(f"[ {symbol} ] place order {placeord.orderId} FILLED")

        return orderfilled
    

