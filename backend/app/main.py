from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.database import get_db, engine, Base
from app.users import models as user_models
from app.ai import models as ai_models
from app.users.routes import router as users_router
from app.ai.routes import router as ai_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DoKi Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(ai_router)


@app.get("/")
def read_root():
    return {"message": "DoKi backend is running"}


@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "connected"}