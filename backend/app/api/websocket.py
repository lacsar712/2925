from fastapi import APIRouter, WebSocket, Depends
from loguru import logger

from app.api.deps import get_current_user_ws
from app.services.websocket_service import handle_websocket

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/quotes")
async def websocket_quotes(websocket: WebSocket, _user=Depends(get_current_user_ws)):
    await handle_websocket(websocket)
