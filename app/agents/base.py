from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TraceStep:
    agent: str
    action: str
    detail: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


@dataclass
class AgentTrace:
    steps: list[TraceStep] = field(default_factory=list)

    def log(self, agent: str, action: str, detail: str = "") -> None:
        self.steps.append(TraceStep(agent=agent, action=action, detail=detail))

    def as_list(self) -> list[dict]:
        return [step.__dict__ for step in self.steps]


class BaseAgent:
    name: str = "agent"
    role: str = ""

    def __init__(self, trace: AgentTrace) -> None:
        self.trace = trace

    def _log(self, action: str, detail: str = "") -> None:
        self.trace.log(self.name, action, detail)
