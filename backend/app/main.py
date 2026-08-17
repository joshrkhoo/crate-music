from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import cors_allow_origins
from app.routers.auth import router as auth_router
from app.routers.playlists import router as playlists_router

app = FastAPI(title="crate-music")

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
