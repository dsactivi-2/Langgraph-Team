from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class AgentStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_HUMAN = "needs_human"
    REFLECTION = "reflection"


class ArtifactType(StrEnum):
    CODE = "code"
    DOCUMENTATION = "documentation"
    CONFIG = "config"
    TEST = "test"
    DOCKER = "docker"
    K8S = "k8s"


class GeneratedArtifact(BaseModel):
    filename: str
    content: str
    artifact_type: ArtifactType
    description: str | None = None


class TestResult(BaseModel):
    test_name: str
    status: Literal["passed", "failed", "skipped"]
    output: str
    error_message: str | None = None
    execution_time: float = 0.0


class ReviewFeedback(BaseModel):
    category: str
    severity: Literal["low", "medium", "high", "critical"]
    message: str
    suggestion: str | None = None


class VerificationResult(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    category_scores: dict[str, int]
    strengths: list[str]
    weaknesses: list[str]
    improvement_suggestions: list[str]
    recommendation: Literal["approve", "revise", "reject"]


class BuilderState(BaseModel):
    project_id: str = Field(default_factory=lambda: f"project-{uuid4().hex[:10]}")
    user_request: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    plan: str | None = None
    architecture_decisions: list[str] = Field(default_factory=list)

    generated_artifacts: list[GeneratedArtifact] = Field(default_factory=list)
    current_code: str | None = None

    test_results: list[TestResult] = Field(default_factory=list)
    sandbox_logs: list[str] = Field(default_factory=list)

    review_feedback: list[ReviewFeedback] = Field(default_factory=list)
    verification_result: VerificationResult | None = None
    quality_score: int = 0

    used_skills: list[str] = Field(default_factory=list)
    new_skills_proposed: list[dict[str, Any]] = Field(default_factory=list)

    docker_compose: str | None = None
    k8s_manifests: list[str] = Field(default_factory=list)
    deployment_instructions: str | None = None

    current_agent: str = "orchestrator"
    status: AgentStatus = AgentStatus.PENDING
    decision_history: list[dict[str, Any]] = Field(default_factory=list)
    human_approval_points: list[str] = Field(default_factory=list)
    token_usage: dict[str, int] = Field(default_factory=dict)
    reflection_notes: list[str] = Field(default_factory=list)

    final_summary: str | None = None
    recommended_next_steps: list[str] = Field(default_factory=list)

    def touch(self) -> "BuilderState":
        self.updated_at = datetime.now(UTC)
        return self


class BuildRequest(BaseModel):
    user_request: str = Field(..., min_length=3, max_length=10_000)
    project_id: str | None = Field(default=None, min_length=1, max_length=120)


class ChatMessageRequest(BaseModel):
    project_id: str = Field(..., min_length=1, max_length=120)
    role: Literal["user", "assistant", "system"] = "user"
    content: str = Field(..., min_length=1, max_length=20_000)


class MemoryUpsertRequest(BaseModel):
    project_id: str = Field(..., min_length=1, max_length=120)
    text: str = Field(..., min_length=1, max_length=20_000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemorySearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2_000)
    project_id: str | None = Field(default=None, min_length=1, max_length=120)
    limit: int = Field(default=5, ge=1, le=20)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class LLMCompletionRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=20_000)
    system: str | None = Field(default=None, max_length=5_000)


class BuildResponse(BaseModel):
    project_id: str
    status: AgentStatus
    quality_score: int
    plan: str | None
    artifacts: list[GeneratedArtifact]
    review_feedback: list[ReviewFeedback]
    verification_result: VerificationResult | None
    deployment_instructions: str | None
