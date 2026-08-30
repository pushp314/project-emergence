import sys

with open("app/desktop/main_window.py", "r") as f:
    content = f.read()

old_block = """        elif event_type == "agent.started":
            agent_id = payload.get("agent_id", "Agent").upper()
            self.log_view.append(f"<span style='color: #f59e0b;'><i>🧠 {agent_id} is thinking...</i></span><br>")
            
        else:
            payload_str = str(payload)"""

new_block = """        elif event_type == "agent.started":
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
            msg.setText(f"An agent is attempting a HIGH RISK action.\\n\\nPermission: {perm}\\nRisk Level: {risk}\\n\\nDo you approve?")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setDefaultButton(QMessageBox.StandardButton.No)
            
            # Use styling
            msg.setStyleSheet("QMessageBox { background-color: #1e293b; color: #f8fafc; } QLabel { color: #f8fafc; } QPushButton { background-color: #3b82f6; color: white; padding: 6px; border-radius: 4px; }")
            
            result = msg.exec()
            
            approved = (result == QMessageBox.StandardButton.Yes)
            
            if hasattr(self.sandbox_app, 'permission_futures') and req_id in self.sandbox_app.permission_futures:
                future = self.sandbox_app.permission_futures.pop(req_id)
                if not future.done():
                    future.set_result(approved)
            
            if approved:
                self.log_view.append(f"<span style='color: #10b981;'><i>🔓 High-risk action APPROVED by user.</i></span><br>")
            else:
                self.log_view.append(f"<span style='color: #ef4444;'><i>🔒 High-risk action DENIED by user.</i></span><br>")
            
        else:
            payload_str = str(payload)"""

content = content.replace(old_block, new_block)

with open("app/desktop/main_window.py", "w") as f:
    f.write(content)
