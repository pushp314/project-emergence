from __future__ import annotations

import asyncio
import json
import logging
import sys
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from app.main import SandboxApp
from app.evidence import get_evidence_manager, EvidenceManager
from app.sessions import get_session_manager, SessionManager, SessionConfig
from app.reports import get_report_generator, ReportGenerator
from app.research import get_research_manager, ResearchManager
from app.decision import get_decision_manager, DecisionManager
from app.artifacts import get_artifact_manager, ArtifactManager
from app.capabilities import get_capability_registry, CapabilityRegistry
from app.self_modification import get_self_modification_engine, SelfModificationEngine
from app.resources import get_resource_manager, ResourceManager
from app.permissions import get_permission_manager, PermissionManager
from app.tools import get_tool_gateway, ToolGateway
from app.autonomy import get_autonomous_environment, AutonomousEnvironment
from app.models import get_model_registry

console = Console()
logger = logging.getLogger(__name__)


class CLIContext:
    def __init__(self):
        self.app: Optional[SandboxApp] = None
        self.running = False
    
    async def ensure_app(self, config_path: str = "./config.yaml") -> SandboxApp:
        if self.app is None:
            self.app = SandboxApp(config_path)
            await self.app.initialize()
        return self.app


cli_context = CLIContext()


@click.group()
@click.option('--config', '-c', default='./config.yaml', help='Config file path')
@click.pass_context
def cli(ctx, config):
    """AI Sandbox - Autonomous Multi-Agent AI Laboratory"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = config


@cli.command()
@click.option('--config', '-c', default='./config.yaml', help='Config file path')
def start(config):
    """Start the autonomous AI sandbox"""
    asyncio.run(_start_sandbox(config))


async def _start_sandbox(config_path: str):
    await _interactive_sandbox(config_path)


@cli.command()
@click.option('--config', '-c', default='./config.yaml', help='Config file path')
@click.option('--port', '-p', default=8000, help='API port')
def api(config, port):
    """Start the FastAPI server"""
    from app.api.server import start_server
    start_server(config, port)


@cli.command()
@click.option('--config', '-c', default='./config.yaml', help='Config file path')
def watch(config):
    """Watch agents without interactive input"""
    asyncio.run(_watch_sandbox(config))


async def _watch_sandbox(config_path: str):
    app = SandboxApp(config_path)
    await app.initialize()
    cli_context.app = app
    
    console.print(Panel.fit(
        "[bold cyan]AI SANDBOX - Watch Mode[/bold cyan]",
        border_style="cyan"
    ))
    
    try:
        await app.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping...[/yellow]")
        await app.shutdown()


@cli.command()
@click.option('--config', '-c', default='./config.yaml', help='Config file path')
def interactive(config):
    """Start interactive mode with CLI commands"""
    asyncio.run(_interactive_sandbox(config))


async def _interactive_sandbox(config_path: str):
    app = SandboxApp(config_path, start_paused=True)
    await app.initialize()
    cli_context.app = app
    
    app.conversation_engine.add_turn_callback(_on_turn_display)
    app.conversation_engine.add_thinking_callback(_on_thinking)
    
    console.print(Panel.fit(
        "[bold cyan]AI SANDBOX[/bold cyan]",
        border_style="cyan"
    ))
    console.print(f"[dim]Session:[/dim] {app.conversation_engine.conversation_id[:12]}")
    console.print()
    console.print("[bold]Agents are standing by.[/bold]")
    console.print()
    console.print("  [cyan]/start[/cyan]     Begin autonomous conversation")
    console.print("  [cyan]/stop[/cyan]      Pause agents")
    console.print("  [cyan]/status[/cyan]    System status")
    console.print("  [cyan]/tts[/cyan]       Toggle text-to-speech")
    console.print("  [cyan]/help[/cyan]      All commands")
    console.print()
    console.print("[dim]Type anything to send a message to the agents[/dim]")
    console.print()
    
    async def run_engine():
        await app.run()
    
    async def input_loop():
        while True:
            try:
                console.print()
                console.print("─" * 50, style="dim")
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input("YOU > ")
                )
                if not user_input.strip():
                    continue
                
                text = user_input.strip()
                
                if text.startswith("/"):
                    await _handle_command(app, text)
                else:
                    await app.conversation_engine.inject_human_message(text)
                    console.print("[green]  >> Sent[/green]")
                    
            except (EOFError, KeyboardInterrupt):
                break
    
    await asyncio.gather(run_engine(), input_loop())


_thinking_status = None

def _on_thinking(agent_name: str, turn_number: int):
    global _thinking_status
    icons = {"atlas": "🧭", "argus": "🔍", "explorer": "🧭"}
    icon = icons.get(agent_name, "•")
    name = agent_name.upper()
    if _thinking_status:
        try:
            _thinking_status.stop()
        except Exception:
            pass
    _thinking_status = console.status(f"[dim]{icon} {name} is thinking...[/dim]", spinner="dots")
    _thinking_status.start()

def _on_turn_display(message):
    global _thinking_status
    if _thinking_status:
        try:
            _thinking_status.stop()
        except Exception:
            _thinking_status = None
    
    identity_styles = {
        "atlas": {"color": "cyan", "icon": "🧭"},
        "argus": {"color": "magenta", "icon": "🔍"},
        "explorer": {"color": "cyan", "icon": "🧭"},
        "observer": {"color": "yellow", "icon": "👁"},
        "human": {"color": "green", "icon": "👤"}
    }
    style = identity_styles.get(message.agent_identity, {"color": "white", "icon": "•"})
    name = message.agent_identity.upper()
    
    panel = Panel(
        message.content,
        title=f"[bold {style['color']}]{style['icon']} {name}[/bold {style['color']}]  Turn {message.turn_number}",
        border_style=style["color"],
        padding=(0, 1),
        width=min(console.width, 100)
    )
    console.print(panel)


async def _handle_command(app: SandboxApp, command: str):
    parts = command.split()
    cmd = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    
    if cmd in ("/help", "/h"):
        _show_help()
    elif cmd in ("/start", "/go"):
        await app.conversation_engine.resume()
        console.print("[green]Agents started[/green]")
    elif cmd in ("/stop", "/s"):
        await app.conversation_engine.pause()
        console.print("[yellow]Agents paused[/yellow]")
    elif cmd in ("/pause", "/pa"):
        await app.conversation_engine.pause()
        console.print("[yellow]Paused[/yellow]")
    elif cmd in ("/resume", "/re"):
        await app.conversation_engine.resume()
        console.print("[green]Resumed[/green]")
    elif cmd in ("/status", "/st"):
        await _show_status(app)
    elif cmd in ("/sessions", "/ss"):
        await _show_sessions(app)
    elif cmd in ("/session", "/se"):
        await _show_session(app, args[0] if args else None)
    elif cmd in ("/memory", "/m"):
        await _show_memory(app)
    elif cmd in ("/research", "/r"):
        query = " ".join(args)
        if query:
            await _run_research_cli(app, query)
        else:
            await _show_research(app)
    elif cmd in ("/gaps", "/discover", "/unexplored"):
        await _show_research_gaps(app)
    elif cmd in ("/peers", "/agents", "/cards"):
        await _show_peers(app)
    elif cmd in ("/evidence", "/e"):
        await _show_evidence(app)
    elif cmd in ("/experiments", "/ex"):
        await _show_experiments(app)
    elif cmd in ("/permissions", "/perm"):
        await _show_permissions(app)
    elif cmd in ("/approve", "/ap"):
        await _approve_permission(app, args[0] if args else None)
    elif cmd in ("/deny", "/d"):
        await _deny_permission(app, args[0] if args else None)
    elif cmd in ("/tools", "/t"):
        await _show_tools(app)
    elif cmd in ("/tool",):
        if not args:
            console.print("[red]Usage: /tool <tool_name> [json_arguments][/red]")
        else:
            tool_name = args[0]
            args_str = " ".join(args[1:]) if len(args) > 1 else "{}"
            await _run_cli_tool(app, tool_name, args_str)
    elif cmd in ("/models", "/model"):
        await _show_models(app)
    elif cmd in ("/search", "/find"):
        query = " ".join(args)
        if query:
            await _search_memory_cli(app, query)
        else:
            console.print("[red]Usage: /search <query>[/red]")
    elif cmd in ("/resources", "/res"):
        await _show_resources(app)
    elif cmd in ("/logs", "/l"):
        await _show_logs(app)
    elif cmd in ("/timeline", "/tl"):
        await _show_timeline(app)
    elif cmd in ("/report", "/rep"):
        await _generate_report(app)
    elif cmd in ("/modifications", "/mod"):
        await _show_modifications(app)
    elif cmd in ("/rollback", "/rb"):
        await _rollback(app, args[0] if args else None)
    elif cmd in ("/inject", "/inj"):
        message = " ".join(args)
        if message:
            await app.conversation_engine.inject_human_message(message)
        else:
            console.print("[red]Usage: /inject <message>[/red]")
    elif cmd in ("/tts",):
        _toggle_tts(app)
    elif cmd in ("/join",):
        console.print("[green]You are now in the conversation. Type your message:[/green]")
    elif cmd in ("/db",):
        subcommand = args[0] if args else None
        await _handle_db_command(app, subcommand)
    else:
        console.print(f"[red]Unknown command: {cmd}[/red]")


async def _handle_db_command(app: SandboxApp, subcommand: Optional[str]):
    if not subcommand:
        console.print("[red]Usage: /db <subcommand>[/red]")
        console.print("  /db health   - Database health check")
        console.print("  /db backup   - Create database backup")
        console.print("  /db sessions - List sessions from database")
        console.print("  /db events   - Show recent events")
        console.print("  /db tables   - Show table names and row counts")
        console.print("  /db size     - Show database file size")
        return

    subcommand = subcommand.lower()

    if subcommand == "health":
        await _db_health(app)
    elif subcommand == "backup":
        await _db_backup(app)
    elif subcommand == "sessions":
        await _db_sessions(app)
    elif subcommand == "events":
        await _db_events(app)
    elif subcommand == "tables":
        await _db_tables(app)
    elif subcommand == "size":
        await _db_size(app)
    else:
        console.print(f"[red]Unknown /db subcommand: {subcommand}[/red]")


async def _db_health(app: SandboxApp):
    try:
        health = app.evidence_manager.get_db_health()
        table = Table(title="Database Health")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Integrity", "OK" if health.get("integrity_ok") else "FAILED")
        table.add_row("WAL Mode", str(health.get("wal_mode", False)))
        table.add_row("Tables", str(health.get("table_count", 0)))
        for name, count in health.get("row_counts", {}).items():
            table.add_row(f"  {name}", str(count))

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error checking health: {e}[/red]")


async def _db_backup(app: SandboxApp):
    try:
        path = app.evidence_manager.backup()
        console.print(f"[green]Backup created: {path}[/green]")
    except Exception as e:
        console.print(f"[red]Backup failed: {e}[/red]")


async def _db_sessions(app: SandboxApp):
    try:
        store = app.conversation_engine.context_manager.store
        with store._get_conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT conversation_id FROM conversations ORDER BY rowid DESC LIMIT 20"
            ).fetchall()

        if not rows:
            console.print("[yellow]No sessions in database[/yellow]")
            return

        table = Table(title="Database Sessions")
        table.add_column("Session ID", style="cyan")
        for row in rows:
            table.add_row(row[0])
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error listing sessions: {e}[/red]")


async def _db_events(app: SandboxApp):
    try:
        events = app.evidence_manager.get_timeline(limit=20)
        if not events:
            console.print("[yellow]No events found[/yellow]")
            return

        table = Table(title="Recent Events (Evidence DB)")
        table.add_column("Time", style="cyan")
        table.add_column("Type", style="white")
        table.add_column("Agent", style="white")
        table.add_column("Intent", style="white")

        for e in events:
            table.add_row(
                e.get("timestamp", "")[11:19],
                e.get("event_type", ""),
                e.get("agent_id", ""),
                (e.get("intent", "") or "")[:30],
            )
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error listing events: {e}[/red]")


async def _db_tables(app: SandboxApp):
    try:
        health = app.evidence_manager.get_db_health()
        row_counts = health.get("row_counts", {})

        table = Table(title="Database Tables")
        table.add_column("Table", style="cyan")
        table.add_column("Rows", style="white")

        for name, count in row_counts.items():
            table.add_row(name, str(count))

        if not row_counts:
            table.add_row("(none)", "-")
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error listing tables: {e}[/red]")


async def _db_size(app: SandboxApp):
    try:
        store = app.conversation_engine.context_manager.store
        db_path = Path(store.db_path)
        if db_path.exists():
            size = db_path.stat().st_size
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            console.print(f"[bold]Database:[/bold] {db_path}")
            console.print(f"[bold]Size:[/bold]     {size_str}")
        else:
            console.print(f"[yellow]Database file not found: {db_path}[/yellow]")
    except Exception as e:
        console.print(f"[red]Error checking size: {e}[/red]")


def _toggle_tts(app: SandboxApp):
    if not app._tts:
        console.print("[yellow]TTS not available. Enable in config.yaml: audio.tts_enabled: true[/yellow]")
        console.print("[dim]Requires: pip install TTS[/dim]")
        return
    if app._tts.is_speaking():
        asyncio.create_task(app._tts.stop())
        console.print("[yellow]TTS stopped[/yellow]")
    else:
        console.print("[green]TTS enabled - agents will be spoken aloud[/green]")


def _show_help():
    help_text = """
