from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.websocket_manager import manager


router = APIRouter(
    tags=["WebSocket"],
)


@router.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket):
    """
    Real-time security alert stream for analyst dashboards.
    """

    await manager.connect(websocket)

    try:
        while True:
            # Keep the connection alive and allow the client
            # to send lightweight heartbeat messages.
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)

    except Exception:
        manager.disconnect(websocket)