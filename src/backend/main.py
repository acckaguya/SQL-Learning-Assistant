from fastapi import FastAPI, Depends
from src.backend.routers import users, questions, attempts, schemas as schema_router
from src.backend.database import engine, Base


Base.metadata.create_all(bind=engine)



app = FastAPI()

app.include_router(users.router, prefix="/users")
app.include_router(questions.router, prefix="/questions")
app.include_router(attempts.router, prefix="/attempts")
app.include_router(schema_router.router, prefix="/sample-schemas")

@app.get("/")
def read_root():
    return {"message": "SQL智能练习平台后端服务"}
