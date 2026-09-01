from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.events.bus import EventBus, EventType, get_event_bus

logger = logging.getLogger(__name__)


@dataclass
class StandingJob:
    job_id: str = field(default_factory=lambda: "job_" + str(uuid.uuid4())[:8])
    name: str = "Standing Autonomous Job"
    task_prompt: str = ""
    interval_seconds: int = 900  # Default 15 minutes
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    run_count: int = 0
    last_status: str = "pending"
    last_result_summary: str = ""


class DaemonScheduler:
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        db_path: str = "./data/scheduled_jobs.json"
    ):
        self.event_bus = event_bus or get_event_bus()
        self.db_path = Path(db_path)
        self.jobs: Dict[str, StandingJob] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._load_jobs()

    def _load_jobs(self) -> None:
        if self.db_path.exists():
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        job = StandingJob(**item)
                        self.jobs[job.job_id] = job
            except Exception as e:
                logger.warning(f"Could not load scheduled jobs: {e}")
        
        # Add default recommended standing missions if empty
        if not self.jobs:
            self.add_job(
                name="Telemetry & System Health Check",
                task_prompt="Inspect Mac CPU, RAM, and battery status. If RAM > 85%, log an alert.",
                interval_seconds=900,  # Every 15 mins
                is_active=False
            )
            self.add_job(
                name="Autonomous Research & Gap Discovery",
                task_prompt="Analyze previous research history, discover 1 novel unexplored frontier, synthesize paper and publish to Desktop.",
                interval_seconds=3600,  # Every 1 hr
                is_active=False
            )

    def _save_jobs(self) -> None:
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump([asdict(j) for j in self.jobs.values()], f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save scheduled jobs: {e}")

    def add_job(
        self,
        name: str,
        task_prompt: str,
        interval_seconds: int = 900,
        is_active: bool = True
    ) -> StandingJob:
        job = StandingJob(
            name=name,
            task_prompt=task_prompt,
            interval_seconds=max(interval_seconds, 60),
            is_active=is_active
        )
        self.jobs[job.job_id] = job
        self._save_jobs()
        logger.info(f"Added standing job '{name}' (every {interval_seconds}s, active={is_active})")
        return job

    def toggle_job(self, job_id: str) -> Optional[StandingJob]:
        if job_id in self.jobs:
            job = self.jobs[job_id]
            job.is_active = not job.is_active
            self._save_jobs()
            return job
        return None

    def delete_job(self, job_id: str) -> bool:
        if job_id in self.jobs:
            del self.jobs[job_id]
            self._save_jobs()
            return True
        return False

    def list_jobs(self) -> List[Dict[str, Any]]:
        return [asdict(j) for j in self.jobs.values()]

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("DaemonScheduler background loop started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _scheduler_loop(self) -> None:
        from app.agents.system_controller import get_mac_controller

        while self._running:
            now = time.time()

            for job in list(self.jobs.values()):
                if not job.is_active:
                    continue

                should_run = False
                if not job.last_run_at:
                    should_run = True
                else:
                    try:
                        last_ts = datetime.fromisoformat(job.last_run_at).timestamp()
                        if now - last_ts >= job.interval_seconds:
                            should_run = True
                    except Exception:
                        should_run = True

                if should_run:
                    logger.info(f"Executing standing background job '{job.name}'...")
                    job.last_run_at = datetime.now(timezone.utc).isoformat()
                    job.run_count += 1
                    job.last_status = "running"
                    self._save_jobs()

                    try:
                        controller = get_mac_controller()
                        result = await controller.execute_task(
                            task=job.task_prompt,
                            conversation_id=f"daemon_{job.job_id}",
                            mode="24/7"
                        )
                        job.last_status = "completed" if result.get("success") else "failed"
                        job.last_result_summary = result.get("final_response", "")[:300]
                    except Exception as e:
                        logger.error(f"Error in standing job '{job.name}': {e}")
                        job.last_status = "error"
                        job.last_result_summary = str(e)

                    self._save_jobs()

            await asyncio.sleep(10)  # Check every 10 seconds


_daemon_scheduler: Optional[DaemonScheduler] = None


def get_daemon_scheduler() -> DaemonScheduler:
    global _daemon_scheduler
    if _daemon_scheduler is None:
        _daemon_scheduler = DaemonScheduler()
    return _daemon_scheduler
