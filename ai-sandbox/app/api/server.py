import asyncio
import json
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from pydantic import BaseModel

import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.main import SandboxApp
from app.events.bus import EventType

logger = logging.getLogger(__name__)

# --- Models ---
class ChatMessage(BaseModel):
    message: str
    mode: Optional[str] = "24/7"

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

    # Start 24/7 Standing Daemon Scheduler
    from app.orchestration.daemon_scheduler import get_daemon_scheduler
    daemon_sched = get_daemon_scheduler()
    daemon_sched.event_bus = sandbox.event_bus
    await daemon_sched.start()
    app.state.daemon_scheduler = daemon_sched
    
    yield
    
    # Shutdown
    await daemon_sched.stop()
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
                return {"results": [], "error": str(e)}
        return {"results": [], "error": "Vector store not initialized or empty query"}

    @app.get("/api/analytics/metrics")
    async def get_analytics_metrics(request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        import psutil
        try:
            # System stats
            cpu_percent = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory()
            ram_percent = ram.percent
            
            # DB stats
            total_sessions = 0
            total_memories = sandbox.vector_store.collection.count() if sandbox.vector_store else 0
            
            if sandbox.session_manager:
                with sandbox.session_manager._get_conn() as conn:
                    row = conn.execute("SELECT COUNT(*) as c FROM session_metadata").fetchone()
                    if row:
                        total_sessions = row["c"]
            
            return {
                "success": True,
                "system": {
                    "cpu_percent": cpu_percent,
                    "ram_percent": ram_percent,
                    "ram_used_gb": round(ram.used / (1024**3), 2),
                    "ram_total_gb": round(ram.total / (1024**3), 2)
                },
                "database": {
                    "total_sessions": total_sessions,
                    "total_vector_memories": total_memories
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @app.delete("/api/memory/vectors/{memory_id}")
    async def delete_vector(memory_id: str, request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        if sandbox.vector_store:
            try:
                success = await sandbox.vector_store.delete_memory_async(memory_id)
                return {"success": success}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "Vector store not initialized"}

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

    @app.post("/api/sessions")
    async def create_session(request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        if sandbox.session_manager and sandbox.conversation_engine:
            try:
                # Generate a new session ID
                new_session_id = str(uuid.uuid4())
                # Reset engine to new session
                sandbox.conversation_engine.reset(new_session_id)
                
                # We need to recreate the session config using the new ID. 
                # Normally the manager does this on start, but we can just use the engine's config
                from app.sessions.manager import SessionConfig
                config = SessionConfig(
                    session_id=new_session_id,
                    initial_speaker=sandbox.conversation_engine.config.initial_speaker
                )
                session = await sandbox.session_manager.create_session(config)
                
                return {"success": True, "session_id": new_session_id, "session": session.__dict__}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "Session manager not available"}

    @app.post("/api/sessions/{session_id}/switch")
    async def switch_session(session_id: str, request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        if sandbox.session_manager and sandbox.conversation_engine:
            try:
                # Pause current if running
                if sandbox.conversation_engine.is_running:
                    await sandbox.conversation_engine.pause()
                    
                # Reset the engine state to the target session ID
                sandbox.conversation_engine.reset(session_id)
                
                # Check if session exists in DB
                session_info = sandbox.session_manager.get_session_info(session_id)
                if not session_info:
                    return {"success": False, "error": "Session not found"}
                
                # Update current session in manager
                # Since we don't have a perfect "switch_session" in SessionManager, 
                # we just use recover_session which achieves the same thing by loading state
                await sandbox.session_manager.recover_session(session_id)
                
                return {"success": True, "session_id": session_id}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "Session manager not available"}

    @app.delete("/api/sessions/{session_id}")
    async def delete_session(session_id: str, request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        if sandbox.session_manager:
            try:
                success = await sandbox.session_manager.delete_session(session_id)
                return {"success": success}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "Session manager not available"}

    @app.get("/api/sessions/{session_id}/messages")
    async def get_session_messages(session_id: str, request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        try:
            # We fetch evidence of type human_message and agent_message for this session
            evidence_manager = sandbox.session_manager.evidence_manager
            # We can use get_session_evidence or we could just filter timeline
            timeline = evidence_manager.get_timeline(session_id=session_id)
            messages = []
            
            for item in timeline:
                event_type = item.get("event_type")
                if event_type in ["agent.message", "human.message.processed"]:
                    payload = item.get("payload", {})
                    # Format matching our frontend Message interface
                    messages.append({
                        "id": str(item.get("evidence_id")),
                        "sender": "user" if event_type == "human.message.processed" else "agent",
                        "content": payload.get("content", ""),
                        "thought": payload.get("thought"),
                        "model": payload.get("model"),
                        "timestamp": item.get("timestamp")
                    })
            
            return {"messages": messages}
        except Exception as e:
            return {"messages": [], "error": str(e)}

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
        question = req.get("question") or req.get("query") or req.get("topic")
        if not question:
            raise HTTPException(status_code=400, detail="question or topic is required")
        
        agent_id = req.get("agent_id", "researcher")
        max_sources = req.get("max_sources", 5)
        export_desktop = req.get("export_desktop", True)

        if not sandbox.research_manager:
            raise HTTPException(status_code=500, detail="Research manager not available")

        try:
            session = await sandbox.research_manager.research(
                agent_id=agent_id,
                question=question,
                reason=f"Operator requested research on: {question}",
                max_sources=max_sources,
                export_desktop=export_desktop
            )
            return {
                "success": True,
                "research_id": session.research_id,
                "question": session.question,
                "status": session.status,
                "sources_count": len(session.sources),
                "claims_count": len(session.claims),
                "conclusion": session.conclusion,
                "report_path": session.metadata.get("report_path", ""),
                "desktop_path": session.metadata.get("desktop_path", ""),
                "summary": session.metadata.get("summary", "")
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @app.get("/api/research/gaps")
    async def get_research_gaps(request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        if not sandbox.research_manager:
            raise HTTPException(status_code=500, detail="Research manager not available")
        try:
            data = await sandbox.research_manager.discover_unexplored_gaps(limit=5)
            return {"success": True, **data}
        except Exception as e:
            return {"success": False, "error": str(e), "recommended_gaps": []}

    @app.post("/api/research/discover")
    async def auto_discover_and_research(req: Dict[str, Any], request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        if not sandbox.research_manager:
            raise HTTPException(status_code=500, detail="Research manager not available")
        try:
            gaps_data = await sandbox.research_manager.discover_unexplored_gaps(limit=1)
            recommended = gaps_data.get("recommended_gaps", [])
            if not recommended:
                raise HTTPException(status_code=404, detail="No new research gaps found")
            
            top_gap = recommended[0]
            topic = top_gap.get("topic")
            
            session = await sandbox.research_manager.research(
                agent_id="researcher",
                question=topic,
                reason=f"Autonomous gap discovery: {top_gap.get('rationale', '')}",
                max_sources=5,
                export_desktop=True
            )
            return {
                "success": True,
                "discovered_topic": topic,
                "gap_metadata": top_gap,
                "research_id": session.research_id,
                "status": session.status,
                "desktop_path": session.metadata.get("desktop_path", ""),
                "summary": session.metadata.get("summary", "")
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
        from app.agents.system_controller import get_mac_controller
        controller = get_mac_controller()
        controller.tool_gateway = sandbox.tool_gateway
        controller.event_bus = sandbox.event_bus

        # Publish human message event
        await sandbox.event_bus.publish_type(
            EventType.HUMAN_MESSAGE,
            sandbox.conversation_engine.conversation_id,
            {"content": msg.message}
        )

        # Execute autonomously on Mac system
        try:
            result = await controller.execute_task(
                task=msg.message,
                conversation_id=sandbox.conversation_engine.conversation_id,
                mode="24/7"
            )
            return {"success": True, **result}
        except Exception as e:
            logger.error(f"MacSystemController error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    @app.post("/api/agent/execute")
    async def agent_execute(req: Dict[str, Any], request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        task = req.get("task") or req.get("message")
        if not task:
            raise HTTPException(status_code=400, detail="task is required")
        
        mode = req.get("mode", "24/7")
        from app.agents.system_controller import get_mac_controller
        controller = get_mac_controller()
        controller.tool_gateway = sandbox.tool_gateway
        controller.event_bus = sandbox.event_bus

        result = await controller.execute_task(
            task=task,
            conversation_id=sandbox.conversation_engine.conversation_id,
            mode=mode
        )
        return {"success": True, **result}

    @app.post("/api/vision/screen")
    async def inspect_screen(req: Dict[str, Any], request: Request):
        sandbox: SandboxApp = request.app.state.sandbox
        prompt = req.get("prompt", "Analyze what is currently open on my Mac screen, identify active applications, code, or any visual errors, and provide a helpful summary.")
        
        # 1. Take screenshot using tool
        vision_tool = sandbox.tool_gateway.get_tool("screenshot")
        if not vision_tool:
            raise HTTPException(status_code=500, detail="Vision/Screenshot tool not available")
        
        snap_res = await vision_tool.execute({})
        if not snap_res.get("success"):
            return {"success": False, "error": snap_res.get("error", "Screenshot capture failed")}
        
        base64_img = snap_res.get("image_base64")
        file_path = snap_res.get("file_path")
        
        # 2. Multimodal LLM analysis
        try:
            from app.models.base import get_model_registry, GenerationRequest
            registry = get_model_registry()
            model = registry.get("default")
            
            gen_req = GenerationRequest(
                prompt=f"{prompt}\n[Attached: Base64 macOS Screen Capture]",
                system_prompt="You are an expert macOS Vision Assistant. Examine the user's screen capture, interpret all visual context accurately, and provide a clear, concise breakdown.",
                images=[base64_img] if base64_img else [],
                temperature=0.3,
                max_tokens=2000
            )
            response = await model.generate(gen_req)
            analysis_text = response.text.strip()
            
            # Emit event to WebSocket
            await sandbox.event_bus.publish_type(
                EventType.AGENT_MESSAGE,
                sandbox.conversation_engine.conversation_id,
                {"content": analysis_text, "screenshot_path": file_path}
            )
            
            return {
                "success": True,
                "analysis": analysis_text,
                "screenshot_path": file_path,
                "image_base64": base64_img[:500] + "..." if base64_img else None,
                "timestamp": snap_res.get("timestamp")
            }
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}", exc_info=True)
            return {
                "success": True,
                "analysis": f"Screenshot captured successfully at `{file_path}`. (Vision model note: {e})",
                "screenshot_path": file_path
            }

    @app.get("/api/scheduler/jobs")
    async def get_scheduled_jobs():
        from app.orchestration.daemon_scheduler import get_daemon_scheduler
        sched = get_daemon_scheduler()
        return {"success": True, "jobs": sched.list_jobs()}

    @app.post("/api/scheduler/jobs")
    async def add_scheduled_job(req: Dict[str, Any]):
        name = req.get("name", "Standing Autonomous Mission")
        task_prompt = req.get("task_prompt", "")
        interval_seconds = req.get("interval_seconds", 900)
        is_active = req.get("is_active", True)
        
        if not task_prompt:
            raise HTTPException(status_code=400, detail="task_prompt is required")
        
        from app.orchestration.daemon_scheduler import get_daemon_scheduler
        sched = get_daemon_scheduler()
        job = sched.add_job(name, task_prompt, interval_seconds, is_active)
        return {"success": True, "job": job.__dict__ if hasattr(job, "__dict__") else job}

    @app.post("/api/scheduler/jobs/{job_id}/toggle")
    async def toggle_scheduled_job(job_id: str):
        from app.orchestration.daemon_scheduler import get_daemon_scheduler
        sched = get_daemon_scheduler()
        job = sched.toggle_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"success": True, "job": job.__dict__ if hasattr(job, "__dict__") else job}

    @app.delete("/api/scheduler/jobs/{job_id}")
    async def delete_scheduled_job(job_id: str):
        from app.orchestration.daemon_scheduler import get_daemon_scheduler
        sched = get_daemon_scheduler()
        deleted = sched.delete_job(job_id)
        return {"success": deleted}

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
