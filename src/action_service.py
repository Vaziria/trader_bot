import asyncio

from .logger import create_logger
from .binance_account import BinanceAccount
from .config import Config
from .models.binance_model import *
from .models.exchange_model import *
from .storages.order_storage import OrderStorage
from .helper import cache_time_func
from .dependencies import get_dependency

logger = create_logger(__name__)

class SymbolHaveOrderException(Exception):
    pass

class Balance:
    client: BinanceAccount
    data: dict

    @classmethod
    async def create(cls):
        client = await get_dependency(BinanceAccount)
        obj = cls(client)
        return obj
    
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

    # untuk dependendcy injection biar lebih enak buat aplikasinya
    @classmethod
    async def create(cls):
        obj: ActionService = cls()
        obj.client = await get_dependency(BinanceAccount)
        obj.config = await get_dependency(Config)
        obj.balance = await get_dependency(Balance)
        obj.order_storage = await get_dependency(OrderStorage)
        return obj

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
        logger.info(f"[ {symbol} ] place order buy {placeord.orderId}")

        orderfilled = await self.wait_filled(symbol, placeord.orderId)
        await self.order_storage.add(orderfilled)

        logger.info(f"[ {symbol} ] order buy {placeord.orderId} FILLED")

        return orderfilled
    
    async def place_sell(self, symbol: str) -> Order:
        
        buyorder = await self.order_storage.get(symbol)
        qty = buyorder.origQty
        placeord = await self.client.order_market_sell(symbol, qty)
        logger.info(f"[ {symbol} ] place order {placeord.orderId}")

        orderfilled = await self.wait_filled(symbol=symbol, orderId=placeord.orderId)
        await self.order_storage.remove(orderfilled)

        logger.info(f"[ {symbol} ] order sell {placeord.orderId} FILLED")

        return orderfilled


    
if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    async def check():
        print("chekc")

    async def main():
        loop.create_task(check())
        service: ActionService = await get_dependency(ActionService)

        data = await service.get_exchange_info()
        service: ActionService = await get_dependency(ActionService)
        service: ActionService = await get_dependency(ActionService)

        await service.client.client.close_connection()


    
    loop.run_until_complete(main())
    
