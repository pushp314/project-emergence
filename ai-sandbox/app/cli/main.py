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
from rich.live import Live
from rich.layout import Layout

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
    app = SandboxApp(config_path)
    await app.initialize()
    cli_context.app = app
    
    console.print(Panel.fit(
        "[bold cyan]AI SANDBOX - Autonomous Multi-Agent Conversation[/bold cyan]",
        border_style="cyan"
    ))
    
    console.print(f"[green]Conversation ID:[/green] {app.conversation_engine.conversation_id}")
    console.print(f"[green]Agents:[/green] A (Explorer) <-> B (Challenger)")
    if app.resource_manager:
        console.print(f"[green]Resource Monitoring:[/green] Enabled")
    console.print("[yellow]Press Ctrl+C to stop[/yellow]\n")
    
    try:
        await app.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutdown requested...[/yellow]")
        await app.shutdown()


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
    app = SandboxApp(config_path)
    await app.initialize()
    cli_context.app = app
    
    console.print(Panel.fit(
        "[bold cyan]AI SANDBOX - Interactive Mode[/bold cyan]",
        border_style="cyan"
    ))
    console.print("[green]Commands:[/green] /help, /status, /pause, /resume, /stop, /sessions, /memory, /research, /evidence, /experiments, /permissions, /approve, /deny, /resources, /report, /inject")
    console.print("[yellow]Type your message or command. Ctrl+C to exit.[/yellow]\n")
    
    app.conversation_engine.add_turn_callback(_on_turn_display)
    
    async def input_loop():
        while app.conversation_engine.is_running:
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(None, input, "YOU > ")
                if user_input.strip():
                    if user_input.startswith("/"):
                        await _handle_command(app, user_input.strip())
                    else:
                        await app.conversation_engine.inject_human_message(user_input.strip())
            except (EOFError, KeyboardInterrupt):
                break
    
    await asyncio.gather(app.run(), input_loop())


def _on_turn_display(message):
    role_colors = {
        "explorer": "cyan",
        "challenger": "magenta",
        "observer": "yellow",
        "human": "green"
    }
    color = role_colors.get(message.role.value, "white")
    console.print(f"[bold {color}][{message.role.value.upper()}][/bold {color}] Turn {message.turn_number}")
    console.print(message.content)
    console.print()


async def _handle_command(app: SandboxApp, command: str):
    parts = command.split()
    cmd = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    
    if cmd in ("/help", "/h"):
        _show_help()
    elif cmd in ("/status", "/st"):
        await _show_status(app)
    elif cmd in ("/pause", "/pa"):
        await app.conversation_engine.pause()
        console.print("[yellow]Paused[/yellow]")
    elif cmd in ("/resume", "/re"):
        await app.conversation_engine.resume()
        console.print("[green]Resumed[/green]")
    elif cmd in ("/stop", "/s"):
        await app.shutdown()
        console.print("[red]Stopped[/red]")
    elif cmd in ("/sessions", "/ss"):
        await _show_sessions(app)
    elif cmd in ("/session", "/se"):
        await _show_session(app, args[0] if args else None)
    elif cmd in ("/memory", "/m"):
        await _show_memory(app)
    elif cmd in ("/research", "/r"):
        await _show_research(app)
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
    else:
        console.print(f"[red]Unknown command: {cmd}[/red]")


def _show_help():
    help_text = """
[bold]Available Commands:[/bold]

[bold]System Control:[/bold]
  /help, /h          Show this help
  /status, /st       Show system status
  /pause, /pa        Pause the conversation
  /resume, /re       Resume the conversation
  /stop, /s          Stop the system

[bold]Session Management:[/bold]
  /sessions, /ss     List all sessions
  /session <id>      Show session details

[bold]Inspection:[/bold]
  /memory, /m        Show memory state
  /research, /r      Show research
  /evidence, /e      Show evidence
  /experiments, /ex  Show experiments
  /permissions, /perm Show permissions
  /tools, /t         Show available tools
  /resources, /res   Show resource usage
  /logs, /l          Show recent logs
  /timeline, /tl     Show event timeline
  /report, /rep      Generate session report

[bold]Permissions:[/bold]
  /approve <id>      Approve permission request
  /deny <id>         Deny permission request

[bold]Modifications:[/bold]
  /modifications     Show self-modifications
  /rollback <id>     Rollback modification

[bold]Interaction:[/bold]
  /inject <message>  Send message to agents
  <text>             Send message to agents (no prefix)
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
        report_path = app.session_manager.generate_final_report(app.conversation_engine.conversation_id)
        console.print(f"[green]Report generated: {report_path}[/green]")
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


if __name__ == "__main__":
    cli()