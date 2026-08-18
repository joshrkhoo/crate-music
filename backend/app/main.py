from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import cors_allow_origins
from app.embed import warmup_model
from app.routers.auth import router as auth_router
from app.routers.playlists import router as playlists_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    warmup_model()
    yield


app = FastAPI(title="crate-music", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allow_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router)
app.include_router(playlists_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
