from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import uvicorn

from database.connection import connect_to_mongo, close_mongo_connection, db
from init_db import initialize_database

from routes import (
    auth,
    users,
    patients,
    hospitals,
    aircraft,
    bookings,
    reports,
    dashboard,
    settings,
    notifications,
    hospital_staff,
)

# ---------------------------------------------------
# Lifespan (Startup & Shutdown)
# ---------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting Air Ambulance Management System...")
    if connect_to_mongo():
        initialize_database()
        print_routes(app)
        yield
        close_mongo_connection()
        print("👋 Shutting down Air Ambulance Management System...")
    else:
        print("❌ MongoDB connection failed")
        yield


# ---------------------------------------------------
# App Initialization
# ---------------------------------------------------
app = FastAPI(
    title="Air Ambulance Management System",
    description="Comprehensive backend for air ambulance operations management",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------
# ✅ CORS Middleware (FIXED)
# ---------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5174",
        "*", # Allow all origins for development to fix CORS issues with dynamic IPs
        "http://10.214.79.226:8080",
        "http://10.124.178.119:5173",
        "http://172.21.224.1:5173",
        "https://moviecloud-airambulanc.onrender.com",
        "https://*.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------
# Routers
# ---------------------------------------------------
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(patients.router)
app.include_router(hospitals.router)
app.include_router(aircraft.router)
app.include_router(bookings.router)
app.include_router(reports.router)
app.include_router(hospital_staff.router)
app.include_router(dashboard.router)
app.include_router(settings.router)
app.include_router(notifications.router)

# ---------------------------------------------------
# Root Endpoint
# ---------------------------------------------------
@app.get("/")
async def root():
    return {
        "message": "Air Ambulance Management System API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
    }

# ---------------------------------------------------
# Health Check
# ---------------------------------------------------
@app.get("/health")
async def health_check():
    try:
        if db.client:
            db.client.admin.command("ping")
            db_status = "connected"
        else:
            db_status = "disconnected"
    except Exception:
        db_status = "error"

    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat(),
    }

# ---------------------------------------------------
# Debug Routes
# ---------------------------------------------------
@app.get("/debug/routes")
async def debug_routes():
    return {
        "total_routes": len(app.routes),
        "routes": [
            {
                "path": r.path,
                "methods": list(r.methods),
                "name": getattr(r, "name", "unknown"),
            }
            for r in app.routes
            if hasattr(r, "methods")
        ],
    }

# ---------------------------------------------------
# Utility: Print Routes
# ---------------------------------------------------
def print_routes(app: FastAPI):
    print("\n📋 REGISTERED ROUTES")
    print("=" * 50)
    for route in app.routes:
        if hasattr(route, "methods"):
            print(f"{', '.join(route.methods):15} {route.path}")
    print("=" * 50)

# ---------------------------------------------------
# Run Server (Local)
# ---------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
