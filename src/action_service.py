import asyncio

from .logger import create_logger
from .binance_account import BinanceAccount
from .config import Config
from .models.binance_model import *
from .models.exchange_model import *
from .storages.order_storage import OrderStorage, OrderNotFound
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
    orderlock: asyncio.Lock
    trade_symbol = {}

    # untuk dependendcy injection biar lebih enak buat aplikasinya
    @classmethod
    async def create(cls):
        obj: ActionService = ActionService()
        obj.orderlock = asyncio.Lock()
        client: BinanceAccount = await get_dependency(BinanceAccount)
        obj.client = client
        obj.config = await get_dependency(Config)
        obj.balance = await get_dependency(Balance)
        storage: OrderStorage = await get_dependency(OrderStorage)
        obj.order_storage = await get_dependency(OrderStorage)
        return obj

    @cache_time_func(60 * 60)
    async def get_exchange_info(self) -> ExchangeInfo:
        return await self.client.get_exchange_info()


    async def wait_filled(self, symbol: str, orderId: int) -> Order:
        while True:
            last_order = await self.client.get_order(symbol, orderId)
            print(last_order)
            if last_order.status == ORDER_FILLED:
                return last_order
            logger.Info(f"{last_order.orderId} wait filled")
            await asyncio.sleep(0.3)



    async def place_buy(self, symbol: str) -> Order:
        async with self.orderlock:
            try:
                if self.trade_symbol.get(symbol, False):
                    raise SymbolHaveOrderException("event dobel")
            except OrderNotFound:
                pass
            
            await self.balance.refresh_balance(symbol[-4:])
            placeord = await self.client.order_market_buy(symbol=symbol, quoteOrderQty=self.config.amount)
            logger.info(f"[ {symbol} ] place order buy {placeord.orderId}")
            

            orderfilled = await self.wait_filled(symbol, placeord.orderId)
            self.trade_symbol[symbol] = True

            logger.info(f"[ {symbol} ] order buy {placeord.orderId} FILLED")

            return orderfilled
    
    async def place_sell(self, symbol: str) -> Order:
        async with self.orderlock:
            exchange_info = await self.get_exchange_info()
            ex_symbol = exchange_info.get_symbol(symbol)
            filtersym: LotSizeFilter = ex_symbol.get_filter(LOT_SIZE_TYPE)

            balance = await self.balance.refresh_balance(symbol[:-4])
            qty = filtersym.precision(balance.free)
            
            # buyorder = await self.order_storage.get(symbol)
            # qty = buyorder.origQty
            placeord = await self.client.order_market_sell(symbol, qty)
            logger.info(f"[ {symbol} ] place order {placeord.orderId}")

            orderfilled = await self.wait_filled(symbol=symbol, orderId=placeord.orderId)
            self.trade_symbol[symbol] = False

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
    
