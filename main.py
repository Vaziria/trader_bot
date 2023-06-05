import asyncio
from uvicorn import Config, Server
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

loop = asyncio.get_event_loop()




        

fastapp = FastAPI()
fastapp.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



if __name__ == "__main__":
    async def main():
        
        config = Config(
            app=fastapp,
            loop=loop,
            host="0.0.0.0",
            port=5000, 
            log_level="info"
        )
        server = Server(config)
        
        await server.serve()
    
    loop.run_until_complete(main())
