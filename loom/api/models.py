from typing import Any, Literal

from pydantic import BaseModel, Field


class JobRequest(BaseModel):
    target_name: str
    params: dict[str, Any] = Field(default_factory=dict)


class JobAccepted(BaseModel):
    job_id: str
    spider: str


class JobStatus(BaseModel):
    job_id: str
    status: Literal["pending", "running", "finished", "failed", "unknown"]


class JobResult(BaseModel):
    job_id: str
    items: list[dict[str, Any]]
