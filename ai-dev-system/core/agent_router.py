from __future__ import annotations

from agents.architecture_agent import ArchitectureAgent
from agents.coder_agent import CoderAgent
from agents.debugger_agent import DebuggerAgent
from agents.fix_agent import FixAgent
from agents.planner_agent import PlannerAgent
from agents.reflection_agent import ReflectionAgent


class AgentRouter:
    def __init__(self) -> None:
        self.planner = PlannerAgent()
        self.architect = ArchitectureAgent()
        self.coder = CoderAgent()
        self.debugger = DebuggerAgent()
        self.fixer = FixAgent()
        self.reflection = ReflectionAgent()
