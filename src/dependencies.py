import asyncio
from .logger import create_logger

logger = create_logger(__name__)

class Dependend:

    @classmethod
    async def create(cls):
        pass


_register_app = {}
_lock = {}


async def get_dependency(cls: Dependend):
    name = cls.__name__

    obj = _register_app.get(name)
    if obj == None:
        lock = asyncio.Lock()
        _lock[name] = lock

        async with lock:
            logger.info(f"creating object {name}")
            obj = await cls.create()
            _register_app[name] = obj

        del _lock[name]

    lock: asyncio.Lock = _lock.get(name)
    if lock:
        async with lock:
            return obj
    else:
        return obj


if __name__ == '__main__':
    pass