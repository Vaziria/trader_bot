from pydantic import BaseModel
import json
import os
from .logger import create_logger

logger = create_logger(__name__)

config_location = "config.json"

class Config(BaseModel):
    listen_addr: str = "0.0.0.0"
    run: int = 1
    amount: int = 11
    stop_loss: int = 1
    top_profit: int = 3
    pin: str = ""
    public_api: str = ""
    private_api: str = ""

    @classmethod
    async def create(cls):
        cfg = get_config()
        return cfg



def get_config() -> Config:
    if not os.path.exists(config_location):
        config = Config()
        with open(config_location, "w+") as file:
            data = config.dict()
            json.dump(data, file, indent=2)

        logger.info(config.dict())
        return config

    with open(config_location, "r") as file:
        data = json.load(file)
        config = Config.parse_obj(data)
        logger.info(config.dict())
        return config