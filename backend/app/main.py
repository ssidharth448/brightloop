"""Brightloop — Subscription Management API.

FastAPI application entry point.  Registers all routers and configures
CORS for the React frontend.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, customers, dashboard, invoices, payments, plans, products, subscriptions


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from app.seed import seed_database
        seed_database()
    except Exception as e:
        print(f"Startup notice: {e}")
    yield


app = FastAPI(
    title="Brightloop",
    description="Subscription management system — Odoo × Make-A-Ton hackathon",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the Vite React dev server and common local origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Register routers ----------
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(plans.router)
app.include_router(customers.router)
app.include_router(subscriptions.router)
app.include_router(invoices.router)
app.include_router(payments.router)
app.include_router(dashboard.router)


@app.get("/", tags=["Health"])
def root():
    """Health check endpoint."""
    return {"status": "ok", "app": "Brightloop", "version": "1.0.0"}
