import asyncio

from pydantic import BaseModel
from fastapi import HTTPException, APIRouter

from .config import Config
from .logger import create_logger
from .dependencies import get_dependency
from .action_service import ActionService

logger = create_logger(__name__)

ACTION_CLOSE = 'close'
ACTION_OPEN = 'open'

class Event(BaseModel):
    pair: str
    pin: str
    action: str

class HookResponse(BaseModel):
    msg: str = "success"


def task_error_handler(task: asyncio.Task):
    try:
        task.result()
    except Exception as e:
        logger.error(task.exception(), exc_info=True)
    

webhookrouter = APIRouter()

@webhookrouter.post("/webhook")
async def webhook(event: Event) -> HookResponse:
    config: Config = await get_dependency(Config)
    action: ActionService = await get_dependency(ActionService)
    loop = asyncio.get_event_loop()

    logger.info("new event")
    logger.info(event)
    # checking pin
    if event.pin != config.pin:
        raise HTTPException(status_code=403)
    
    async def default_action():
        logger.info(f"handler tidak ada untuk event {event.action}")
    
    if event.action == ACTION_OPEN:
        coro = action.place_buy(event.pair)

    elif event.action == ACTION_CLOSE:
        coro = action.place_sell(event.pair)
    else:
        coro = default_action()

    task = loop.create_task(coro)
    task.add_done_callback(task_error_handler)

    return HookResponse()


c = 0

@webhookrouter.post("/test")
async def webhook(event: Event):
    logger.info(event)
    loop = asyncio.get_event_loop()
    action: ActionService = await get_dependency(ActionService)

    async def default_action():
        global c
        logger.info(f"handler tidak ada untuk event {event.action}")
        await asyncio.sleep(5)
        logger.info(f"asdasd {c}")
        c += 1
        raise Exception(f"asdasd {c}")
    
    coro = default_action()
    task = loop.create_task(coro)
    task.add_done_callback(task_error_handler)

    return HookResponse()