from binance.client import Client
from src.config import get_config

cfg = get_config()
c = Client(cfg.public_api, cfg.private_api)

c.get_exchange_info()