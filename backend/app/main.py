from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db.database import init_db
from .routers import detect, plagiarism, rewrite, auth, history, upload, export, compare


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
    except Exception:
        pass
    yield


app = FastAPI(title="降AIGC & 查重平台", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(detect.router, prefix="/api")
app.include_router(plagiarism.router, prefix="/api")
app.include_router(rewrite.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(compare.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/debug-register")
async def debug_register():
    import traceback
    from .db.database import async_session
    from .db.models import User
    from .services.auth_service import hash_password

    try:
        async with async_session() as db:
            from sqlalchemy import select
            result = await db.execute(select(User).where(User.email == "debug@test.com"))
            if result.scalar_one_or_none():
                return {"msg": "user already exists"}

            user = User(
                email="debug@test.com",
                name="Debug",
                password_hash=hash_password("test123456"),
            )
            db.add(user)
            await db.commit()
            return {"msg": "success", "user_id": user.id}
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}
