from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from . import models
from .routers import books, votes, auth_router, admin
from .scheduler import start_scheduler
 
Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="Book Club API",
    root_path="/api",            # Tells Swagger to add /api to its data requests
    openapi_url="/openapi.json", # Internally just /openapi.json
    docs_url="/docs",            # Internally just /docs
    redoc_url="/redoc"
)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
 
app.include_router(auth_router.router)
app.include_router(books.router)
app.include_router(votes.router)
app.include_router(admin.router)
 
@app.on_event("startup")
def on_startup():
    start_scheduler()
 
@app.get("/health")
def health():
    return {"status": "ok"}
