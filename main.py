import asyncio
from uvicorn import Config as UVConfig, Server
import asyncio
from src.app import fastapp
from src.webhook import *

loop = asyncio.get_event_loop()


if __name__ == "__main__":
    async def main():
        await get_dependency(ActionService)

        uvconfig = UVConfig(
            app=fastapp,
            loop=loop,
            host="0.0.0.0",
            port=5000, 
            log_level="info"
        )
        server = Server(uvconfig)
        
        await server.serve()
    
    loop.run_until_complete(main())
