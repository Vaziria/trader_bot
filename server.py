import asyncio
from uvicorn import Config as UVConfig, Server
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.webhook import webhookrouter
from src.dependencies import get_dependency
from src.action_service import ActionService


def create_app() -> FastAPI: 
    fastapp = FastAPI()
    fastapp.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    fastapp.include_router(webhookrouter)
    return fastapp




loop = asyncio.get_event_loop()


if __name__ == "__main__":
    async def main():
        await get_dependency(ActionService)
        app = create_app()
        uvconfig = UVConfig(
            app=app,
            loop=loop,
            host="0.0.0.0",
            port=80, 
            log_level="info"
        )
        server = Server(uvconfig)
        
        await server.serve()
    
    loop.run_until_complete(main())
