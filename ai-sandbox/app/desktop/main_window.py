from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QPushButton, QLineEdit, QLabel, QCheckBox,
    QTabWidget, QListWidget, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QTimer
import asyncio
from app.main import SandboxApp
import logging
from app.voice.engine import get_voice_engine
from app.voice.listener import ContinuousVoiceListener
from app.orchestration.goal_loop import GoalState

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    event_signal = pyqtSignal(dict)
    voice_status_signal = pyqtSignal(bool)
    
    def __init__(self, sandbox_app: SandboxApp):
        super().__init__()
        self.sandbox_app = sandbox_app
        self.setWindowTitle("AI Sandbox Desktop")
        self.setMinimumSize(900, 650)
        
        # macOS Dark Mode Premium Styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f172a;
            }
            QTextEdit {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 12px;
                font-family: 'Menlo', 'Monaco', monospace;
                font-size: 13px;
                line-height: 1.5;
            }
            QLineEdit {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #8b5cf6;
            }
            QLabel {
                color: #94a3b8;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QCheckBox {
                color: #cbd5e1;
                font-weight: bold;
            }
        """)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #334155; border-radius: 4px; } QTabBar::tab { background: #1e293b; color: #94a3b8; padding: 8px 16px; border: 1px solid #334155; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; } QTabBar::tab:selected { background: #0f172a; color: #f8fafc; font-weight: bold; }")
        main_layout.addWidget(self.tabs)
        
        # Tab 1: Chat
        self.tab_chat = QWidget()
        layout = QVBoxLayout(self.tab_chat)
        self.tabs.addTab(self.tab_chat, "💬 Chat & Controls")
        
        # Tab 2: Memory Viewer
        self.tab_memory = QWidget()
        mem_layout = QVBoxLayout(self.tab_memory)
        self.tabs.addTab(self.tab_memory, "🧠 Memory Viewer")
        
        self.btn_refresh_memory = QPushButton("🔄 Refresh Memory")
        self.btn_refresh_memory.setStyleSheet("background-color: #3b82f6; color: white; padding: 8px; font-weight: bold; border-radius: 4px;")
        self.btn_refresh_memory.clicked.connect(self.refresh_memory)
        mem_layout.addWidget(self.btn_refresh_memory)
        
        self.memory_list = QListWidget()
        self.memory_list.setStyleSheet("background-color: #1e293b; color: #f8fafc; border: 1px solid #334155; border-radius: 8px; padding: 8px; font-size: 13px;")
        mem_layout.addWidget(self.memory_list)
        
        # Tab 3: Goal Tracker
        self.tab_goal = QWidget()
        goal_layout = QVBoxLayout(self.tab_goal)
        self.tabs.addTab(self.tab_goal, "🎯 Goal Tracker")
        
        # Goal Status
        self.goal_status_label = QLabel("Goal Engine: IDLE")
        self.goal_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #8b5cf6;")
        goal_layout.addWidget(self.goal_status_label)
        
        # Goal Plan List
        self.goal_plan_list = QListWidget()
        self.goal_plan_list.setStyleSheet("background-color: #1e293b; color: #f8fafc; border: 1px solid #334155; border-radius: 8px; padding: 8px; font-size: 13px;")
        goal_layout.addWidget(self.goal_plan_list)
        
        # Timer for polling GoalEngine
        self.goal_timer = QTimer(self)
        self.goal_timer.timeout.connect(self.update_goal_ui)
        self.goal_timer.start(1000) # Poll every 1 second
        
        # Status Label
        self.status_label = QLabel("Initializing...")
        layout.addWidget(self.status_label)
        
        # Log view
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Assign a new objective to your agents...")
        self.task_input.returnPressed.connect(self.dispatch_task)
        self.task_input.setStyleSheet("padding: 8px; font-size: 14px;")
        controls_layout.addWidget(self.task_input)
        
        self.dispatch_btn = QPushButton("Dispatch Task")
        self.dispatch_btn.clicked.connect(self.dispatch_task)
        self.dispatch_btn.setStyleSheet("padding: 8px; font-size: 14px;")
        controls_layout.addWidget(self.dispatch_btn)
        
        self.voice_toggle = QCheckBox("🎙️ Always-On Voice (Jarvis)")
        self.voice_toggle.setStyleSheet("color: #8b5cf6; font-size: 14px; font-weight: bold; margin-right: 10px;")
        self.voice_toggle.stateChanged.connect(self.toggle_voice_mode)
        controls_layout.addWidget(self.voice_toggle)
        
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setStyleSheet("background-color: #f59e0b; color: white; padding: 8px; font-size: 14px; font-weight: bold;")
        self.pause_btn.clicked.connect(self.pause_agents)
        controls_layout.addWidget(self.pause_btn)
        
        self.resume_btn = QPushButton("Resume")
        self.resume_btn.setStyleSheet("background-color: #10b981; color: white; padding: 8px; font-size: 14px; font-weight: bold;")
        self.resume_btn.clicked.connect(self.resume_agents)
        controls_layout.addWidget(self.resume_btn)
        
        layout.addLayout(controls_layout)
        
        # Master Objective Control
        master_layout = QHBoxLayout()
        self.master_input = QLineEdit()
        self.master_input.setPlaceholderText("Set Master Objective for Goal Engine...")
        self.master_input.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #8b5cf6;")
        master_layout.addWidget(self.master_input)
        
        self.start_goal_btn = QPushButton("Start Goal")
        self.start_goal_btn.setStyleSheet("background-color: #8b5cf6; color: white; padding: 8px; font-size: 14px; font-weight: bold;")
        self.start_goal_btn.clicked.connect(self.start_master_goal)
        master_layout.addWidget(self.start_goal_btn)
        
        layout.addLayout(master_layout)
        
        # CTA Quick Actions
        cta_layout = QHBoxLayout()
        cta_label = QLabel("Quick Actions:")
        cta_layout.addWidget(cta_label)
        
        self.btn_web = QPushButton("🌐 Web Research")
        self.btn_web.setStyleSheet("background-color: #475569; color: white; padding: 6px; font-size: 13px; border-radius: 4px;")
        self.btn_web.clicked.connect(lambda: self._dispatch_preset("Research the latest top 5 AI news articles on the web and summarize them."))
        cta_layout.addWidget(self.btn_web)
        
        self.btn_sys = QPushButton("💻 System Check")
        self.btn_sys.setStyleSheet("background-color: #475569; color: white; padding: 6px; font-size: 13px; border-radius: 4px;")
        self.btn_sys.clicked.connect(lambda: self._dispatch_preset("Check the current system disk space and CPU memory usage using the terminal."))
        cta_layout.addWidget(self.btn_sys)
        
        self.btn_code = QPushButton("📁 Analyze Codebase")
        self.btn_code.setStyleSheet("background-color: #475569; color: white; padding: 6px; font-size: 13px; border-radius: 4px;")
        self.btn_code.clicked.connect(lambda: self._dispatch_preset("Analyze the directory structure of this project and explain the architecture."))
        cta_layout.addWidget(self.btn_code)
        
        self.btn_music = QPushButton("🎵 YouTube Music")
        self.btn_music.setStyleSheet("background-color: #475569; color: white; padding: 6px; font-size: 13px; border-radius: 4px;")
        self.btn_music.clicked.connect(lambda: self._dispatch_preset("Open Brave browser and play some trending music on YouTube."))
        cta_layout.addWidget(self.btn_music)
        
        layout.addLayout(cta_layout)
        

        # Setup event routing from asyncio to Qt
        self.event_signal.connect(self.on_event_received)
        self.sandbox_app.event_bus.subscribe_all(self._route_event)
        
        self.status_label.setText("System: Connected to Jarvis Core.")
        
        self.voice_listener = ContinuousVoiceListener(
            self.sandbox_app, 
            wake_word="jarvis", 
            status_callback=lambda active: self.voice_status_signal.emit(active)
        )
        self.voice_status_signal.connect(self.on_voice_status_changed)
        
        # Set Voice Mode off by default
        self.voice_toggle.setChecked(False)
        
    async def _route_event(self, event):
        event_dict = {
            "type": event.type.value if hasattr(event.type, "value") else str(event.type),
            "payload": event.payload
        }
        self.event_signal.emit(event_dict)
        
    @pyqtSlot(dict)
    def on_event_received(self, data):
        event_type = data["type"]
        payload = data["payload"]
        
        if event_type == "agent.message":
            agent = payload.get("agent_identity", "System").upper()
            content = payload.get("content", "")
            self.log_view.append(f"<span style='color: #a78bfa;'><b>{agent}:</b></span> {content}<br>")
            
        elif event_type == "tool.request":
            tool_name = payload.get("tool_name", "unknown")
            args = payload.get("arguments", {})
            self.log_view.append(f"<span style='color: #94a3b8;'><i>⚙️ Agent is using tool: <b>{tool_name}</b> {args}...</i></span><br>")
            
        elif event_type == "tool.completed":
            tool_name = payload.get("tool_name", "unknown")
            result = payload.get("result", {})
            self.log_view.append(f"<span style='color: #10b981;'><i>✅ Tool <b>{tool_name}</b> completed.</i></span><br>")
            
            if tool_name == "terminal" and isinstance(result, dict):
                import html
                stdout = result.get("stdout", "")
                stderr = result.get("stderr", "")
                
                if stdout:
                    safe_out = html.escape(str(stdout)).strip()
                    if safe_out:
                        self.log_view.append(f"<div style='background-color: #000; color: #10b981; padding: 10px; font-family: monospace; font-size: 11px; margin-top: 5px; margin-bottom: 5px; border-radius: 4px; white-space: pre-wrap;'>{safe_out}</div>")
                
                if stderr:
                    safe_err = html.escape(str(stderr)).strip()
                    if safe_err:
                        self.log_view.append(f"<div style='background-color: #000; color: #ef4444; padding: 10px; font-family: monospace; font-size: 11px; margin-top: 5px; margin-bottom: 5px; border-radius: 4px; white-space: pre-wrap;'>{safe_err}</div>")

        elif event_type == "tool.failed":
            tool_name = payload.get("tool_name", "unknown")
            error = payload.get("error", "Unknown error")
            import html
            safe_err = html.escape(str(error))
            self.log_view.append(f"<span style='color: #ef4444;'><i>❌ Tool <b>{tool_name}</b> failed: {safe_err}</i></span><br>")
            
        elif event_type == "agent.started":
            agent_id = payload.get("agent_id", "Agent").upper()
            self.log_view.append(f"<span style='color: #f59e0b;'><i>🧠 {agent_id} is thinking...</i></span><br>")
            
        elif event_type == "permission.request":
            req_id = payload.get("request_id")
            perm = payload.get("permission")
            risk = payload.get("risk")
            
            # Show QMessageBox
            msg = QMessageBox(self)
            msg.setWindowTitle("High-Risk Action Approval")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText(f"An agent is attempting a HIGH RISK action.\n\nPermission: {perm}\nRisk Level: {risk}\n\nDo you approve?")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setDefaultButton(QMessageBox.StandardButton.No)
            
            # Use styling
            msg.setStyleSheet("QMessageBox { background-color: #1e293b; color: #f8fafc; } QLabel { color: #f8fafc; } QPushButton { background-color: #3b82f6; color: white; padding: 6px; border-radius: 4px; }")
            
            result = msg.exec()
            
            approved = (result == QMessageBox.StandardButton.Yes)
            
            if hasattr(self.sandbox_app, 'permission_futures') and req_id in self.sandbox_app.permission_futures:
                future = self.sandbox_app.permission_futures.pop(req_id)
                if not future.done():
                    loop = future.get_loop()
                    loop.call_soon_threadsafe(future.set_result, approved)
            
            if approved:
                self.log_view.append(f"<span style='color: #10b981;'><i>🔓 High-risk action APPROVED by user.</i></span><br>")
            else:
                self.log_view.append(f"<span style='color: #ef4444;'><i>🔒 High-risk action DENIED by user.</i></span><br>")
            
        else:
            payload_str = str(payload)
            if len(payload_str) > 120:
                payload_str = payload_str[:120] + "..."
            self.log_view.append(f"<span style='color: #38bdf8;'>{event_type}</span> <span style='color: #888;'>{payload_str}</span>")
            
    def dispatch_task(self):
        text = self.task_input.text().strip()
        if text:
            self.task_input.clear()
            self._dispatch_preset(text)

    def start_master_goal(self):
        text = self.master_input.text().strip()
        if text:
            self.master_input.clear()
            if self.sandbox_app.goal_engine:
                self.sandbox_app.goal_engine.start_goal(text)
                self.log_view.append(f"<span style='color: #8b5cf6; font-weight: bold;'>SYSTEM:</span> Master Goal set: {text}<br>")
                self.tabs.setCurrentWidget(self.tab_goal)
            else:
                self.log_view.append("<span style='color: #ef4444; font-weight: bold;'>ERROR:</span> Goal Engine not initialized.<br>")

    def _dispatch_preset(self, text: str):
        self.log_view.append(f"<span style='color: #38bdf8; font-weight: bold;'>HUMAN (You):</span> {text}<br>")
        asyncio.create_task(self.sandbox_app.conversation_engine.inject_human_message(text))

    def toggle_voice_mode(self, state):
        # 2 corresponds to Qt.CheckState.Checked
        if state == 2:
            self.log_view.append("<span style='color: #8b5cf6; font-weight: bold;'>System: Always-On Voice Enabled. Say 'Jarvis' to command.</span><br>")
            self.voice_listener.start()
        else:
            self.log_view.append("<span style='color: #8b5cf6; font-weight: bold;'>System: Always-On Voice Disabled.</span><br>")
            self.voice_listener.stop()
            
    @pyqtSlot(bool)
    def on_voice_status_changed(self, is_speaking):
        if is_speaking:
            self.voice_toggle.setText("🟢 Jarvis is listening...")
            self.voice_toggle.setStyleSheet("color: #10b981; font-size: 14px; font-weight: bold; margin-right: 10px;")
        else:
            self.voice_toggle.setText("🎙️ Always-On Voice (Jarvis)")
            self.voice_toggle.setStyleSheet("color: #cbd5e1; font-size: 14px; font-weight: bold; margin-right: 10px;")
            
    def pause_agents(self):
        asyncio.create_task(self.sandbox_app.conversation_engine.pause())
        self.log_view.append("<span style='color: #f59e0b; font-weight: bold;'>System: Agents Paused</span>")
        
    def resume_agents(self):
        asyncio.create_task(self.sandbox_app.conversation_engine.resume())
        self.log_view.append("<span style='color: #10b981; font-weight: bold;'>System: Agents Resumed</span>")

    def refresh_memory(self):
        self.memory_list.clear()
        
        # Fetch from vector store if available
        if hasattr(self.sandbox_app, 'memory_manager'):
            import json
            # We can't directly list all vectors easily if it's FAISS/Chroma without a specific API,
            # but we can check the SQLiteStore if available, or just fetch recent context
            async def fetch():
                try:
                    turn = self.sandbox_app.conversation_engine.turn_number
                    ctx = await self.sandbox_app.memory_manager.get_context(turn)
                    return ctx
                except Exception as e:
                    return {"error": str(e)}
            
            future = asyncio.run_coroutine_threadsafe(fetch(), asyncio.get_event_loop())
            try:
                ctx = future.result(timeout=5.0)
                if "error" in ctx:
                    self.memory_list.addItem(f"Error fetching memory: {ctx['error']}")
                else:
                    self.memory_list.addItem("--- Important Facts ---")
                    for fact in ctx.get("important_facts", []):
                        self.memory_list.addItem(f"• {fact}")
                    
                    self.memory_list.addItem("\n--- Open Questions ---")
                    for q in ctx.get("open_questions", []):
                        self.memory_list.addItem(f"• {q}")
                        
                    self.memory_list.addItem("\n--- Current Plan ---")
                    for p in ctx.get("current_plan", []):
                        self.memory_list.addItem(f"• {p}")
            except Exception as e:
                self.memory_list.addItem(f"Timeout fetching memory: {e}")
        else:
            self.memory_list.addItem("Memory Manager not initialized in sandbox_app.")

    def update_goal_ui(self):
        if not hasattr(self.sandbox_app, 'goal_engine') or not self.sandbox_app.goal_engine:
            return
            
        engine = self.sandbox_app.goal_engine
        
        state_colors = {
            GoalState.IDLE: "#94a3b8",
            GoalState.PLANNING: "#3b82f6",
            GoalState.ACTING: "#f59e0b",
            GoalState.CRITIQUING: "#8b5cf6",
            GoalState.DONE: "#10b981",
            GoalState.FAILED: "#ef4444"
        }
        
        color = state_colors.get(engine.state, "#94a3b8")
        status_text = f"Goal Engine: {engine.state.value.upper()}"
        
        if engine.context:
            status_text += f" | Objective: {engine.context.objective}"
            
        self.goal_status_label.setText(status_text)
        self.goal_status_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {color};")
        
        # Update plan list if context exists
        if engine.context and engine.context.plan:
            # Only update if the plan length or current step changed to avoid flicker
            if self.goal_plan_list.count() != len(engine.context.plan) or \
               getattr(self, '_last_goal_step', -1) != engine.context.current_step:
                
                self.goal_plan_list.clear()
                for i, step in enumerate(engine.context.plan):
                    status = " "
                    if i < engine.context.current_step:
                        status = "✅"
                    elif i == engine.context.current_step:
                        status = "▶️"
                    self.goal_plan_list.addItem(f"{status} [{i+1}] {step}")
                
                self._last_goal_step = engine.context.current_step
