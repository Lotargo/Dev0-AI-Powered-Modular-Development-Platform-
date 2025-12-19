from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from project.core.framework.observability import get_event_bus
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    bus = get_event_bus()
    logger.info("WebSocket connected")

    try:
        # Subscribe to the global event channel
        # Note: The subscribe method returns an async generator
        async for event in bus.subscribe("dev0:events"):
            # Forward the event as JSON text
            await websocket.send_text(event.to_json())
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()