[bold]Available Commands:[/bold]

[bold]Control:[/bold]
  /start             Start autonomous conversation
  /stop              Pause agents
  /status            System status & metrics

[bold]Chat:[/bold]
  <text>             Send message to agents (no prefix needed)
  /inject <message>  Send message to agents

[bold]Audio:[/bold]
  /tts               Toggle text-to-speech

[bold]Tools & Capabilities:[/bold]
  /tools             Show all registered tools & permissions
  /tool <name> [json] Execute any tool manually (e.g. /tool terminal {"command":"ls"})
  /models            Show active LLM provider tiers, circuit breakers & key pool
  /search <query>    Search vector memory embeddings

[bold]Other:[/bold]
  /help              Show this help
  /pause             Pause (same as /stop)
  /resume            Resume (same as /start)
  /sessions          List sessions
  /memory            Show memory
  /evidence          Show evidence
  /resources         Show resource usage
  /logs              Show logs
  /report            Generate report

[bold]Database:[/bold]
  /db health         Database health check (integrity, WAL, row counts)
  /db backup         Create a database backup
  /db sessions       List sessions from database
  /db events         Show recent events from evidence database
  /db tables         Show table names and row counts
  /db size           Show database file size
"""
    console.print(Panel(help_text, title="Help", border_style="blue"))


async def _show_status(app: SandboxApp):
    state = app.conversation_engine.get_state()
    resources = app.resource_manager.get_metrics() if app.resource_manager else None
    
    table = Table(title="System Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Session ID", state.get("conversation_id", "Unknown"))
    table.add_row("Turn", str(state.get("turn_number", 0)))
    table.add_row("State", state.get("state", "Unknown"))
    table.add_row("Current Speaker", state.get("current_speaker", "Unknown"))
    table.add_row("Next Speaker", state.get("next_speaker", "Unknown"))
    table.add_row("Running", str(state.get("running", False)))
    table.add_row("Messages", str(state.get("message_count", 0)))
    
    if resources:
        table.add_row("RAM", f"{resources.ram_used_gb:.1f} / {resources.ram_total_gb:.1f} GB")
        table.add_row("CPU", f"{resources.cpu_percent:.1f}%")
        table.add_row("Inference Latency", f"{resources.generation_latency_ms:.0f} ms")
        table.add_row("Active Model", resources.active_model)
    
    console.print(table)


async def _show_sessions(app: SandboxApp):
    sessions = await app.session_manager.get_session_history()
    
    if not sessions:
        console.print("[yellow]No sessions found[/yellow]")
        return
    
    table = Table(title="Sessions")
    table.add_column("ID", style="cyan")
    table.add_column("Number", style="white")
    table.add_column("Status", style="white")
    table.add_row("Start Time", style="white")
    table.add_column("Turns", style="white")
    
    for s in sessions:
        status_color = {
            "COMPLETED": "green",
            "RUNNING": "yellow",
            "INTERRUPTED": "red",
            "PAUSED": "blue"
        }.get(s["status"], "white")
        
        table.add_row(
            s["session_id"][:8],
            str(s["session_number"]),
            f"[{status_color}]{s['status']}[/{status_color}]",
            s["start_time"][:19],
            str(s["current_turn"])
        )
    
    console.print(table)


async def _show_session(app: SandboxApp, session_id: Optional[str]):
    if not session_id:
        session_id = app.conversation_engine.conversation_id
    
    session = app.session_manager.get_session_info(session_id)
    if not session:
        console.print(f"[red]Session {session_id} not found[/red]")
        return
    
    console.print(Panel(f"[bold]Session:[/bold] {session['session_id']}\n"
                        f"[bold]Number:[/bold] {session['session_number']}\n"
                        f"[bold]Status:[/bold] {session['status']}\n"
                        f"[bold]Start:[/bold] {session['start_time']}\n"
                        f"[bold]End:[/bold] {session['end_time'] or 'Running'}\n"
                        f"[bold]Current Turn:[/bold] {session['current_turn']}\n"
                        f"[bold]Current Speaker:[/bold] {session['current_speaker']}", 
                        title="Session Details", border_style="cyan"))


async def _show_memory(app: SandboxApp):
    if not app.memory_manager:
        console.print("[red]Memory manager not available[/red]")
        return
    
    turn = app.conversation_engine.turn_number
    context = await app.memory_manager.get_context(turn)
    
    console.print(Panel(f"[bold]Recent Messages:[/bold] {len(context.get('recent_messages', []))}\n"
                        f"[bold]Summary:[/bold] {context.get('summary', 'None')[:200]}...\n"
                        f"[bold]Important Facts:[/bold] {len(context.get('important_facts', []))}\n"
                        f"[bold]Open Questions:[/bold] {len(context.get('open_questions', []))}", 
                        title="Memory", border_style="cyan"))


async def _run_research_cli(app: SandboxApp, query: str):
    if not app.research_manager:
        console.print("[red]ResearchManager not initialized[/red]")
        return
    with console.status(f"[bold cyan]🔬 Conducting deep autonomous research & synthesis on '{query}'...[/bold cyan]"):
        try:
            session = await app.research_manager.research(
                agent_id="operator",
                question=query,
                reason=f"CLI operator research: {query}",
                max_sources=4,
                export_desktop=True
            )
            console.print(f"[green]✓ Autonomous Deep Research Completed:[/green] [bold white]{session.question}[/bold white]")
            console.print(f"  Status: [cyan]{session.status}[/cyan] | Sources: [yellow]{len(session.sources)}[/yellow] | Claims: [magenta]{len(session.claims)}[/magenta]")
            
            desktop_path = session.metadata.get("desktop_path")
            if desktop_path:
                console.print(f"  📁 [bold green]Published to Desktop:[/bold green] [bold white underline]{desktop_path}[/bold white underline]")

            report_path = session.metadata.get("report_path")
            if report_path and Path(report_path).exists():
                with open(report_path, encoding="utf-8") as f:
                    content = f.read()
                preview = content[:1200] + ("\n\n... [Full Report on Desktop]" if len(content) > 1200 else "")
                console.print(Panel(preview, title="🔬 Research Paper Preview", border_style="green"))

            for sid in session.sources:
                s = app.research_manager.get_source(sid)
                if s:
                    console.print(f"  • [blue]{s.title}[/blue] ({s.url})")
        except Exception as e:
            console.print(f"[red]Research failed: {e}[/red]")


async def _show_research_gaps(app: SandboxApp):
    if not app.research_manager:
        console.print("[red]ResearchManager not initialized[/red]")
        return
    with console.status("[bold magenta]🔭 Analyzing previous research coverage and discovering unexplored gaps...[/bold magenta]"):
        try:
            data = await app.research_manager.discover_unexplored_gaps(limit=5)
            gaps = data.get("recommended_gaps", [])
            if not gaps:
                console.print("[yellow]No new research gaps found[/yellow]")
                return

            table = Table(title=f"🔭 Unexplored Research Frontiers (Analyzed {data.get('analyzed_previous_topics_count', 0)} Past Sessions)")
            table.add_column("#", style="cyan", width=3)
            table.add_column("Category", style="yellow", width=14)
            table.add_column("Novel Research Topic", style="bold white", width=36)
            table.add_column("Impact", style="bold green", width=8)
            table.add_column("Rationale & Gap", style="white")

            for i, gap in enumerate(gaps):
                impact_style = "green" if gap.get("impact") == "HIGH" else "yellow"
                table.add_row(
                    str(i + 1),
                    gap.get("category", "General"),
                    gap.get("topic", "N/A"),
                    f"[{impact_style}]{gap.get('impact', 'MED')}[/{impact_style}]",
                    f"{gap.get('rationale', '')} [italic dim]({gap.get('unexplored_aspect', '')})[/italic dim]"
                )

            console.print(table)
            console.print("[dim cyan]Tip: Run `/research <topic>` to immediately launch autonomous research on any novel gap.[/dim cyan]")
        except Exception as e:
            console.print(f"[red]Gap discovery failed: {e}[/red]")


async def _show_peers(app: SandboxApp):
    if not app.a2a_protocol:
        console.print("[yellow]A2A Protocol not initialized[/yellow]")
        return
    peers = app.a2a_protocol.list_peers()
    if not peers:
        console.print("[yellow]No A2A peers registered[/yellow]")
        return
    table = Table(title="A2A Protocol Registered Agent Cards")
    table.add_column("Agent ID", style="cyan")
    table.add_column("Name", style="bold white")
    table.add_column("Description", style="white")
    table.add_column("Capabilities", style="yellow")
    for p in peers:
        table.add_row(
            p.agent_id,
            p.name,
            p.description,
            ", ".join(p.capabilities)
        )
    console.print(table)


async def _show_research(app: SandboxApp):
    evidence_mgr = app.evidence_manager
    research = evidence_mgr.get_session_evidence(
        evidence_type="research_started"
    )
    
    if not research:
        console.print("[yellow]No research found[/yellow]")
        return
    
    table = Table(title="Research")
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Agent", style="white")
    table.add_column("Reason", style="white")
    
    for r in research[:20]:
        table.add_row(
            r.get("evidence_id", "")[:12],
            r.get("evidence_type", ""),
            r.get("agent_id", ""),
            r.get("reason", "")[:50]
        )
    
    console.print(table)


async def _show_evidence(app: SandboxApp):
    evidence_mgr = app.evidence_manager
    evidence = evidence_mgr.get_session_evidence(limit=50)
    
    if not evidence:
        console.print("[yellow]No evidence found[/yellow]")
        return
    
    table = Table(title="Evidence")
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Agent", style="white")
    table.add_column("Intent", style="white")
    table.add_column("Reason", style="white")
    
    for e in evidence:
        table.add_row(
            e.get("evidence_id", "")[:12],
            e.get("evidence_type", ""),
            e.get("agent_id", ""),
            e.get("intent", "")[:30],
            e.get("reason", "")[:40]
        )
    
    console.print(table)


async def _show_experiments(app: SandboxApp):
    evidence_mgr = app.evidence_manager
    experiments = evidence_mgr.get_session_evidence(
        evidence_type="experiment_started"
    )
    
    if not experiments:
        console.print("[yellow]No experiments found[/yellow]")
        return
    
    table = Table(title="Experiments")
    table.add_column("ID", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Agent", style="white")
    table.add_column("Reason", style="white")
    
    for e in experiments:
        table.add_row(
            e.get("evidence_id", "")[:12],
            e.get("evidence_type", ""),
            e.get("agent_id", ""),
            e.get("reason", "")[:50]
        )
    
    console.print(table)


async def _show_permissions(app: SandboxApp):
    if not app.permission_manager:
        console.print("[red]Permission manager not available[/red]")
        return
    
    pending = app.permission_manager.get_pending()
    history = app.permission_manager.get_history()
    
    if pending:
        table = Table(title="Pending Permissions")
        table.add_column("ID", style="cyan")
        table.add_column("Agent", style="white")
        table.add_column("Action", style="white")
        table.add_column("Risk", style="white")
        
        for p in pending:
            table.add_row(
                p.request.request_id[:12],
                p.request.agent_id,
                p.request.action,
                p.request.risk.value
            )
        console.print(table)
    
    if history:
        console.print(f"\n[dim]Total permission requests: {len(history)}[/dim]")


async def _approve_permission(app: SandboxApp, perm_id: Optional[str]):
    if not app.permission_manager or not perm_id:
        console.print("[red]Usage: /approve <permission_id>[/red]")
        return
    
    result = await app.permission_manager.approve(perm_id)
    if result:
        console.print(f"[green]Permission {perm_id} approved[/green]")
    else:
        console.print(f"[red]Permission {perm_id} not found[/red]")


async def _deny_permission(app: SandboxApp, perm_id: Optional[str]):
    if not app.permission_manager or not perm_id:
        console.print("[red]Usage: /deny <permission_id>[/red]")
        return
    
    result = await app.permission_manager.deny(perm_id)
    if result:
        console.print(f"[red]Permission {perm_id} denied[/red]")
    else:
        console.print(f"[red]Permission {perm_id} not found[/red]")


async def _show_tools(app: SandboxApp):
    if not app.tool_gateway:
        console.print("[red]Tool gateway not available[/red]")
        return
    
    tools = app.tool_gateway.list_tools()
    
    table = Table(title="Available Tools")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Permission", style="white")
    table.add_column("Risk", style="white")
    
    for t in tools:
        table.add_row(t.name, t.description[:50], t.permission.value, t.risk.value)
    
    console.print(table)


async def _run_cli_tool(app: SandboxApp, tool_name: str, args_str: str):
    import json
    if not app.tool_gateway:
        console.print("[red]Tool gateway not available[/red]")
        return

    try:
        arguments = json.loads(args_str) if args_str.strip() else {}
    except Exception as e:
        console.print(f"[red]Invalid JSON arguments: {e}[/red]")
        return

    from app.events.schemas import ToolCall
    call = ToolCall(tool_name=tool_name, arguments=arguments, agent_id="cli_operator")
    console.print(f"[cyan]Executing tool '{tool_name}' with args:[/cyan] {arguments}")
    
    result = await app.tool_gateway.execute(call)
    if result.success:
        console.print(Panel(str(result.result), title=f"✓ Tool Result ({tool_name})", border_style="green"))
    else:
        console.print(Panel(str(result.error), title=f"✗ Tool Error ({tool_name})", border_style="red"))


async def _show_models(app: SandboxApp):
    registry = app.model_registry
    table = Table(title="Model Providers & Resilient Routers")
    table.add_column("Route", style="cyan")
    table.add_column("Active Model", style="white")
    table.add_column("State", style="green")
    table.add_column("Failover Chain", style="dim")
    table.add_column("Key Pool / Details", style="white")

    for name, adapter in registry._adapters.items():
        if hasattr(adapter, "get_telemetry"):
            telemetry = adapter.get_telemetry()
            active = telemetry.get("active_tier", name)
            tiers = telemetry.get("tiers", [])
            tier_names = [f"{t['name']} ({t['state']})" for t in tiers]
            
            key_details = "N/A"
            for t in tiers:
                if "details" in t and "key_pool" in t["details"]:
                    kp = t["details"]["key_pool"]
                    key_details = f"{kp.get('active_keys', 0)}/{kp.get('total_keys', 0)} Keys Active"

            table.add_row(
                name,
                active,
                "[green]Online[/green]",
                " ➔ ".join(tier_names),
                key_details
            )
        elif hasattr(adapter, "get_model_info"):
            info = adapter.get_model_info()
            table.add_row(name, info.get("name", name), "[green]Direct[/green]", "None", str(info.get("backend", "")))
        else:
            table.add_row(name, name, "[white]Custom[/white]", "None", type(adapter).__name__)

    console.print(table)


async def _search_memory_cli(app: SandboxApp, query: str):
    if not app.vector_store:
        console.print("[yellow]Vector memory store not configured[/yellow]")
        return

    try:
        results = app.vector_store.search(query, limit=5)
        if not results:
            console.print(f"[yellow]No memory matches found for '{query}'[/yellow]")
            return

        table = Table(title=f"Vector Memory Search: '{query}'")
        table.add_column("Memory ID", style="cyan")
        table.add_column("Distance", style="yellow")
        table.add_column("Content Preview", style="white")

        for r in results:
            dist = f"{r.get('distance', 0):.3f}" if r.get('distance') is not None else "N/A"
            text = r.get("content") or r.get("text") or str(r)
            table.add_row(r.get("id", "")[:12], dist, text[:120])

        console.print(table)
    except Exception as e:
        console.print(f"[red]Memory search error: {e}[/red]")


async def _show_resources(app: SandboxApp):
    if not app.resource_manager:
        console.print("[red]Resource manager not available[/red]")
        return
    
    state = app.resource_manager.get_state()
    metrics = state.metrics
    
    if not metrics:
        console.print("[yellow]No metrics available[/yellow]")
        return
    
    table = Table(title="Resource Usage")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("RAM", f"{metrics.ram_used_gb:.1f} / {metrics.ram_total_gb:.1f} GB ({metrics.ram_percent:.1f}%)")
    table.add_row("CPU", f"{metrics.cpu_percent:.1f}%")
    table.add_row("Inference Latency", f"{metrics.generation_latency_ms:.0f} ms")
    table.add_row("Active Model", metrics.active_model)
    table.add_row("Queue Length", str(metrics.queue_length))
    
    if state.warnings:
        console.print("\n[bold red]Warnings:[/bold red]")
        for w in state.warnings:
            console.print(f"  [red]• {w}[/red]")
    
    console.print(table)


async def _show_logs(app: SandboxApp):
    log_file = Path("./logs/sandbox.log")
    if not log_file.exists():
        console.print("[yellow]No log file found[/yellow]")
        return
    
    try:
        with open(log_file) as f:
            lines = f.readlines()[-50:]
        
        console.print("[bold]Recent Logs:[/bold]")
        for line in lines:
            console.print(line.rstrip())
    except Exception as e:
        console.print(f"[red]Error reading logs: {e}[/red]")


async def _show_timeline(app: SandboxApp):
    timeline = app.evidence_manager.get_timeline()
    
    if not timeline:
        console.print("[yellow]No timeline events[/yellow]")
        return
    
    table = Table(title="Timeline")
    table.add_column("Time", style="cyan")
    table.add_column("Type", style="white")
    table.add_column("Agent", style="white")
    table.add_column("Intent", style="white")
    table.add_column("Reason", style="white")
    
    for e in timeline[-30:]:
        table.add_row(
            e.get("timestamp", "")[11:19],
            e.get("event_type", ""),
            e.get("agent_id", ""),
            e.get("intent", "")[:30],
            e.get("reason", "")[:40]
        )
    
    console.print(table)


async def _generate_report(app: SandboxApp):
    try:
        from app.reports.generator import ReportGenerator
        generator = ReportGenerator(
            evidence_manager=app.evidence_manager,
            session_manager=app.session_manager
        )
        report_path = generator.generate_final_report(
            app.conversation_engine.conversation_id if app.conversation_engine else None
        )
        console.print(f"[green]✓ Report generated successfully:[/green] [bold white]{report_path}[/bold white]")
        if Path(report_path).exists():
            with open(report_path) as f:
                content = f.read()
            console.print(Panel(content[:1500] + ("\n..." if len(content) > 1500 else ""), title="Session Report Preview", border_style="green"))
    except Exception as e:
        console.print(f"[red]Error generating report: {e}[/red]")


async def _show_modifications(app: SandboxApp):
    if not hasattr(app, 'self_modification_engine') or not app.self_modification_engine:
        console.print("[yellow]Self-modification engine not available[/yellow]")
        return
    
    mods = app.self_modification_engine.get_active_modifications()
    
    if not mods:
        console.print("[yellow]No active modifications[/yellow]")
        return
    
    table = Table(title="Self-Modifications")
    table.add_column("ID", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Problem", style="white")
    
    for m in mods:
        table.add_row(
            m.modification_id[:12],
            m.status,
            m.reason[:50]
        )
    
    console.print(table)


async def _rollback(app: SandboxApp, mod_id: Optional[str]):
    if not hasattr(app, 'self_modification_engine') or not app.self_modification_engine:
        console.print("[red]Self-modification engine not available[/red]")
        return
    
    if not mod_id:
        console.print("[red]Usage: /rollback <modification_id>[/red]")
        return
    
    result = await app.self_modification_engine.rollback_modification(mod_id)
    if result:
        console.print(f"[green]Modification {mod_id} rolled back[/green]")
    else:
        console.print(f"[red]Rollback failed for {mod_id}[/red]")


@cli.command()
@click.argument('log_file', type=click.Path(exists=True))
@click.option('--config', '-c', default='./config.yaml', help='Config file path')
def autofix(log_file, config):
    """Autonomously fix a crash based on a log file"""
    asyncio.run(_autofix(log_file, config))

async def _autofix(log_file: str, config_path: str):
    console.print(f"[bold cyan]Auto-Fixer Initiated[/bold cyan] reading {log_file}")
    with open(log_file, 'r') as f:
        crash_log = f.read()

    app = SandboxApp(config_path, start_paused=True)
    await app.initialize()
    cli_context.app = app
    
    app.conversation_engine.add_thinking_callback(_on_thinking)
    
    prompt = f"""CRITICAL SYSTEM CRASH DETECTED.
The application just crashed with the following traceback:

{crash_log}

Your objective: Fix this bug immediately.
1. Use your filesystem/terminal tools to read the file(s) mentioned in the traceback.
2. Identify the root cause of the crash.
3. Use the filesystem tool (write/append) or terminal tools to modify the broken file(s) and apply the fix.
4. When you are absolutely certain the fix is applied to the codebase, reply with exactly the phrase "FIX_COMPLETE".

DO NOT try to run or restart the application yourself. Just apply the code changes.
"""
    
    await app.conversation_engine.inject_human_message(prompt)
    await app.conversation_engine.resume()
    
    fix_completed = asyncio.Event()
    
    def check_fix(message):
        _on_turn_display(message)
        if "FIX_COMPLETE" in message.content:
            console.print("[bold green]Agent reported fix complete![/bold green]")
            fix_completed.set()
            
    app.conversation_engine.add_turn_callback(check_fix)
    
    run_task = asyncio.create_task(app.run())
    
    try:
        await asyncio.wait_for(fix_completed.wait(), timeout=300)
    except asyncio.TimeoutError:
        console.print("[bold red]Auto-fixer timed out after 5 minutes.[/bold red]")
    
    await app.shutdown()
    try:
        await run_task
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    cli()