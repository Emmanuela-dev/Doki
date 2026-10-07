"""
DoKi — AI-Powered B2B Organic Waste Marketplace
FastAPI application entry point.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.db.supabase import get_supabase
from app.listings.router import router as listings_router
from app.marketplace.router import router as marketplace_router
from app.marketplace.location_router import router as location_router
from app.marketplace.transactions_router import router as transactions_router
from app.users.supabase_routes import router as auth_router

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="DoKi Marketplace API",
    description=(
        "AI-Powered B2B Organic Waste Marketplace — "
        "connecting waste producers with circular-economy buyers in Kenya."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Static file serving for local image uploads
# ---------------------------------------------------------------------------

UPLOAD_DIR = settings.LOCAL_UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

API_PREFIX = "/api/v1"

app.include_router(listings_router,     prefix=API_PREFIX)
app.include_router(marketplace_router,  prefix=API_PREFIX)
app.include_router(location_router,     prefix=API_PREFIX)
app.include_router(transactions_router, prefix=API_PREFIX)
app.include_router(auth_router)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def root():
    return {
        "service": "DoKi Marketplace API",
        "version": "0.1.0",
        "status": "healthy",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


@app.get("/db-check", tags=["Health"])
def db_check():
    response = get_supabase().table("users").select("id").limit(1).execute()
    return {"database": "connected", "rows_checked": len(response.data)}
