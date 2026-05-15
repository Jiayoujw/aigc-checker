from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db.database import init_db
from .routers import detect, rewrite, auth, history, upload, export, compare, apikeys, credits, calibration, report_rewrite


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
    except Exception:
        pass
    yield


app = FastAPI(title="降AIGC平台", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(detect.router, prefix="/api")
app.include_router(rewrite.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(compare.router, prefix="/api")
app.include_router(apikeys.router, prefix="/api")
app.include_router(credits.router, prefix="/api")
app.include_router(calibration.router, prefix="/api")
app.include_router(report_rewrite.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
