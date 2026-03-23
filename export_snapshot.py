"""Export all agents from agent_hunter.db to agents_data.json and stats_data.json."""
import json
import sqlite3
import os
from collections import Counter

DB_PATH = os.getenv('DATABASE_PATH', 'agent_hunter.db')

with sqlite3.connect(DB_PATH) as conn:
    conn.row_factory = sqlite3.Row
    agents = [dict(r) for r in conn.execute('SELECT * FROM agentprofile').fetchall()]

for a in agents:
    if isinstance(a.get('capabilities'), str):
        try:
            a['capabilities'] = json.loads(a['capabilities'])
        except (json.JSONDecodeError, ValueError):
            a['capabilities'] = []

with open('agents_data.json', 'w') as f:
    json.dump(agents, f)

models = Counter(a.get('model_detected', 'unknown') for a in agents)
frameworks = Counter(a.get('framework', 'unknown') for a in agents)
types = Counter(a.get('agent_type', 'unknown') for a in agents)
stats = {'models': dict(models), 'frameworks': dict(frameworks), 'agent_types': dict(types)}

with open('stats_data.json', 'w') as f:
    json.dump(stats, f)

print(f'Exported {len(agents)} total agents to agents_data.json')
