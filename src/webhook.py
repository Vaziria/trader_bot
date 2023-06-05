from pydantic import BaseModel
from fastapi import HTTPException
from .app import fastapp
from .config import get_config
from .logger import create_logger

logger = create_logger(__name__)

config = get_config()

ACTION_CLOSE = 'close'
ACTION_OPEN = 'open'

class Event(BaseModel):
    pair: str
    pin: str
    action: str

class HookResponse(BaseModel):
    msg: str = "success"


@fastapp.post("/webhook")
async def webhook(event: Event) -> HookResponse:
    logger.info("new event")
    logger.info(event)
    # checking pin
    if event.pin != config.pin:
        raise HTTPException(status_code=403)
    # handle event

    return HookResponse()