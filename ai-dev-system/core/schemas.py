from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    queued = "queued"
    running = "running"
    success = "success"
    failed = "failed"


class FileChange(BaseModel):
    path: str
    content: str


class AgentPlan(BaseModel):
    goal: str = ""
    steps: list[str] = Field(default_factory=list)
    architecture: dict[str, list[str]] = Field(default_factory=dict)
    risks: list[str] = Field(default_factory=list)
    validation_plan: list[str] = Field(default_factory=list)


class CodeProposal(BaseModel):
    summary: str = ""
    changes: list[FileChange] = Field(default_factory=list)
    tests: list[str] = Field(default_factory=list)


class DebugReport(BaseModel):
    root_cause: str = ""
    evidence: list[str] = Field(default_factory=list)
    fix_plan: list[str] = Field(default_factory=list)
    regression_risk: str = "medium"


class RunRecord(BaseModel):
    run_id: str
    status: RunStatus
    task: str
    logs: list[str] = Field(default_factory=list)
    changed_files: list[str] = Field(default_factory=list)
    plan: AgentPlan | None = None
    architecture: dict[str, list[str]] = Field(default_factory=dict)
    attempts: int = 0
    last_error: str = ""
