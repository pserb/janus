import logging
from fastapi import WebSocket
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger("janus-websocket")


class ConnectionManager:
    """
    WebSocket connection manager for real-time job updates.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Connect a new WebSocket client.

        Args:
            websocket: WebSocket connection
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            f"WebSocket client connected (total: {len(self.active_connections)})"
        )

    def disconnect(self, websocket: WebSocket):
        """
        Disconnect a WebSocket client.

        Args:
            websocket: WebSocket connection
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(
                f"WebSocket client disconnected (total: {len(self.active_connections)})"
            )

    async def send_personal_message(
        self, message: Dict[str, Any], websocket: WebSocket
    ):
        """
        Send a message to a specific client.

        Args:
            message: Message to send
            websocket: WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {str(e)}")
            self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast a message to all connected clients.

        Args:
            message: Message to broadcast
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {str(e)}")
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


# Create a connection manager instance
manager = ConnectionManager()


async def notify_new_job(job_data: Dict[str, Any]):
    """
    Notify connected clients about a new job.

    Args:
        job_data: Job data to send
    """
    await manager.broadcast(
        {
            "event": "jobs:new",
            "data": job_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
