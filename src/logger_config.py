from contextvars import ContextVar
import os
import socket
from typing import Optional

from pydantic import BaseModel, Field

configuration_context = ContextVar('configuration context', default=None)

def default_log_level():
    mode = os.environ.get('logmode', 'info').upper()
    
    level = {
        "CRITICAL": 50,
        "ERROR": 40,
        "WARNING": 30,
        "INFO": 20,
        "DEBUG": 10,
        "NOTSET": 0,
    }
    
    return level.get(mode, 20)


def get_hostname():
    return socket.gethostname()
    
class LabelsExtras(BaseModel):
    username: Optional[str]
    version: Optional[str]
    hostname: str = Field(default_factory=get_hostname)
    
    

class Configuration(BaseModel):
    log_level: int = Field(default_factory=default_log_level)
    log_format: str = '[ %(levelname)s ][ %(asctime)s ] %(name)s : %(message)s'
    labels: LabelsExtras = LabelsExtras()
    
    
    


def set_configuration(config: Configuration = None):
    if not config:
        config = Configuration()
        
    configuration_context.set(config)

def get_configuration() -> Configuration:
    
    config = configuration_context.get()
    if not config:
        set_configuration()
        return get_configuration()
    
    return config
    