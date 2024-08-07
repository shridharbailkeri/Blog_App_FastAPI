from enum import auto
#import pwd
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth
from . import models
from .database import engine
from .routers import post, user,vote
from .config import settings



models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(post.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(vote.router)

@app.get("/")
def root():
    return {"message": "Hello Tom!!!J"}




