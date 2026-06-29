"""Aggregate API routers."""

from fastapi import APIRouter

from app.api.routes import ask, auth, conversations, enterprise, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(conversations.router)
api_router.include_router(enterprise.router)
api_router.include_router(ask.router)
