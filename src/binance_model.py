from typing import List
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


class RateLimit(BaseModel):

    rateLimitType: str            
    interval: str
    limit: int


class SymbolFilter(BaseModel):
    filterType: str

class PriceFilter(SymbolFilter):
    filterType: str = 'PRICE_FILTER'
    minPrice: float
    maxPrice: float
    tickSize: float

class LotSizeFilter(SymbolFilter):
    filterType: str = 'LOT_SIZE' 
    minQty: float
    maxQty: float
    stepSize: float

class MinNotional(SymbolFilter):
    filterType: str = 'MIN_NOTIONAL'
    minNotional: float

class Symbol(BaseModel):
    symbol: str
    status: str
    baseAsset: str
    baseAssetPrecision: int
    quoteAsset: str
    quotePrecision: int
    orderTypes: List[str] = []
    icebergAllowed: bool
    filters: List[SymbolFilter] = []


class ExchangeInfo(BaseModel):
    timezone: str
    serverTime: int
    rateLimits: List[RateLimit] = []
    exchangeFilters: List[dict] = []
    symbols: List[Symbol] = []


class PlaceOrderMarketBuy(BaseModel):
    orderId: int