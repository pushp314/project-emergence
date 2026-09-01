from typing import Any, Dict
import os
import sys
import importlib
from app.events.schemas import PermissionLevel, RiskLevel
from app.tools.gateway import Tool, get_tool_gateway

class CreateToolTool(Tool):
    @property
    def name(self) -> str:
        return "create_tool"
    
    @property
    def description(self) -> str:
        return "Write Python code to dynamically create and register a new tool for yourself. Your code must define a class that inherits from `Tool` and you must instantiate it as `TOOL_INSTANCE` at the module level. DO NOT attempt to register it yourself."
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "The internal name of the tool (must match the .name property of your class)"
                },
                "code": {
                    "type": "string",
                    "description": "The complete Python code for the tool. Must import `Tool` from `app.tools.gateway`. Must assign an instance of your class to `TOOL_INSTANCE`."
                }
            },
            "required": ["tool_name", "code"]
        }
    
    @property
    def permission(self) -> PermissionLevel:
        return PermissionLevel.SYSTEM
    
    @property
    def risk(self) -> RiskLevel:
        return RiskLevel.HIGH
    
    @property
    def enabled(self) -> bool:
        return True
    
    async def execute(self, arguments: Dict[str, Any]) -> Any:
        tool_name = arguments["tool_name"]
        code = arguments["code"]
        
        import ast
        
        # Security validation (basic)
        if not tool_name.isidentifier():
            return "Error: tool_name must be a valid Python identifier"
            
        # AST parsing to check for dangerous imports
        dangerous_modules = {"os", "sys", "subprocess", "pty", "shutil", "socket"}
        found_dangerous = set()
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] in dangerous_modules:
                            found_dangerous.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split(".")[0] in dangerous_modules:
                        found_dangerous.add(node.module)
        except SyntaxError as e:
            return f"Syntax Error in provided code: {e}"
            
        if found_dangerous:
            from app.permissions.manager import get_permission_manager
            from app.events.schemas import RiskLevel, PermissionLevel
            pm = get_permission_manager()
            
            conv_id = arguments.get("_conversation_id", "operator")
            approved = await pm.request_permission(
                agent_id=conv_id,
                action="create_tool",
                command=f"Inject Dynamic Tool: {tool_name}",
                reason=f"The agent is attempting to inject a new tool '{tool_name}' that uses dangerous modules: {', '.join(found_dangerous)}. \nCode:\n{code[:300]}...",
                risk=RiskLevel.HIGH,
                scope=PermissionLevel.SYSTEM,
                timeout=300
            )
            
            if not approved:
                return f"Security Error: User denied permission to create tool '{tool_name}' due to dangerous imports."
            
        file_path = f"app/tools/dynamic/{tool_name}.py"
        os.makedirs("app/tools/dynamic", exist_ok=True)
        with open(file_path, "w") as f:
            f.write(code)
            
        try:
            # Dynamically import the module
            module_name = f"app.tools.dynamic.{tool_name}"
            
            if module_name in sys.modules:
                module = importlib.reload(sys.modules[module_name])
            else:
                module = importlib.import_module(module_name)
                
            if not hasattr(module, "TOOL_INSTANCE"):
                return f"Error: The code did not define TOOL_INSTANCE."
                
            new_tool = getattr(module, "TOOL_INSTANCE")
            if not isinstance(new_tool, Tool):
                return f"Error: TOOL_INSTANCE must inherit from Tool."
                
            gateway = get_tool_gateway()
            gateway.register(new_tool)
            
            return f"Successfully created and registered dynamic tool: {new_tool.name}"
        except Exception as e:
            return f"Error compiling or registering tool: {str(e)}"
