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

    @app.get("/api/models/status")
    async def get_models_status(request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        registry = sandbox.model_registry
        routes_data = {}
        for name, adapter in registry._adapters.items():
            if hasattr(adapter, "get_telemetry"):
                routes_data[name] = adapter.get_telemetry()
            elif hasattr(adapter, "get_model_info"):
                routes_data[name] = adapter.get_model_info()
            else:
                routes_data[name] = {"name": name, "type": type(adapter).__name__}
        return {"routes": routes_data}

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

    @app.get("/api/tools")
    async def get_tools(request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        tools = sandbox.tool_gateway.list_tools()
        return {
            "tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.input_schema,
                    "permission": t.permission.value,
                    "risk": t.risk.value,
                    "enabled": t.enabled
                }
                for t in tools
            ]
        }

    @app.post("/api/tools/execute")
    async def execute_tool_endpoint(req: Dict[str, Any], request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        tool_name = req.get("tool_name")
        arguments = req.get("arguments", {})
        agent_id = req.get("agent_id", "operator")

        if not tool_name:
            raise HTTPException(status_code=400, detail="tool_name is required")

        from app.events.schemas import ToolCall
        call = ToolCall(tool_name=tool_name, arguments=arguments, agent_id=agent_id)
        result = await sandbox.tool_gateway.execute(call)
        return {
            "success": result.success,
            "call_id": result.call_id,
            "result": result.result,
            "error": result.error
        }

    @app.get("/api/memory")
    async def get_memory(request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        turn = sandbox.conversation_engine.turn_number
        context = {}
        if sandbox.memory_manager:
            try:
                context = await sandbox.memory_manager.get_context(turn)
            except Exception as e:
                context = {"error": str(e)}

        vector_count = 0
        if sandbox.vector_store:
            try:
                vector_count = len(getattr(sandbox.vector_store, "_embeddings", []))
            except Exception:
                pass

        return {
            "turn": turn,
            "context": context,
            "vector_store_entries": vector_count
        }

    @app.post("/api/memory/search")
    async def search_memory(req: Dict[str, Any], request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        query = req.get("query", "")
        limit = req.get("limit", 5)

        if not query:
            return {"results": []}

        if sandbox.vector_store:
            try:
                results = sandbox.vector_store.search(query, limit=limit)
                return {"results": results}
            except Exception as e:
                return {"error": str(e), "results": []}

        return {"results": [], "message": "Vector store not configured"}

    @app.get("/api/evidence")
    async def get_evidence(request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        if sandbox.evidence_manager:
            try:
                evidence = sandbox.evidence_manager.get_timeline(limit=100)
                return {"evidence": evidence}
            except Exception as e:
                return {"evidence": [], "error": str(e)}
        return {"evidence": []}

    @app.get("/api/sessions")
    async def get_sessions(request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        if sandbox.session_manager:
            try:
                sessions = await sandbox.session_manager.get_session_history()
                return {"sessions": sessions}
            except Exception as e:
                return {"sessions": [], "error": str(e)}
        return {"sessions": []}

    @app.get("/api/modifications")
    async def get_modifications(request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        if hasattr(sandbox, 'self_modification_engine') and sandbox.self_modification_engine:
            try:
                active = sandbox.self_modification_engine.get_active_modifications()
                history = sandbox.self_modification_engine.get_modification_history()
                return {
                    "active_modifications": [
                        {
                            "id": m.modification_id,
                            "file_path": m.file_path,
                            "reason": m.reason,
                            "risk": m.risk.value if hasattr(m.risk, 'value') else str(m.risk),
                            "status": m.status.value if hasattr(m.status, 'value') else str(m.status),
                            "timestamp": m.timestamp,
                            "diff": m.diff
                        }
                        for m in active
                    ],
                    "history": [
                        {
                            "id": m.modification_id,
                            "file_path": m.file_path,
                            "reason": m.reason,
                            "risk": m.risk.value if hasattr(m.risk, 'value') else str(m.risk),
                            "status": m.status.value if hasattr(m.status, 'value') else str(m.status),
                            "timestamp": m.timestamp
                        }
                        for m in history
                    ]
                }
            except Exception as e:
                return {"active_modifications": [], "history": [], "error": str(e)}
        return {"active_modifications": [], "history": [], "message": "Self-modification engine not active"}

    @app.post("/api/modifications/{mod_id}/rollback")
    async def rollback_modification(mod_id: str, request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        if hasattr(sandbox, 'self_modification_engine') and sandbox.self_modification_engine:
            success = await sandbox.self_modification_engine.rollback_modification(mod_id)
            if success:
                return {"success": True, "message": f"Modification {mod_id} successfully rolled back"}
            raise HTTPException(status_code=400, detail="Rollback failed")
        raise HTTPException(status_code=500, detail="Self-modification engine not available")

    @app.post("/api/audio/speak")
    async def speak_audio(req: Dict[str, Any], request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        text = req.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="text is required")
        if sandbox._tts:
            asyncio.create_task(sandbox._tts.speak(text))
            return {"success": True, "message": "Audio dispatched"}
        return {"success": False, "message": "TTS not initialized"}

    @app.get("/api/db/health")
    async def get_db_health(request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        import sqlite3, os
        db_path = sandbox.config.get("memory", {}).get("db_path", "./data/memory.db")
        if not os.path.exists(db_path):
            return {"status": "not_found", "path": db_path}

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            table_stats = {}
            for t in tables:
                cursor.execute(f"SELECT count(*) FROM {t}")
                table_stats[t] = cursor.fetchone()[0]
            conn.close()

            file_size_kb = round(os.path.getsize(db_path) / 1024, 2)
            return {
                "status": "healthy" if integrity == "ok" else "warning",
                "integrity": integrity,
                "journal_mode": journal_mode,
                "file_size_kb": file_size_kb,
                "tables": table_stats
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @app.post("/api/reports/generate")
    async def generate_report_endpoint(req: Dict[str, Any], request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        session_id = req.get("session_id") or (sandbox.conversation_engine.conversation_id if sandbox.conversation_engine else None)
        if not session_id:
            raise HTTPException(status_code=400, detail="No active session found")

        from app.reports.generator import ReportGenerator
        generator = ReportGenerator(
            evidence_manager=sandbox.evidence_manager,
            session_manager=sandbox.session_manager
        )
        try:
            report_path = generator.generate_final_report(session_id)
            with open(report_path, "r") as f:
                content = f.read()
            return {"success": True, "report_path": report_path, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @app.get("/api/reports")
    async def list_reports():
        import os, glob
        reports_dir = "./reports"
        if not os.path.exists(reports_dir):
            return {"reports": []}
        files = glob.glob(f"{reports_dir}/*.md")
        return {"reports": [os.path.basename(f) for f in files]}

    @app.get("/api/benchmarks/run")
    async def run_benchmarks_endpoint():
        try:
            from app.benchmarks import bench_event_bus, bench_sqlite_writes, bench_context_manager, bench_scheduler_round_robin
            bus_res = await asyncio.to_thread(bench_event_bus)
            db_res = await asyncio.to_thread(bench_sqlite_writes)
            ctx_res = await asyncio.to_thread(bench_context_manager)
            sched_res = await asyncio.to_thread(bench_scheduler_round_robin)

            return {
                "success": True,
                "benchmarks": {
                    "event_bus": {
                        "name": bus_res.name,
                        "iterations": bus_res.iterations,
                        "elapsed_s": bus_res.elapsed_s,
                        "ops_per_second": bus_res.ops_per_sec,
                        "avg_latency_us": bus_res.per_op_us,
                        "passed": bus_res.passed
                    },
                    "sqlite_store": {
                        "name": db_res.name,
                        "iterations": db_res.iterations,
                        "elapsed_s": db_res.elapsed_s,
                        "ops_per_second": db_res.ops_per_sec,
                        "avg_latency_us": db_res.per_op_us,
                        "passed": db_res.passed
                    },
                    "context_manager": {
                        "name": ctx_res.name,
                        "iterations": ctx_res.iterations,
                        "elapsed_s": ctx_res.elapsed_s,
                        "ops_per_second": ctx_res.ops_per_sec,
                        "avg_latency_us": ctx_res.per_op_us,
                        "passed": ctx_res.passed
                    },
                    "scheduler": {
                        "name": sched_res.name,
                        "iterations": sched_res.iterations,
                        "elapsed_s": sched_res.elapsed_s,
                        "ops_per_second": sched_res.ops_per_sec,
                        "avg_latency_us": sched_res.per_op_us,
                        "passed": sched_res.passed
                    }
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @app.get("/api/capabilities")
    async def get_capabilities():
        from app.capabilities.registry import get_capability_registry
        reg = get_capability_registry()
        return {
            "models": [
                {
                    "id": m.model_id,
                    "name": m.name,
                    "max_context": m.max_context,
                    "max_output": m.max_output,
                    "estimated_latency_ms": m.estimated_latency_ms,
                    "estimated_ram_mb": m.estimated_ram_mb,
                    "specialization": m.specialization
                }
                for m in reg.list_models()
            ],
            "tools": [
                {
                    "id": t.tool_id,
                    "name": t.name,
                    "description": t.description,
                    "permission_required": t.permission_required,
                    "risk_level": t.risk_level
                }
                for t in reg.list_tools()
            ],
            "agents": [
                {
                    "id": a.agent_id,
                    "name": a.name,
                    "preferred_models": a.preferred_models,
                    "available_tools": a.available_tools
                }
                for a in reg.list_agents()
            ]
        }

    @app.post("/api/research")
    async def run_research(req: Dict[str, Any], request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        question = req.get("question") or req.get("query")
        if not question:
            raise HTTPException(status_code=400, detail="question is required")
        
        agent_id = req.get("agent_id", "researcher")
        max_sources = req.get("max_sources", 5)

        if not sandbox.research_manager:
            raise HTTPException(status_code=500, detail="Research manager not available")

        try:
            session = await sandbox.research_manager.research(
                agent_id=agent_id,
                question=question,
                reason=f"Operator requested research on: {question}",
                max_sources=max_sources
            )
            return {
                "success": True,
                "research_id": session.research_id,
                "question": session.question,
                "status": session.status,
                "sources_count": len(session.sources),
                "claims_count": len(session.claims),
                "conclusion": session.conclusion
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @app.get("/api/a2a/peers")
    async def get_a2a_peers(request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        if sandbox.a2a_protocol:
            peers = sandbox.a2a_protocol.list_peers()
            return {
                "peers": [
                    {
                        "agent_id": p.agent_id,
                        "name": p.name,
                        "description": p.description,
                        "version": p.version,
                        "capabilities": p.capabilities
                    }
                    for p in peers
                ]
            }
        return {"peers": []}

    @app.post("/api/chat")
    async def chat(msg: ChatMessage, request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        await sandbox.conversation_engine.inject_human_message(msg.message)
        return {"success": True}

    @app.post("/api/start")
    async def start_engine(request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        await sandbox.conversation_engine.resume()
        return {"success": True}

    @app.post("/api/pause")
    async def pause_engine(request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        await sandbox.conversation_engine.pause()
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
        sandbox.event_bus.subscribe_all(event_callback)
        
        try:
            while True:
                data = await queue.get()
                # Use default str for things that aren't JSON serializable (like Enums, dates)
                try:
                    await websocket.send_text(json.dumps(data, default=str))
                except Exception as e:
                    logger.error(f"Failed to send WS message: {e}")
                    break  # Break out of the loop if we can't send (e.g. connection closed)
        except WebSocketDisconnect:
            pass
        finally:
            sandbox.event_bus.unsubscribe_all(event_callback)
            
    return app

def start_server(config_path: str = "./config.yaml", port: int = 8000):
    app = create_app(config_path)
    uvicorn.run(app, host="0.0.0.0", port=port)
