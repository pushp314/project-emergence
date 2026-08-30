from __future__ import annotations

import asyncio
import logging
import os
import pathlib
from typing import Any, Dict, List, Optional

from app.tools.gateway import Tool
from app.events.schemas import PermissionLevel, RiskLevel

logger = logging.getLogger(__name__)


class FilesystemTool(Tool):
    def __init__(
        self,
        base_path: Optional[str] = None,
        max_file_size: int = 10 * 1024 * 1024,
        allowed_extensions: Optional[List[str]] = None,
        blocked_paths: Optional[List[str]] = None
    ):
        self._base_path = pathlib.Path(base_path or os.getcwd()).resolve()
        self._max_file_size = max_file_size
        self._allowed_extensions = allowed_extensions or [
            ".txt", ".md", ".py", ".js", ".ts", ".json", ".yaml", ".yml",
            ".html", ".css", ".sql", ".sh", ".csv", ".log", ".xml", ".toml"
        ]
        self._blocked_paths = blocked_paths if blocked_paths is not None else [
            "/etc", "/var", "/usr", "/bin", "/sbin", "/boot", "/sys", "/proc",
            "/root", "/home/*/.ssh", "/home/*/.gnupg"
        ]
    
    @property
    def name(self) -> str:
        return "filesystem"
    
    @property
    def description(self) -> str:
        return "Read, write, list, and manipulate files in the filesystem."
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["read", "write", "append", "list", "exists", "delete", "mkdir", "copy", "move"],
                    "description": "Operation to perform"
                },
                "path": {
                    "type": "string",
                    "description": "File or directory path (relative to base path)"
                },
                "content": {
                    "type": "string",
                    "description": "Content for write/append operations"
                },
                "destination": {
                    "type": "string",
                    "description": "Destination path for copy/move operations"
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Recursive operation for list/delete",
                    "default": False
                }
            },
            "required": ["operation", "path"]
        }
    
    @property
    def permission(self) -> PermissionLevel:
        return PermissionLevel.WRITE
    
    @property
    def risk(self) -> RiskLevel:
        return RiskLevel.MEDIUM
    
    @property
    def enabled(self) -> bool:
        return True
    
    def _resolve_path(self, path: str) -> pathlib.Path:
        target = (self._base_path / path).resolve()
        
        try:
            target.relative_to(self._base_path)
        except ValueError:
            raise PermissionError(f"Path '{path}' is outside base directory")
        
        # Blocked paths check - applies to ALL paths, even those inside base_path
        for blocked in self._blocked_paths:
            try:
                blocked_resolved = pathlib.Path(blocked).resolve()
                if target.is_relative_to(blocked_resolved):
                    raise PermissionError(f"Path '{path}' is in blocked directory: {blocked}")
            except ValueError:
                pass
        
        return target
    
    def _check_extension(self, path: pathlib.Path) -> bool:
        if path.is_dir():
            return True
        return path.suffix.lower() in self._allowed_extensions
    
    async def execute(self, arguments: Dict[str, Any]) -> Any:
        operation = arguments.get("operation", "").lower()
        path = arguments.get("path", "")
        
        if not operation or not path:
            return {"error": "Missing operation or path"}
        
        try:
            target = self._resolve_path(path)
        except PermissionError as e:
            return {"error": str(e)}
        
        if operation == "read":
            return await self._read(target)
        elif operation == "write":
            content = arguments.get("content", "")
            return await self._write(target, content)
        elif operation == "append":
            content = arguments.get("content", "")
            return await self._append(target, content)
        elif operation == "list":
            recursive = arguments.get("recursive", False)
            return await self._list(target, recursive)
        elif operation == "exists":
            return await self._exists(target)
        elif operation == "delete":
            recursive = arguments.get("recursive", False)
            return await self._delete(target, recursive)
        elif operation == "mkdir":
            return await self._mkdir(target)
        elif operation == "copy":
            destination = arguments.get("destination", "")
            if not destination:
                return {"error": "Missing destination for copy"}
            return await self._copy(target, self._resolve_path(destination))
        elif operation == "move":
            destination = arguments.get("destination", "")
            if not destination:
                return {"error": "Missing destination for move"}
            return await self._move(target, self._resolve_path(destination))
        else:
            return {"error": f"Unknown operation: {operation}"}
    
    async def _read(self, path: pathlib.Path) -> Dict[str, Any]:
        if not path.exists():
            return {"error": "File not found", "content": ""}
        
        if not self._check_extension(path):
            return {"error": f"File type not allowed: {path.suffix}", "content": ""}
        
        if path.stat().st_size > self._max_file_size:
            return {"error": f"File too large (max {self._max_file_size} bytes)", "content": ""}
        
        try:
            content = path.read_text(encoding="utf-8")
            return {"content": content, "size": len(content), "path": str(path)}
        except UnicodeDecodeError:
            return {"error": "File is not valid UTF-8 text", "content": ""}
        except Exception as e:
            return {"error": str(e), "content": ""}
    
    async def _write(self, path: pathlib.Path, content: str) -> Dict[str, Any]:
        if not self._check_extension(path):
            return {"error": f"File type not allowed: {path.suffix}"}
        
        if len(content.encode("utf-8")) > self._max_file_size:
            return {"error": f"Content too large (max {self._max_file_size} bytes)"}
        
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return {"success": True, "path": str(path), "size": len(content)}
        except Exception as e:
            return {"error": str(e)}
    
    async def _append(self, path: pathlib.Path, content: str) -> Dict[str, Any]:
        if not self._check_extension(path):
            return {"error": f"File type not allowed: {path.suffix}"}
        
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "path": str(path), "appended": len(content)}
        except Exception as e:
            return {"error": str(e)}
    
    async def _list(self, path: pathlib.Path, recursive: bool) -> Dict[str, Any]:
        if not path.exists():
            return {"error": "Path not found", "entries": []}
        
        if not path.is_dir():
            return {"error": "Not a directory", "entries": []}
        
        try:
            if recursive:
                entries = []
                for p in path.rglob("*"):
                    try:
                        rel = p.relative_to(path)
                        entries.append({
                            "name": str(rel),
                            "type": "directory" if p.is_dir() else "file",
                            "size": p.stat().st_size if p.is_file() else 0
                        })
                    except Exception:
                        continue
            else:
                entries = []
                for p in path.iterdir():
                    entries.append({
                        "name": p.name,
                        "type": "directory" if p.is_dir() else "file",
                        "size": p.stat().st_size if p.is_file() else 0
                    })
            
            return {"entries": sorted(entries, key=lambda x: (x["type"], x["name"]))}
        except Exception as e:
            return {"error": str(e), "entries": []}
    
    async def _exists(self, path: pathlib.Path) -> Dict[str, Any]:
        return {"exists": path.exists(), "path": str(path)}
    
    async def _delete(self, path: pathlib.Path, recursive: bool) -> Dict[str, Any]:
        if not path.exists():
            return {"error": "Path not found"}
        
        try:
            if path.is_dir():
                if recursive:
                    import shutil
                    shutil.rmtree(path)
                else:
                    path.rmdir()
            else:
                path.unlink()
            return {"success": True, "path": str(path)}
        except Exception as e:
            return {"error": str(e)}
    
    async def _mkdir(self, path: pathlib.Path) -> Dict[str, Any]:
        try:
            path.mkdir(parents=True, exist_ok=True)
            return {"success": True, "path": str(path)}
        except Exception as e:
            return {"error": str(e)}
    
    async def _copy(self, src: pathlib.Path, dst: pathlib.Path) -> Dict[str, Any]:
        if not src.exists():
            return {"error": "Source not found"}
        
        try:
            import shutil
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            return {"success": True, "source": str(src), "destination": str(dst)}
        except Exception as e:
            return {"error": str(e)}
    
    async def _move(self, src: pathlib.Path, dst: pathlib.Path) -> Dict[str, Any]:
        if not src.exists():
            return {"error": "Source not found"}
        
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)
            return {"success": True, "source": str(src), "destination": str(dst)}
        except Exception as e:
            return {"error": str(e)}