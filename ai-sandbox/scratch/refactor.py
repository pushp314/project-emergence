import re
import os

filepath = "/Users/pushp/Desktop/A2A/ai-sandbox/app/evidence/manager.py"
with open(filepath, "r") as f:
    content = f.read()

# 1. Rename _save_evidence to _save_evidence_sync
content = content.replace("def _save_evidence(self, evidence: Evidence) -> None:", "def _save_evidence_sync(self, evidence: Evidence) -> None:")

# 2. Add async wrapper
async_wrapper = """
    async def _save_evidence(self, evidence: Evidence) -> None:
        import asyncio
        await asyncio.to_thread(self._save_evidence_sync, evidence)
"""
content = content.replace("def _save_evidence_sync(self, evidence: Evidence) -> None:", async_wrapper + "\n    def _save_evidence_sync(self, evidence: Evidence) -> None:")

# 3. Add await to all self._save_evidence calls inside async methods
# We only want to replace calls that are currently synchronous.
# Regex to find self._save_evidence(evidence) and prepend await
content = re.sub(r'(\s+)self\._save_evidence\(', r'\1await self._save_evidence(', content)

# 4. Also wrap _create_session_record and _complete_session_record
content = content.replace("def _create_session_record(self, session_id: str) -> None:", "def _create_session_record_sync(self, session_id: str) -> None:")
content = content.replace("def _complete_session_record(self, session_id: str) -> None:", "def _complete_session_record_sync(self, session_id: str) -> None:")

content = content.replace("def _create_session_record_sync", "async def _create_session_record(self, session_id: str) -> None:\n        import asyncio\n        await asyncio.to_thread(self._create_session_record_sync, session_id)\n\n    def _create_session_record_sync", 1)
content = content.replace("def _complete_session_record_sync", "async def _complete_session_record(self, session_id: str) -> None:\n        import asyncio\n        await asyncio.to_thread(self._complete_session_record_sync, session_id)\n\n    def _complete_session_record_sync", 1)

content = re.sub(r'(\s+)self\._create_session_record\(', r'\1await self._create_session_record(', content)
content = re.sub(r'(\s+)self\._complete_session_record\(', r'\1await self._complete_session_record(', content)

# Clean up double awaits if any
content = content.replace("await await", "await")

with open(filepath, "w") as f:
    f.write(content)

print("Refactor complete.")
