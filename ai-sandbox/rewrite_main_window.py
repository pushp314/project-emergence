import sys

with open("app/desktop/main_window.py", "r") as f:
    content = f.read()

# Replace imports
content = content.replace(
    "QTextEdit, QPushButton, QLineEdit, QLabel, QCheckBox",
    "QTextEdit, QPushButton, QLineEdit, QLabel, QCheckBox,\n    QTabWidget, QListWidget, QMessageBox"
)

# Replace central widget setup
old_setup = """        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Status Label"""

new_setup = """        # Central widget
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
        
        # Status Label"""

content = content.replace(old_setup, new_setup)

# Add refresh_memory method
refresh_method = """
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
                    
                    self.memory_list.addItem("\\n--- Open Questions ---")
                    for q in ctx.get("open_questions", []):
                        self.memory_list.addItem(f"• {q}")
                        
                    self.memory_list.addItem("\\n--- Current Plan ---")
                    for p in ctx.get("current_plan", []):
                        self.memory_list.addItem(f"• {p}")
            except Exception as e:
                self.memory_list.addItem(f"Timeout fetching memory: {e}")
        else:
            self.memory_list.addItem("Memory Manager not initialized in sandbox_app.")
"""

if "def refresh_memory(" not in content:
    content += refresh_method

with open("app/desktop/main_window.py", "w") as f:
    f.write(content)
