from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, JSON, Column


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AgentProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    source_url: str = Field(unique=True, index=True)
    source_platform: str
    model_detected: str = "unknown"
    framework: str = "unknown"
    capabilities: List[str] = Field(default=[], sa_column=Column(JSON))
    agent_type: str = "unknown"
    risk_level: str = "safe"
    stars: int = 0
    first_seen: datetime = Field(default_factory=_utcnow)
    last_seen: datetime = Field(default_factory=_utcnow)
    raw_description: str = ""
    status: str = "unchecked"
    last_checked: Optional[datetime] = None
    response_time_ms: Optional[int] = None
