import sys

with open("app/main.py", "r") as f:
    content = f.read()

old_checker = """        async def permission_checker(agent_id: str, perm: PermissionLevel, risk: RiskLevel) -> bool:
            # User requested an autonomous agent, auto-approve all actions
            return True"""

new_checker = """        async def permission_checker(agent_id: str, perm: PermissionLevel, risk: RiskLevel) -> bool:
            if risk in (RiskLevel.HIGH, RiskLevel.CRITICAL) or perm == PermissionLevel.SYSTEM:
                future = asyncio.get_event_loop().create_future()
                req_id = str(uuid.uuid4())
                
                if not hasattr(self, 'permission_futures'):
                    self.permission_futures = {}
                self.permission_futures[req_id] = future
                
                await self.event_bus.publish_type(
                    EventType.PERMISSION_REQUEST,
                    agent_id,
                    {
                        "request_id": req_id,
                        "permission": perm.value,
                        "risk": risk.value
                    }
                )
                
                try:
                    return await asyncio.wait_for(future, timeout=300.0)
                except asyncio.TimeoutError:
                    return False
            return True"""

content = content.replace(old_checker, new_checker)

with open("app/main.py", "w") as f:
    f.write(content)
