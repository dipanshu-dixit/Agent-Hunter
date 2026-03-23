from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ScanState(SQLModel, table=True):
    topic: str = Field(primary_key=True)
    platform: str = "github"
    last_page: int = 0
    total_found: int = 0
    exhausted: bool = False
    last_updated: datetime = Field(default_factory=_utcnow)