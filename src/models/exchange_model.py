from pydantic import BaseModel, validator
from .binance_model import *



class RateLimit(BaseModel):

    rateLimitType: str            
    interval: str
    limit: int


PRICE_FILTER_TYPE = 'PRICE_FILTER'
LOT_SIZE_TYPE ='LOT_SIZE'
MIN_NOTIONAL_TYPE ='MIN_NOTIONAL'

class SymbolFilter(BaseModel):
    filterType: str

class PriceFilter(SymbolFilter):
    filterType: str = PRICE_FILTER_TYPE
    minPrice: float
    maxPrice: float
    tickSize: float

class LotSizeFilter(SymbolFilter):
    filterType: str = LOT_SIZE_TYPE
    minQty: float
    maxQty: float
    stepSize: float

class MinNotional(SymbolFilter):
    filterType: str = MIN_NOTIONAL_TYPE
    minNotional: float

class FilterNotFound(Exception):
    pass

class Symbol(BaseModel):
    symbol: str
    status: str
    baseAsset: str
    baseAssetPrecision: int
    quoteAsset: str
    quotePrecision: int
    orderTypes: List[str] = []
    icebergAllowed: bool
    filters: List[Any] = []

    @validator('filters', pre=True)
    def validate_exchange(cls, v):
        def create(data):
            if data.get('filterType') == PRICE_FILTER_TYPE:
                return PriceFilter.parse_obj(data)
            elif data.get('filterType') == LOT_SIZE_TYPE:
                return LotSizeFilter.parse_obj(data)
            elif data.get('filterType') == MIN_NOTIONAL_TYPE:
                return MinNotional.parse_obj(data)
            return data
        return list(map(create, v))
    
    def get_filter(self, filter_key: str):
        item: SymbolFilter
        for item in self.filters:
            if item.filterType == filter_key:
                return item
        
        raise FilterNotFound(f"filter {filter_key} from symbol {self.symbol} tidak ada")


class SymbolNotFound(Exception):
    pass

class ExchangeInfo(BaseModel):
    timezone: str
    serverTime: int
    rateLimits: List[RateLimit] = []
    exchangeFilters: List[Any] = []
    symbols: List[Symbol] = []

    def get_symbol(self, symbol: str) -> Symbol:
        for item in self.symbols:
            if item.symbol == symbol:
                return item
            
        raise SymbolNotFound(f"symbol {symbol} tidak ada")
   