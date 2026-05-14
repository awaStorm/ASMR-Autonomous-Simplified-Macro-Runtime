from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
from .config import settings
from .database import engine, Base
from .api import todos, agent, images, bili, jm, click

# 确保数据目录存在
Path(settings.data_dir).mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    Base.metadata.create_all(bind=engine)
    yield
    # 关闭时
    pass


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    debug=settings.debug
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(todos.router, prefix="/api/todos", tags=["todos"])
app.include_router(images.router, prefix="/api/images", tags=["images"])
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])
app.include_router(bili.router, prefix="/api/bili", tags=["bili"])
app.include_router(jm.router, prefix="/api/jm", tags=["jm"])
app.include_router(click.router, prefix="/api/click", tags=["click"])


@app.get("/")
async def root():
    """健康检查接口"""
    return {
        "message": "Bot_to_html API is running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=True)
