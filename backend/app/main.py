from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import detect, plagiarism, rewrite

app = FastAPI(title="降AIGC & 查重平台", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(detect.router, prefix="/api")
app.include_router(plagiarism.router, prefix="/api")
app.include_router(rewrite.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
