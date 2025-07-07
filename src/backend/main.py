"""
FastAPI应用入口，初始化FastAPI应用并注册路由
"""
from fastapi import FastAPI
from src.backend.routers import users, questions, attempts, schemas as schema_router
from src.backend.database import engine, Base


# 创建数据库表
Base.metadata.create_all(bind=engine)


# 初始化FastAPI应用
app = FastAPI()


# 注册路由
app.include_router(users.router, prefix="/users")
app.include_router(questions.router, prefix="/questions")
app.include_router(attempts.router, prefix="/attempts")
app.include_router(schema_router.router, prefix="/sample-schemas")


# 跟路由
@app.get("/")
def read_root():
    return {"message": "SQL智能练习平台后端服务"}
