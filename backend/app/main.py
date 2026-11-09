
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth import router as auth_router
from app.routers.permissions import router as permissions_router
from app.routers.documents import router as documents_router
from app.routers.audit import router as audit_router

app = FastAPI(
    title="TrustVault API",
    description="Secure Document Management and Access Control System",
    version="1.0.0",
)
# CORS configuration for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Register API routers
app.include_router(auth_router)
app.include_router(permissions_router)
app.include_router(documents_router)
app.include_router(audit_router)

@app.get("/")
def home():
    return {
        "message": "Welcome to TrustVault API",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
