"""
AccelerateAI - FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import urllib.request

from routers import auth, student, company, government, ai_evaluation, mentor, chat, test, mentorship, messages
from database.connection import client

app = FastAPI(
    title="AccelerateAI API",
    description="AI-Powered Fair Internship Ecosystem — Government of Global",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={"persistAuthorization": True}
)

# OpenAPI Security Definition
# This ensures the "Authorize" button appears in Swagger UI for JWT.
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token in the format: Bearer <token>"
        }
    }
    # Apply security selectively to paths
    # We exclude /api/auth and public paths like / or /health
    for path, path_item in openapi_schema["paths"].items():
        if path.startswith("/api/") and not path.startswith("/api/auth/"):
            for method in path_item:
                if "security" not in path_item[method]:
                    path_item[method]["security"] = [{"HTTPBearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(student.router)
app.include_router(company.router)
app.include_router(government.router)
app.include_router(ai_evaluation.router)
app.include_router(mentor.router)
app.include_router(chat.router)
app.include_router(test.router)
app.include_router(mentorship.router)
app.include_router(messages.router)

@app.on_event("startup")
async def startup_db_check():
    try:
        await client.admin.command("ping")
        print("[OK] MongoDB connected successfully")
    except Exception as e:
        print(f"[ERROR] MongoDB connection failed: {e}")
        # Crash app if database is unavailable
        import sys
        sys.exit(1)

@app.on_event("startup")
async def check_ollama():
    """Ensure local Ollama server is running and reachable at startup using stdlib"""
    try:
        # Check standard Ollama local tags endpoint
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as response:
            if response.getcode() != 200:
                raise Exception(f"Ollama server returned status {response.getcode()}")
        print("[OK] Ollama Local Server connected successfully (verified via /api/tags)")
    except Exception as e:
        print(f"[ERROR] Ollama connection failed: {e}")
        print("💡 Ensure Ollama is running locally with 'ollama serve'")
        # For demo purposes, we don't crash the whole app if Ollama is down
@app.get("/")
async def root():
    return {
        "message": "AccelerateAI API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "AccelerateAI"}

@app.post("/api/ai/stress-test")
async def stress_test_ai():
    """Simulate 3 concurrent AI evaluation requests for audit purposes"""
    from services.crew_ai_service import run_evaluation
    import asyncio
    
    tasks = [
        run_evaluation("TEST001", "print('hello')", "Simple output"),
        run_evaluation("TEST002", "def add(a,b): return a+b", "Addition function"),
        run_evaluation("TEST003", "import os; os.listdir('.')", "File listing")
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {"results": [str(r) if isinstance(r, Exception) else r for r in results]}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
