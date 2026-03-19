"""Export all agents from agent_hunter.db to agents_data.json and stats_data.json."""
import json
import sqlite3
from collections import Counter

conn = sqlite3.connect('agent_hunter.db')
conn.row_factory = sqlite3.Row
agents = [dict(r) for r in conn.execute('SELECT * FROM agentprofile').fetchall()]
for a in agents:
    if isinstance(a.get('capabilities'), str):
        try:
            a['capabilities'] = json.loads(a['capabilities'])
        except Exception:
            a['capabilities'] = []
conn.close()

with open('agents_data.json', 'w') as f:
    json.dump(agents, f)

models = Counter(a.get('model_detected', 'unknown') for a in agents)
frameworks = Counter(a.get('framework', 'unknown') for a in agents)
types = Counter(a.get('agent_type', 'unknown') for a in agents)
stats = {'models': dict(models), 'frameworks': dict(frameworks), 'agent_types': dict(types)}

with open('stats_data.json', 'w') as f:
    json.dump(stats, f)

print(f'Exported {len(agents)} total agents to agents_data.json')
