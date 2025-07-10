"""
FastAPI应用入口，初始化FastAPI应用并注册路由
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import users, questions, attempts, analyze, schemas as schema_router
from src.database import engine, Base


# 创建数据库表
Base.metadata.create_all(bind=engine)


# 初始化FastAPI应用
app = FastAPI()


origins = [
    "http://localhost:3000",  # 前端开发地址
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(users.router, prefix="/users")
app.include_router(questions.router, prefix="/questions")
app.include_router(attempts.router, prefix="/attempts")
app.include_router(schema_router.router, prefix="/sample-schemas")
app.include_router(analyze.router, prefix="/analyze")


# 跟路由
@app.get("/")
def read_root():
    return {"message": "SQL智能练习平台后端服务"}
