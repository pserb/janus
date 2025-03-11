from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
import time
from typing import List
import json

from .api.api import api_router
from .database import engine, Base, get_db
from .websocket import manager
from sqlalchemy.orm import Session
from . import crud
from .db_init import init_db  # Import the init_db function

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("janus-api")

# Create database tables - with validation
if not init_db():
    logger.warning("Database tables may not have been created correctly")
else:
    logger.info("Database tables created successfully")

# Get allowed origins from environment variable, or use default
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", 
    "http://localhost:3000,http://localhost:8000"
).split(",")

# Create FastAPI app
app = FastAPI(
    title="Janus API",
    description="API for Janus - Internship & Job Tracker",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API router
app.include_router(api_router, prefix="/api")

# Add request processing time middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Add global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    await manager.connect(websocket)
    try:
        # Send initial data on connection
        stats = crud.get_job_statistics(db)
        await manager.send_personal_message(
            {
                "event": "connected",
                "data": {
                    "message": "Connected to Janus WebSocket",
                    "stats": stats
                }
            },
            websocket
        )
        
        # Listen for messages
        while True:
            data = await websocket.receive_text()
            
            # Parse message
            try:
                message = json.loads(data)
                event = message.get("event")
                
                # Handle different event types
                if event == "ping":
                    await manager.send_personal_message({"event": "pong"}, websocket)
                
                elif event == "subscribe:jobs":
                    # Client is subscribing to job updates
                    # You can store subscription info here if needed
                    await manager.send_personal_message(
                        {"event": "subscribed", "channel": "jobs"},
                        websocket
                    )
                
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}

# Documentation endpoints
@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Welcome to Janus API. Visit /docs for API documentation."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)