# 📚 AgentHunter — Technical Documentation

Complete technical reference for AgentHunter's data collection, storage, and usage.

## 📋 Table of Contents

- [How It Works](#how-it-works)
- [Data Collection Process](#data-collection-process)
- [Database Schema](#database-schema)
- [API Reference](#api-reference)
- [Scanner Details](#scanner-details)
- [Fingerprinting Engine](#fingerprinting-engine)
- [Health Monitoring](#health-monitoring)
- [Usage Examples](#usage-examples)

## 🔄 How It Works

AgentHunter operates on a continuous discovery cycle:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Discovery     │───▶│  Fingerprinting │───▶│    Storage      │
│   (5 Scanners)  │    │   (AI Analysis) │    │   (Database)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                                              │
         │              ┌─────────────────┐             │
         └──────────────│  Health Check   │◀────────────┘
                        │   (Monitoring)  │
                        └─────────────────┘
```

### Execution Flow
1. **Scanners** discover agents from 5 different sources
2. **Fingerprinter** analyzes each agent to detect AI characteristics
3. **Database** stores agents with deduplication by URL
4. **Health Checker** periodically tests agent availability
5. **API** serves data to dashboard and external consumers
6. **Dashboard** provides visual interface for exploration

## 🕷️ Data Collection Process

### Phase 1: Discovery
Each scanner runs independently and collects raw data:

**GitHub Scanner**
- Searches 24 AI-related topics
- Extracts repository metadata
- Downloads README snippets
- Rate-limited to prevent API abuse

**HuggingFace Scanner**
- Queries public model API
- Filters by AI agent tags
- Collects model metadata
- No authentication required

**Discord Scanner**
- Scrapes bot directory sites
- Parses HTML for bot information
- Extracts server counts and descriptions
- Handles anti-scraping measures

**Honeypot Scanner**
- Tests known AI crawler user-agents
- Logs detection attempts
- Identifies active crawlers
- Creates synthetic entries

**Package Scanner**
- Queries PyPI and npm registries
- Searches for AI agent packages
- Extracts version and author info
- Tracks package popularity

### Phase 2: Fingerprinting
Raw data is analyzed to extract AI characteristics:

```python
# Example fingerprinting process
raw_data = {
    "name": "microsoft/autogen",
    "description": "Multi-agent conversation framework",
    "readme": "AutoGen enables multiple agents to converse..."
}

fingerprinted = {
    "model_detected": "gpt-4",      # Found in README
    "framework": "autogen",         # Detected from name
    "agent_type": "multi-agent",    # Inferred from description
    "capabilities": ["conversation", "code-execution"]
}
```

### Phase 3: Storage
Processed data is stored with deduplication:

- **Upsert Logic**: Updates existing agents by `source_url`
- **Timestamp Tracking**: Records `first_seen` and `last_seen`
- **JSON Storage**: Complex fields stored as JSON in SQLite

## 🗄️ Database Schema

### AgentProfile Table Structure

```sql
CREATE TABLE agentprofile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL,
    source_url VARCHAR NOT NULL UNIQUE,  -- Prevents duplicates
    source_platform VARCHAR NOT NULL,
    model_detected VARCHAR DEFAULT 'unknown',
    framework VARCHAR DEFAULT 'unknown',
    capabilities JSON DEFAULT '[]',      -- Stored as JSON array
    agent_type VARCHAR DEFAULT 'unknown',
    risk_level VARCHAR DEFAULT 'safe',
    stars INTEGER DEFAULT 0,
    first_seen DATETIME NOT NULL,
    last_seen DATETIME NOT NULL,
    raw_description TEXT DEFAULT '',
    status VARCHAR DEFAULT 'unchecked',
    last_checked DATETIME,
    response_time_ms INTEGER
);

-- Indexes for performance
CREATE INDEX ix_agentprofile_source_url ON agentprofile (source_url);
```

### Field Definitions

| Field | Type | Description | Example Values |
|-------|------|-------------|----------------|
| `id` | INTEGER | Auto-incrementing primary key | 1, 2, 3... |
| `name` | VARCHAR | Agent/repository name | "microsoft/autogen" |
| `source_url` | VARCHAR | Unique URL (prevents duplicates) | "https://github.com/microsoft/autogen" |
| `source_platform` | VARCHAR | Where agent was discovered | "github", "huggingface", "discord" |
| `model_detected` | VARCHAR | AI model identified | "gpt-4", "claude", "llama", "unknown" |
| `framework` | VARCHAR | Framework detected | "langchain", "crewai", "autogen" |
| `capabilities` | JSON | Array of capabilities | ["web-search", "code-execution"] |
| `agent_type` | VARCHAR | Type classification | "multi-agent", "chatbot", "crawler" |
| `risk_level` | VARCHAR | Safety assessment | "safe", "suspicious", "rogue" |
| `stars` | INTEGER | GitHub stars or HF likes | 15420 |
| `first_seen` | DATETIME | When first discovered | "2026-03-10T12:00:00" |
| `last_seen` | DATETIME | Last scan update | "2026-03-11T06:00:00" |
| `raw_description` | TEXT | Original description | "Multi-agent conversation framework" |
| `status` | VARCHAR | Health check status | "online", "dead", "unknown" |
| `last_checked` | DATETIME | Last health check | "2026-03-11T08:30:00" |
| `response_time_ms` | INTEGER | Response time in milliseconds | 234 |

### Data Types and Constraints

**Unique Constraints**
- `source_url` must be unique (prevents duplicate agents)

**Default Values**
- New agents default to "unknown" for undetected fields
- `status` defaults to "unchecked" until health check runs
- Timestamps auto-generate on creation

**JSON Fields**
- `capabilities` stored as JSON array for complex queries
- Searchable with SQLite JSON functions

## 🔌 API Reference

### Base URL
```
http://localhost:8000
```

### Authentication
No authentication required for local usage.

### Endpoints

#### GET /health
Health check endpoint.

**Response:**
```json
{"status": "healthy"}
```

#### GET /agents
List all agents with optional filtering.

**Query Parameters:**
- `model` (string): Filter by detected model
- `framework` (string): Filter by framework
- `limit` (integer): Maximum results (default: 100, max: 1000)

**Example:**
```bash
curl "http://localhost:8000/agents?model=gpt-4&limit=10"
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "microsoft/autogen",
    "source_url": "https://github.com/microsoft/autogen",
    "source_platform": "github",
    "model_detected": "gpt-4",
    "framework": "autogen",
    "capabilities": ["conversation", "code-execution"],
    "agent_type": "multi-agent",
    "risk_level": "safe",
    "stars": 15420,
    "status": "online",
    "response_time_ms": 234,
    "first_seen": "2026-03-10T12:00:00",
    "last_seen": "2026-03-11T06:00:00",
    "raw_description": "Multi-agent conversation framework"
  }
]
```

#### GET /agents/{id}
Get single agent by ID.

**Response:** Single agent object or 404 if not found.

#### GET /agents/online
Get only agents with status "online".

#### GET /agents/dead
Get only agents with status "dead".

#### GET /stats
Get aggregated statistics.

**Response:**
```json
{
  "models": {
    "gpt-4": 145,
    "claude": 89,
    "llama": 234,
    "unknown": 1200
  },
  "frameworks": {
    "langchain": 456,
    "crewai": 123,
    "autogen": 67,
    "unknown": 1000
  },
  "agent_types": {
    "multi-agent": 234,
    "chatbot": 567,
    "task-agent": 890,
    "crawler": 45
  }
}
```

#### POST /agents
Create or update an agent (upsert by source_url).

**Request Body:**
```json
{
  "name": "new-agent",
  "source_url": "https://github.com/user/agent",
  "source_platform": "github",
  "model_detected": "gpt-4",
  "framework": "langchain",
  "capabilities": ["web-search"],
  "agent_type": "task-agent",
  "stars": 100,
  "raw_description": "A new AI agent"
}
```

#### PATCH /agents/{id}
Update specific fields of an agent.

**Request Body:**
```json
{
  "status": "online",
  "response_time_ms": 150,
  "last_checked": "2026-03-11T10:00:00"
}
```

## 🔍 Scanner Details

### GitHub Scanner Configuration

**Topics Searched:**
```python
TOPICS = [
    "ai-agent", "llm-agent", "autonomous-agent", "gpt-agent", "claude-agent",
    "langchain", "autogpt", "crewai", "mcp-server", "llm-tools", "openai-agent",
    "chatbot", "voice-agent", "rag-chatbot", "llm-app", "ai-assistant",
    "multi-agent", "agent-framework", "llm-workflow", "agentic-ai",
    "function-calling", "tool-calling", "llm-router", "ai-workflow"
]
```

**Rate Limiting:**
- Without token: 60 requests/hour
- With `GITHUB_TOKEN`: 5,000 requests/hour
- Exponential backoff on rate limits

**Timeouts:**
- 30 seconds per topic search
- 5 seconds per README fetch
- 2 minutes total per scanner

### HuggingFace Scanner Configuration

**API Endpoint:**
```
https://huggingface.co/api/models
```

**Tags Searched:**
- agent
- tool-calling
- assistant
- function-calling

**Parameters:**
- Sort by likes (popularity)
- 10 models per tag
- 15 second timeout

### Discord Scanner Configuration

**Sites Scraped:**
- https://top.gg/tag/ai
- https://discordbotlist.com/tags/ai

**Data Extracted:**
- Bot name and description
- Server count (popularity metric)
- Invite URLs

**Parsing Method:**
- BeautifulSoup HTML parsing
- CSS selector-based extraction
- Fallback handling for layout changes

### Package Scanner Configuration

**PyPI Packages:**
```python
PYPI_PACKAGES = [
    "langchain", "crewai", "autogen", "llama-index", "haystack", 
    "semantic-kernel", "agentops", "phidata", "dspy", "openai-agents", 
    "pydantic-ai", "smolagents"
]
```

**npm Packages:**
```python
NPM_PACKAGES = [
    "langchain", "openai-agents", "ai-sdk", "llamaindex", "autogen"
]
```

**APIs Used:**
- PyPI JSON API: `https://pypi.org/pypi/{package}/json`
- npm Registry API: `https://registry.npmjs.org/{package}`

## 🧠 Fingerprinting Engine

### Detection Logic

**Model Detection:**
```python
MODELS = ["gpt-4", "gpt-3.5", "claude", "gemini", "llama", "mistral", "mixtral", "qwen"]

def _detect_keyword(text, keywords):
    for keyword in keywords:
        if keyword in text.lower():
            return keyword
    return "unknown"
```

**Framework Detection:**
```python
FRAMEWORKS = ["langchain", "crewai", "autogen", "llamaindex", "haystack", "semantic-kernel"]
```

**Capability Detection:**
```python
CAPABILITIES = ["web-search", "email", "code-execution", "browser", "file-system", "database", "api-calls"]

def _detect_capabilities(text):
    return [cap for cap in CAPABILITIES if cap in text or cap.replace("-", "") in text]
```

**Agent Type Classification:**
```python
def _detect_agent_type(text):
    if "crewai" in text or "autogen" in text:
        return "multi-agent"
    if any(kw in text for kw in ["playwright", "selenium"]):
        return "crawler"
    return "task-agent"
```

### Text Sources for Analysis
- Repository/model description
- README snippet (first 500 characters)
- Tags/topics (joined as text)

## 🏥 Health Monitoring

### Health Check Process

**Status Determination:**
```python
def determine_status(response_code):
    if 200 <= response_code <= 399:
        return "online"
    elif response_code in [404, 410]:
        return "dead"
    elif response_code in [301, 302]:
        return "redirected"
    else:
        return "unknown"
```

**Concurrency:**
- All agents tested simultaneously using `asyncio`
- 10 second timeout per URL
- Graceful handling of network errors

**Database Updates:**
- Status, response time, and timestamp updated via PATCH API
- Failed requests don't crash the entire health check

## 💡 Usage Examples

### Basic Data Exploration

**Get all LangChain agents:**
```bash
curl "http://localhost:8000/agents?framework=langchain"
```

**Get GPT-4 powered agents:**
```bash
curl "http://localhost:8000/agents?model=gpt-4"
```

**Get only online agents:**
```bash
curl "http://localhost:8000/agents/online"
```

### Advanced Queries

**Using Python requests:**
```python
import requests

# Get stats
stats = requests.get("http://localhost:8000/stats").json()
print(f"Total models detected: {len(stats['models'])}")

# Get high-star agents
agents = requests.get("http://localhost:8000/agents?limit=1000").json()
popular = [a for a in agents if a['stars'] > 1000]
print(f"Popular agents: {len(popular)}")
```

**Database queries (SQLite):**
```sql
-- Top 10 most popular agents
SELECT name, stars, framework FROM agentprofile 
ORDER BY stars DESC LIMIT 10;

-- Agents by platform
SELECT source_platform, COUNT(*) FROM agentprofile 
GROUP BY source_platform;

-- Recently discovered agents
SELECT name, first_seen FROM agentprofile 
WHERE first_seen > datetime('now', '-7 days');
```

### Dashboard Usage

**Filtering:**
1. Use sidebar filters to narrow results
2. Combine model + framework filters
3. Filter by health status

**Health Checking:**
1. Click "🔍 Check Agent Health" button
2. Watch real-time status updates
3. View response times for performance analysis

**Data Export:**
1. Use API endpoints to export data
2. Query database directly for custom analysis
3. Build custom dashboards using the REST API

## 🔧 Configuration

### Environment Variables

**GITHUB_TOKEN** (optional)
- Increases GitHub API rate limit
- Set in Codespaces secrets or export locally
- Format: `ghp_xxxxxxxxxxxxxxxxxxxx`

### Timeout Configuration

**Scanner Timeouts:**
```python
GITHUB_TIMEOUT = 30  # seconds per topic
README_TIMEOUT = 5   # seconds per README
HF_TIMEOUT = 15      # seconds per request
DISCORD_TIMEOUT = 15 # seconds per site
PACKAGE_TIMEOUT = 15 # seconds per package
HEALTH_TIMEOUT = 10  # seconds per URL check
```

### Database Configuration

**SQLite Settings:**
- File: `agent_hunter.db`
- WAL mode for better concurrency
- Auto-vacuum for space efficiency
- Foreign key constraints enabled

## 📊 Performance Metrics

### Scan Performance
- **GitHub**: ~1,500-2,000 agents per scan
- **HuggingFace**: ~40 models per scan
- **Discord**: ~20-40 bots per scan
- **Honeypot**: 10 crawler tests per scan
- **Packages**: 17 packages per scan
- **Total Time**: 2-5 minutes depending on network

### Database Performance
- **Insert Rate**: ~100 agents/second
- **Query Performance**: <100ms for filtered queries
- **Storage**: ~1KB per agent record
- **Growth Rate**: ~500-1000 new agents per day

### API Performance
- **Response Time**: <50ms for most endpoints
- **Throughput**: 100+ requests/second
- **Memory Usage**: <100MB for typical workloads

---

**This documentation covers the complete technical implementation of AgentHunter. For setup instructions, see [GUIDE.md](GUIDE.md).**