import asyncio
import json
from typing import List
from pydantic import parse_obj_as
import os

from ..models.binance_model import *
from ..logger import create_logger


logger = create_logger(__name__)

class OrderNotFound(Exception):
    pass

class OrderStorage:
    lock: asyncio.Lock
    fname: str
    data: List[Order] = []

    @classmethod
    async def create(cls):
        obj = cls("order_list.json")
        await obj.load()
        return obj

    def __init__(self, fname: str) -> None:
        self.lock = asyncio.Lock()
        self.fname = fname
        logger.info(f"order list on {fname}")

    def dict(self):
        datas = list(map(lambda x: x.dict(), self.datas))
        return datas

    async def load(self):
        logger.info(f"load data order on {self.fname}")
        if not os.path.exists(self.fname):
            return
        
        async with self.lock:
            with open(self.fname, "r") as file:
                data = json.load(file)
                self.data = parse_obj_as(List[Order], data)

    async def save(self):
        with open(self.fname, "w+") as file:
            json.dump(self.dict(), file)


    async def add(self, order: Order):
        async with self.lock:
            self.data.append(order)
            await self.save()

    async def get(self, symbol: str) -> Order:
        for ord in self.data:
            if ord.symbol == symbol:
                return ord
            
        raise OrderNotFound(f"order {symbol} not found")

    async def remove(self, orderid: int):
        with self.lock:
            self.data = list(filter(lambda x: x.orderId != orderid, self.data))
            await self.save()


    

