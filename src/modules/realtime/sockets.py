from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from src.broker.manager import manager
from src.modules.iam.models import Usuario
from src.modules.iam.dependencies import verify_token_ws

router = APIRouter(prefix="/ws", tags=["Tiempo Real"])

@router.websocket("/{tenant_id}/{room_id}")
async def websocket_endpoint(websocket: WebSocket, tenant_id: int, room_id: str, token: str):
    user = verify_token_ws(token)
    if not user or user.tenant_id != tenant_id:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, tenant_id, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo for testing
            await manager.broadcast({"message": f"User {user.Correo}: {data}"}, tenant_id, room_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, tenant_id, room_id)
        await manager.broadcast({"message": f"User {user.Correo} left the room"}, tenant_id, room_id)
