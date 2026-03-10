from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, JSON, Column


class AgentProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    source_url: str = Field(unique=True, index=True)
    source_platform: str  # github/huggingface/discord/telegram/honeypot
    model_detected: str = "unknown"  # gpt-4/claude/gemini/llama/unknown
    framework: str = "unknown"  # langchain/crewai/autogen/unknown
    capabilities: List[str] = Field(default=[], sa_column=Column(JSON))
    agent_type: str = "unknown"  # chatbot/task-agent/crawler/multi-agent
    risk_level: str = "safe"  # safe/suspicious/rogue
    stars: int = 0
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    raw_description: str = ""
    status: str = "unchecked"  # online/dead/unknown/redirected/unchecked
    last_checked: Optional[datetime] = None
    response_time_ms: Optional[int] = None
