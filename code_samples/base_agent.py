"""
Sanitized excerpt: the base class every agent inherits from.

Illustrates the asynchronous mission-queue pattern that decouples all agents.
Agents never call each other; they only claim missions and write results.
No credentials or provider-specific code included.
"""
from __future__ import annotations

import abc
import asyncio


class MissionStatus:
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"       # <- agent finished; a HUMAN promotes to completed
    FAILED = "failed"


class BaseAgent(abc.ABC):
    """Poll -> claim -> execute -> review. One job per subclass."""

    POLL_INTERVAL_S = 30

    def __init__(self, agent_type: str, agent_rank: str):
        self.agent_type = agent_type
        self.agent_rank = agent_rank
        # An agent may also answer to legacy/alias types for compatibility.
        self.alias_agent_types: list[str] = []

    async def run(self) -> None:
        """Long-lived loop. Safe to kill and restart: state lives in the DB."""
        while True:
            mission = await self._claim_next_mission()
            if mission is None:
                await asyncio.sleep(self.POLL_INTERVAL_S)
                continue
            await self._handle_mission(mission)

    async def _handle_mission(self, mission: dict) -> None:
        try:
            summary = await self.execute(mission)
            # Deliberately NOT 'completed'. The machine proposes; a human
            # reviews consequential output before it takes effect.
            await self._set_status(mission, MissionStatus.REVIEW, summary)
        except Exception as exc:  # noqa: BLE001 - agents must never crash the fleet
            await self._set_status(mission, MissionStatus.FAILED, str(exc))
            await self._log(mission, level="ERROR", message=str(exc))

    @abc.abstractmethod
    async def execute(self, mission: dict) -> str:
        """Each agent implements its single job here and returns a summary."""
        raise NotImplementedError

    # --- infra methods (claim/status/log) talk to Postgres; omitted here ---
    async def _claim_next_mission(self) -> dict | None: ...
    async def _set_status(self, mission: dict, status: str, summary: str) -> None: ...
    async def _log(self, mission: dict, level: str, message: str) -> None: ...
