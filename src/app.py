from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


fastapp = FastAPI()
fastapp.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


