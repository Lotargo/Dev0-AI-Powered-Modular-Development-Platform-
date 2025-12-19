from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from project.api.endpoints import router
from project.api.websockets import router as ws_router
from project.core.module_registry import module_registry
from project.core.mcp.server import mcp
from starlette.requests import Request
from starlette.responses import Response
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    On startup, discover and register all available modules.
    """
    module_registry.discover_and_register_modules()
    yield
    # Clean up resources if needed
    pass

app = FastAPI(
    title="Low-Code/No-Code Platform",
    description="A platform for building applications using modular components.",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(router)
app.include_router(ws_router)

# --- MCP Integration ---
# Mounting at /mcp.
# We remove the explicit mount_path arg to let FastMCP use default paths relative to the mount.
app.mount("/mcp", mcp.sse_app(), name="mcp_sse")

# --- Admin Panel ---
admin_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "admin_panel")
if os.path.exists(admin_path):
    app.mount("/admin", StaticFiles(directory=admin_path, html=True), name="admin")

@app.get("/")
async def root():
    return {"message": "Welcome to the Low-Code/No-Code Platform!"}
