from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Create the FastAPI app
app = FastAPI(
    title="Bhoomi TechZone HRMS API",
    description="Backend API for Bhoomi TechZone Human Resource Management System",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="app/web"), name="static")

# Import and include all routers
from app.routes import users, attendance, projects, web, teams, daily_reports, leave_requests, performance_reviews, settings, dashboard, sales_api, profile

app.include_router(users.router)
app.include_router(attendance.router)
app.include_router(projects.router)
app.include_router(web.router)
app.include_router(teams.router)
app.include_router(daily_reports.router)
app.include_router(leave_requests.router)
app.include_router(performance_reviews.router)
app.include_router(settings.router)
app.include_router(dashboard.router)
app.include_router(profile.router, prefix="/users")
app.include_router(sales_api.router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Bhoomi TechZone HRMS API",
        "version": "1.0.0",
        "status": "online",
        "timestamp": "2025-06-11 05:33:42",
        "user": "soherumy"
    }