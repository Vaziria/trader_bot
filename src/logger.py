import logging
from logging.handlers import RotatingFileHandler

from .logger_config import get_configuration

config = get_configuration()

def create_stream_handler():
    formatter = logging.Formatter(config.log_format)
    
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)

    return handler


sthandler = create_stream_handler()
filelog_handler = RotatingFileHandler('app.log', maxBytes=20000, backupCount=10)
filelog_handler.formatter = formatter = logging.Formatter(config.log_format)


def create_logger(name, stream=True) -> logging.Logger:

    logger = logging.getLogger(name)
    logger.propagate = False
    logger.setLevel(config.log_level)
    
    try:
        if logger.hasHandlers():
            logger.handlers.clear()
    except AttributeError as e:
        pass
    
    if stream:
        logger.addHandler(sthandler)
        logger.addHandler(filelog_handler)

    return logger
    
    
    

if __name__ == '__main__':
    import logging
    
    
    l = create_logger(__name__)
    l.info("asdasdasd")
