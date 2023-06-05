import asyncio
import json
from typing import List
from pydantic import BaseModel
from ..models.binance_model import *


class OrderStorage(BaseModel):
    _lock: asyncio.Lock
    _fname: str
    data: List[Order] = []

    def __init__(self, fname: str) -> None:
        self._lock = asyncio.Lock()
        self._fname = fname

    def save(self):
        with open(self.fname, "w+") as file:
            json.dump(self.dict(), file)


    def Add(self, order: Order):
        with self._lock:
            self.data.append(order)
            self.save()


    def remove(self, orderid: int):
        with self._lock:
            self.data = list(filter(lambda x: x.orderId != orderid, self.data))
            self.save()


    

