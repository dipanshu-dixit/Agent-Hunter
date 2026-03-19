"""
Restore previous agents from agents_data.json into a fresh agent_hunter.db.
Run this BEFORE starting the API server on each GitHub Actions run.
This is what makes the database accumulate across runs instead of resetting.
"""

import json
import os
import sys
from datetime import datetime
from sqlmodel import SQLModel, create_engine, Session, select
from models.agent_profile import AgentProfile

SNAPSHOT_FILE = "agents_data.json"
DATABASE_URL = "sqlite:///agent_hunter.db"

VALID_FIELDS = set(AgentProfile.model_fields.keys())


def parse_datetime(value):
    if not value:
        return datetime.utcnow()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00").replace("+00:00", ""))
    except Exception:
        return datetime.utcnow()


def restore():
    if not os.path.exists(SNAPSHOT_FILE):
        print("No agents_data.json found — starting fresh (first run).")
        return

    with open(SNAPSHOT_FILE) as f:
        agents = json.load(f)

    if not isinstance(agents, list) or len(agents) == 0:
        print("Snapshot is empty — starting fresh.")
        return

    engine = create_engine(DATABASE_URL, echo=False)
    SQLModel.metadata.create_all(engine)

    restored = 0
    skipped = 0

    with Session(engine) as session:
        # Build a set of existing URLs to avoid unique constraint errors
        existing_urls = {
            row for row in session.exec(
                __import__("sqlmodel").select(AgentProfile.source_url)
            )
        }

        for a in agents:
            url = a.get("source_url", "")
            if not url or url in existing_urls:
                skipped += 1
                continue

            # Only pass fields that exist on the model, coerce datetime strings
            clean = {}
            for k, v in a.items():
                if k not in VALID_FIELDS:
                    continue
                if k in ("first_seen", "last_seen", "last_checked") and isinstance(v, str):
                    clean[k] = parse_datetime(v)
                else:
                    clean[k] = v

            try:
                session.add(AgentProfile(**clean))
                existing_urls.add(url)
                restored += 1
            except Exception as e:
                print(f"  ⚠️ Skipped {a.get('name', '?')}: {e}")
                skipped += 1

        session.commit()

    print(f"✅ Restored {restored} agents from snapshot ({skipped} already present or invalid).")
    print(f"   DB is ready — scanner will only add genuinely new agents.")


if __name__ == "__main__":
    restore()
