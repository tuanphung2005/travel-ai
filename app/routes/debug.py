"""
Simple browser-based debug UI for API I/O testing.
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.templates.debug_ui import get_debug_ui_html

router = APIRouter(prefix="/debug", tags=["Debug"])


@router.get("", response_class=HTMLResponse, summary="Debug UI")
async def debug_ui():
    return get_debug_ui_html()
