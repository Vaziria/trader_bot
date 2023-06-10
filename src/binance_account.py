from binance.client import AsyncClient
from .models.binance_model import *
from .models.exchange_model import *
from .config import Config
from .dependencies import get_dependency

from pydantic import parse_obj_as



class BinanceAccount:
    client: AsyncClient

    @classmethod
    async def create(cls):
        cfg = await get_dependency(Config)
        obj: BinanceAccount = BinanceAccount()
        obj.client = await AsyncClient.create(cfg.public_api, cfg.private_api)
        return obj

    async def get_open_orders(self, symbol: str, recvWindow: int=59990) -> List[Order]:
        data = await self.client.get_open_orders(symbol =symbol, recvWindow=recvWindow)
        print(data)
        return parse_obj_as(List[Order], data)

    async def get_asset_balance(self, asset: str, recvWindow: int=59990) -> AssetBalance:
        data = await self.client.get_asset_balance(asset, recvWindow=recvWindow)
        return AssetBalance.parse_obj(data)
    
    async def cancel_order(self, **params) -> CancelOrder:
        data = await self.client.cancel_order(**params)
        return CancelOrder.parse_obj(data)

    # async def order_limit_sell(self):
    #     orderId = self.client.order_limit_sell(symbol=symbol, quantity=qty, price=sPrice, recvWindow=59990)['orderId']

    async def get_order(self, symbol: str, orderId: int) -> Order:
        data = await self.client.get_order(symbol=symbol, orderId=orderId)
        return Order.parse_obj(data)

    async def create_order(self):
        await self.client.cancel_order()

    async def order_market_buy(self, symbol: str, quoteOrderQty: int, recvWindow: int = 59990) -> PlaceOrderMarketBuy:
        data = await self.client.order_market_buy(symbol=symbol, quoteOrderQty=quoteOrderQty, recvWindow=recvWindow)
        return PlaceOrderMarketBuy.parse_obj(data)
    
    

    async def get_exchange_info(self) -> ExchangeInfo:
        data = await self.client.get_exchange_info()
        return ExchangeInfo.parse_obj(data)

    async def order_market_sell(self, symbol: str, quantity: int, recvWindow: int = 59990) -> PlaceOrderMarketSell:
        data = await self.client.order_market_sell(symbol=symbol, quantity=quantity, recvWindow=recvWindow)
        return PlaceOrderMarketSell.parse_obj(data)
    

    


if __name__ == '__main__':
    import asyncio
    from dependencies import get_dependency
    
    from .config import get_config

    loop = asyncio.get_event_loop()

    async def main():
        account = await get_dependency(BinanceAccount)

        await account.get_exchange_info()

        await account.client.close_connection()

        # await account.get_exchange_info()

        # await account.client.close_connection()


    loop.run_until_complete(main())

