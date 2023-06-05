from typing import List, Any
from pydantic import BaseModel

ORDER_FILLED = 'FILLED'

class AssetBalance(BaseModel):
    asset: str
    free: float
    locked: float

class CancelOrder(BaseModel):
    symbol: str
    origClientOrderId: str
    orderId: int
    clientOrderId: str


class Order(BaseModel):
    symbol: str
    orderId: int
    clientOrderId: str
    price: float
    origQty: float
    executedQty: float
    status: str
    timeInForce: str
    type: str
    side: str
    stopPrice: float
    icebergQty: float
    time: int

class OrderAck(BaseModel):
    symbol: str
    orderId: int
    clientOrderId: str
    transactTime: int

class OrderResult(BaseModel):
    symbol: str
    orderId: int
    clientOrderId: str
    transactTime: int
    price: float
    
    origQty: float
    executedQty: float
    cummulativeQuoteQty: float
    status: str
    timeInForce: str
    type: str
    side: str

class FillItem(BaseModel):
    price: float
    qty: float
    commission: float
    commissionAsset: str

class OrderFull(BaseModel):
    symbol: str
    orderId: int
    clientOrderId: str
    transactTime: int
    price: float
    origQty: float
    executedQty: float
    cummulativeQuoteQty: float
    status: str
    timeInForce: str
    type: str
    side: str
    fills: List[FillItem]


class PlaceOrderMarketBuy(BaseModel):
    orderId: int