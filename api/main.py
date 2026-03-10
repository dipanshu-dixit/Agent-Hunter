from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, create_engine, Session, select, func
from typing import List, Optional, Dict
from models.agent_profile import AgentProfile

DATABASE_URL = "sqlite:///agent_hunter.db"
engine = create_engine(DATABASE_URL, echo=False)

app = FastAPI(title="Agent Hunter API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_session():
    with Session(engine) as session:
        yield session

@app.on_event("startup")
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/agents", response_model=List[AgentProfile])
def list_agents(
    model: Optional[str] = Query(None),
    framework: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    session: Session = Depends(get_session)
):
    query = select(AgentProfile)
    
    if model:
        query = query.where(AgentProfile.model_detected == model)
    if framework:
        query = query.where(AgentProfile.framework == framework)
    
    query = query.limit(limit)
    return session.exec(query).all()

@app.get("/agents/{agent_id}", response_model=AgentProfile)
def get_agent(agent_id: int, session: Session = Depends(get_session)):
    agent = session.get(AgentProfile, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@app.get("/stats")
def get_stats(session: Session = Depends(get_session)):
    model_counts = session.exec(
        select(AgentProfile.model_detected, func.count()).group_by(AgentProfile.model_detected)
    ).all()
    
    framework_counts = session.exec(
        select(AgentProfile.framework, func.count()).group_by(AgentProfile.framework)
    ).all()
    
    type_counts = session.exec(
        select(AgentProfile.agent_type, func.count()).group_by(AgentProfile.agent_type)
    ).all()
    
    return {
        "models": dict(model_counts),
        "frameworks": dict(framework_counts),
        "agent_types": dict(type_counts)
    }

@app.post("/agents", response_model=AgentProfile)
def upsert_agent(agent_data: Dict, session: Session = Depends(get_session)):
    existing = session.exec(
        select(AgentProfile).where(AgentProfile.source_url == agent_data["source_url"])
    ).first()
    
    if existing:
        for key, value in agent_data.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
        agent = existing
    else:
        agent = AgentProfile(**agent_data)
        session.add(agent)
    
    session.commit()
    session.refresh(agent)
    return agent

@app.patch("/agents/{agent_id}", response_model=AgentProfile)
def update_agent(agent_id: int, update_data: Dict, session: Session = Depends(get_session)):
    agent = session.get(AgentProfile, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    for key, value in update_data.items():
        if hasattr(agent, key):
            setattr(agent, key, value)
    
    session.commit()
    session.refresh(agent)
    return agent

@app.get("/agents/dead", response_model=List[AgentProfile])
def get_dead_agents(session: Session = Depends(get_session)):
    return session.exec(select(AgentProfile).where(AgentProfile.status == "dead")).all()

@app.get("/agents/online", response_model=List[AgentProfile])
def get_online_agents(session: Session = Depends(get_session)):
    return session.exec(select(AgentProfile).where(AgentProfile.status == "online")).all()