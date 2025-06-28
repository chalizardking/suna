#!/usr/bin/env python3
"""
Minimal Suna API Server for Deployment Demo
This is a simplified version to demonstrate the deployment process.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
import uvicorn
from datetime import datetime

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Suna API (Demo)",
    description="Minimal Suna API server for deployment demonstration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Suna API (Demo Mode)",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0-demo"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENV_MODE", "local"),
        "demo_mode": True
    }

@app.get("/api/health")
async def api_health_check():
    """API health check endpoint"""
    return {
        "status": "healthy",
        "api_version": "1.0.0-demo",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/status")
async def api_status():
    """API status endpoint"""
    return {
        "status": "running",
        "mode": "demo",
        "features": {
            "agents": "demo",
            "sandbox": "demo", 
            "llm": "demo"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/config")
async def get_config():
    """Get basic configuration"""
    return {
        "environment": os.getenv("ENV_MODE", "local"),
        "frontend_url": os.getenv("NEXT_PUBLIC_URL", "http://localhost:3000"),
        "demo_mode": True,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/demo")
async def demo_endpoint():
    """Demo endpoint for testing"""
    return {
        "message": "This is a demo endpoint",
        "status": "success",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🚀 Starting Suna API Demo Server...")
    print("📍 Environment:", os.getenv("ENV_MODE", "local"))
    print("🌐 Frontend URL:", os.getenv("NEXT_PUBLIC_URL", "http://localhost:3000"))
    print("🔗 API will be available at: http://localhost:8000")
    print("📊 Health check: http://localhost:8000/health")
    print("📋 API status: http://localhost:8000/api/status")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )
