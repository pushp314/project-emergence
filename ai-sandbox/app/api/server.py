import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from pydantic import BaseModel

import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.main import SandboxApp

logger = logging.getLogger(__name__)

# --- Models ---
class ChatMessage(BaseModel):
    message: str

class ApprovalResponse(BaseModel):
    success: bool

# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SandboxApp
    config_path = app.state.config_path
    sandbox = SandboxApp(config_path, start_paused=True)
    await sandbox.initialize()
    app.state.sandbox = sandbox
    
    # Start the engine in background
    app.state.engine_task = asyncio.create_task(sandbox.run())
    
    # Automatically start un-paused
    await sandbox.conversation_engine.resume()
    
    yield
    
    # Shutdown
    await sandbox.shutdown()
    app.state.engine_task.cancel()
    try:
        await app.state.engine_task
    except asyncio.CancelledError:
        pass


def create_app(config_path: str = "./config.yaml") -> FastAPI:
    app = FastAPI(title="AI Sandbox API", lifespan=lifespan)
    app.state.config_path = config_path
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/status")
    async def get_status(request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        state = sandbox.conversation_engine.get_state()
        return state

    @app.get("/api/permissions")
    async def get_permissions(request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        pending = sandbox.permission_manager.get_pending()
        
        result = []
        for p in pending:
            result.append({
                "id": p.request.request_id,
                "agent_id": p.request.agent_id,
                "action": p.request.action,
                "risk": p.request.risk.value,
                "details": p.request.details
            })
        return {"permissions": result}

    @app.post("/api/permissions/{req_id}/approve", response_model=ApprovalResponse)
    async def approve_permission(req_id: str, request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        success = await sandbox.permission_manager.approve(req_id)
        if not success:
            raise HTTPException(status_code=404, detail="Permission request not found")
        return ApprovalResponse(success=True)

    @app.post("/api/permissions/{req_id}/deny", response_model=ApprovalResponse)
    async def deny_permission(req_id: str, request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        success = await sandbox.permission_manager.deny(req_id)
        if not success:
            raise HTTPException(status_code=404, detail="Permission request not found")
        return ApprovalResponse(success=True)

    @app.post("/api/chat")
    async def chat(msg: ChatMessage, request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        await sandbox.conversation_engine.inject_human_message(msg.message)
        return {"success": True}

    @app.websocket("/ws/events")
    async def websocket_endpoint(websocket: WebSocket):
        sandbox: SandboxApp = websocket.app.state.sandbox
        await websocket.accept()
        
        queue = asyncio.Queue()
        
        def event_callback(event):
            # Try to serialize event to dict
            try:
                if hasattr(event, "to_dict"):
                    data = event.to_dict()
                elif hasattr(event, "__dict__"):
                    data = event.__dict__
                else:
                    data = {"type": type(event).__name__, "str": str(event)}
                
                # Push to queue non-blocking
                queue.put_nowait(data)
            except Exception as e:
                logger.error(f"Error serializing event for WS: {e}")

        # Subscribe to all events
        sandbox.event_bus.subscribe("*", event_callback)
        
        try:
            while True:
                data = await queue.get()
                # Use default str for things that aren't JSON serializable (like Enums, dates)
                try:
                    await websocket.send_text(json.dumps(data, default=str))
                except Exception as e:
                    logger.error(f"Failed to send WS message: {e}")
        except WebSocketDisconnect:
            pass
        finally:
            sandbox.event_bus.unsubscribe("*", event_callback)
            
    return app

def start_server(config_path: str = "./config.yaml", port: int = 8000):
    app = create_app(config_path)
    uvicorn.run(app, host="0.0.0.0", port=port)
