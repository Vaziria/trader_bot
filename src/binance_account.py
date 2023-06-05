from binance.client import AsyncClient
from .binance_model import *

from pydantic import parse_obj_as


class BinanceAccount:
    public_api: str
    private_api: str
    client: AsyncClient
    
    def __init__(self, public_api: str, private_api: str):
        self.public_api = public_api
        self.private_api = private_api

    async def create(self):
        self.client = await AsyncClient.create()

    async def get_open_orders(self, symbol: str, recvWindow: int=59990) -> List[Order]:
        data = await self.client.get_open_orders(symbol =symbol, recvWindow=recvWindow)
        return parse_obj_as(List[Order], data)

    async def get_asset_balance(self, asset: str, recvWindow: int=59990) -> AssetBalance:
        data = await self.client.get_asset_balance(asset, recvWindow=recvWindow)
        return AssetBalance.parse_obj(data)
    
    async def cancel_order(self, **params) -> CancelOrder:
        data = await self.client.cancel_order(**params)
        return CancelOrder.parse_obj(data)

    async def order_limit_sell(self):
        pass

    async def get_order(self, symbol: str, orderId: int) -> Order:
        data = await self.client.get_order(symbol=symbol, orderId=orderId)
        return Order.parse_obj(data)

    async def create_order(self):
        pass

    async def order_market_buy(self, symbol: str, quoteOrderQty: int, recvWindow: int = 59990):
        data = await self.client.order_market_buy(symbol=symbol, quoteOrderQty=quoteOrderQty, recvWindow=recvWindow)
        return PlaceOrderMarketBuy.parse_obj(data)

    async def get_exchange_info(self):
        data = await self.client.get_exchange_info()
        print(data)


    

    


if __name__ == '__main__':
    import asyncio
    from .config import get_config

    async def main():

        cfg = get_config()
        account = BinanceAccount(cfg.public_api, cfg.private_api)
        await account.create()

        await account.get_exchange_info()



    asyncio.run(main())

