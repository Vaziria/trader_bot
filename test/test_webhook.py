import pytest
from unittest import mock
from fastapi.testclient import TestClient
from server import create_app
from src.webhook import Event
from src.action_service import ActionService, SymbolHaveOrderException,PlaceOrderMarketBuy, ORDER_FILLED
from src.dependencies import get_dependency
from binance.client import AsyncClient
from src.binance_account import AssetBalance, Order

order = Order(
            clientOrderId= "",
            executedQty= 0,
            icebergQty= 0,
            orderId= 0,
            origQty= 0,
            price=0,
            side="",
            status="",
            stopPrice=0,
            symbol="",
            time=0,
            type="",
            timeInForce="",
        )

class AsyncMock(mock.MagicMock):
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)
    
    async def get_open_orders(*args, **kwargs):
        return [order]
    
    async def get_asset_balance(*args, **kwargs):

        return AssetBalance(asset="BTCUDT", free=100, locked=50)
    
    async def order_market_buy(*args, **kwargs):
        return PlaceOrderMarketBuy(orderId=0)

    async def wait_filled(*args, **kwargs):
        ord = order.copy()
        ord.status = ORDER_FILLED
        return ord.dict()
    
    async def get_order(*args, **kwargs):
        ord = order.copy()
        ord.status = ORDER_FILLED
        return ord.dict()

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

@pytest.mark.asyncio
async def test_webhook(client: TestClient):
    mockclient = AsyncMock()



    with mock.patch.object(AsyncClient, 'create', new=mockclient) as ss:
        service: ActionService = await get_dependency(ActionService)
        await service.place_buy("asdasdd")
        with pytest.raises(SymbolHaveOrderException):
            await service.place_buy("asdasdd")