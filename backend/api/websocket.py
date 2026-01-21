"""
WebSocket API for real-time updates
Connects Supabase real-time to CopilotKit
"""

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter
import json
import asyncio
from typing import Dict, Set
import sys
from pathlib import Path

# Add parent directory to path for CEP modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cep_machine.core.supabase_db import get_database
from cep_machine.core.cache import get_cache

router = APIRouter()

# Store active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.agent_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        
        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()
        
        self.active_connections[client_id].add(websocket)
        
        # Send initial data
        await self.send_initial_data(websocket, client_id)

    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            self.active_connections[client_id].discard(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, client_id: str = None):
        if client_id:
            # Send to specific client
            if client_id in self.active_connections:
                disconnected = set()
                for connection in self.active_connections[client_id]:
                    try:
                        await connection.send_text(message)
                    except:
                        disconnected.add(connection)
                
                # Clean up disconnected connections
                for conn in disconnected:
                    self.active_connections[client_id].discard(conn)
        else:
            # Broadcast to all clients
            for client_id, connections in self.active_connections.items():
                disconnected = set()
                for connection in connections:
                    try:
                        await connection.send_text(message)
                    except:
                        disconnected.add(connection)
                
                # Clean up disconnected connections
                for conn in disconnected:
                    connections.discard(conn)

    async def send_initial_data(self, websocket: WebSocket, client_id: str):
        """Send initial data to new connection"""
        try:
            # Get database
            db = await get_database()
            
            # Send initial prospects
            prospects = await db.get_prospects(limit=50)
            await websocket.send_text(json.dumps({
                "type": "initial_data",
                "data": {
                    "prospects": prospects,
                    "client_id": client_id
                }
            }))
            
            # Send agent status
            agent_status = await db.get_agent_status()
            await websocket.send_text(json.dumps({
                "type": "agent_status",
                "data": agent_status
            }))
            
            # Send metrics
            cache = await get_cache()
            cache_info = await cache.get_info()
            await websocket.send_text(json.dumps({
                "type": "metrics",
                "data": {
                    "cache": cache_info,
                    "timestamp": asyncio.get_event_loop().time()
                }
            }))
            
        except Exception as e:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": str(e)
            }))

    async def connect_agent(self, websocket: WebSocket, agent_id: str):
        """Connect agent WebSocket"""
        await websocket.accept()
        
        if agent_id not in self.agent_connections:
            self.agent_connections[agent_id] = set()
        
        self.agent_connections[agent_id].add(websocket)
        
        # Send agent-specific data
        await websocket.send_text(json.dumps({
            "type": "agent_connected",
            "agent_id": agent_id
        }))

    def disconnect_agent(self, websocket: WebSocket, agent_id: str):
        """Disconnect agent WebSocket"""
        if agent_id in self.agent_connections:
            self.agent_connections[agent_id].discard(websocket)
            if not self.agent_connections[agent_id]:
                del self.agent_connections[agent_id]

    async def send_to_agent(self, message: str, agent_id: str):
        """Send message to specific agent"""
        if agent_id in self.agent_connections:
            disconnected = set()
            for connection in self.agent_connections[agent_id]:
                try:
                    await connection.send_text(message)
                except:
                    disconnected.add(connection)
            
            # Clean up disconnected connections
            for conn in disconnected:
                self.agent_connections[agent_id].discard(conn)

manager = ConnectionManager()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Main WebSocket endpoint for clients"""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif message.get("type") == "subscribe":
                # Handle subscription requests
                table = message.get("table")
                if table:
                    # In a real implementation, set up Supabase real-time subscription
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "table": table
                    }))
            elif message.get("type") == "agent_message":
                # Forward message to agent
                agent_id = message.get("agent_id")
                if agent_id:
                    await manager.send_to_agent(json.dumps(message), agent_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)

@router.websocket("/ws/agent/{agent_id}")
async def agent_websocket_endpoint(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for agents"""
    await manager.connect_agent(websocket, agent_id)
    
    try:
        while True:
            # Receive message from agent
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle agent messages
            if message.get("type") == "status_update":
                # Broadcast status update to all clients
                await manager.broadcast(json.dumps({
                    "type": "agent_status_update",
                    "agent_id": agent_id,
                    "data": message.get("data")
                }))
            elif message.get("type") == "progress_update":
                # Broadcast progress update
                await manager.broadcast(json.dumps({
                    "type": "agent_progress",
                    "agent_id": agent_id,
                    "progress": message.get("progress"),
                    "message": message.get("message")
                }))
            elif message.get("type") == "result":
                # Broadcast result
                await manager.broadcast(json.dumps({
                    "type": "agent_result",
                    "agent_id": agent_id,
                    "result": message.get("result")
                }))
    
    except WebSocketDisconnect:
        manager.disconnect_agent(websocket, agent_id)

# Helper functions for broadcasting updates
async def broadcast_prospect_update(prospect_data: dict, event_type: str):
    """Broadcast prospect updates to all clients"""
    await manager.broadcast(json.dumps({
        "type": "prospect_update",
        "event": event_type,
        "data": prospect_data
    }))

async def broadcast_agent_status(agent_id: str, status: dict):
    """Broadcast agent status updates"""
    await manager.broadcast(json.dumps({
        "type": "agent_status",
        "agent_id": agent_id,
        "status": status
    }))

async def broadcast_metrics_update(metrics: dict):
    """Broadcast metrics updates"""
    await manager.broadcast(json.dumps({
        "type": "metrics_update",
        "data": metrics
    }))

async def broadcast_coherence_update(coherence: dict):
    """Broadcast coherence metrics updates"""
    await manager.broadcast(json.dumps({
        "type": "coherence_update",
        "data": coherence
    }))

# Export broadcast functions for use in other modules
__all__ = [
    "manager",
    "broadcast_prospect_update",
    "broadcast_agent_status", 
    "broadcast_metrics_update",
    "broadcast_coherence_update"
]
