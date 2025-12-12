# 🧠 Cerina Protocol Foundry

**An AI-powered multi-agent system for generating safe and empathetic CBT (Cognitive Behavioral Therapy) protocols using LangGraph, FastAPI, React, and MCP.**

---

## 🏗️ Architecture

This system uses a **multi-agent orchestration** approach with:

- **5 Specialized Agents**: Drafting, Safety Guardian, Clinical Critic, Revision, and Supervisor
- **LangGraph Workflow**: Stateful execution with conditional routing
- **Postgres Checkpointing**: Crash-recovery and state persistence
- **Human-in-the-Loop**: Manual review at critical safety thresholds
- **MCP Integration**: Expose as a tool for AI assistants like Claude

---

## 📁 Project Structure

```
agent_architect/
├── backend/
│   ├── agents/          # Agent implementations
│   ├── state/           # Pydantic state models
│   ├── graph/           # LangGraph workflow
│   ├── api/             # FastAPI endpoints
│   ├── mcp/             # MCP server
│   └── db/              # Database schemas & migrations
├── frontend/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── hooks/       # Custom hooks (SSE, etc.)
│   │   └── pages/       # Application pages
│   └── package.json
├── docs/
│   ├── architecture.png
│   └── sequence.md
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Docker Desktop with `agent-net` network
- Postgres container running (postgres:agent123)
- Node.js 18+ and Python 3.12+
- OpenRouter API key

### 1. Clone and Configure

```bash
git clone <your-repo-url>
cd agent_architect
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

### 2. Initialize Database

```bash
# Connect to existing postgres container
docker exec -it postgres-db psql -U postgres
CREATE DATABASE cerina_foundry;
\q
```

### 3. Start Backend Services

```bash
# Build and run with docker-compose
docker-compose up -d

# Or run locally for development
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.api.main:app --reload
```

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Agents** | LangGraph, LangChain, OpenRouter API |
| **Backend** | FastAPI, Python 3.12 |
| **Frontend** | React (Vite), TypeScript |
| **Database** | PostgreSQL (Docker) |
| **Integration** | MCP (Model Context Protocol) |
| **Deployment** | Docker, Docker Compose |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/run` | Start a new workflow |
| `GET` | `/state/{thread_id}` | Get current state |
| `POST` | `/edit/{thread_id}` | Edit active draft |
| `POST` | `/approve/{thread_id}` | Resume after human review |
| `GET` | `/events/{thread_id}` | SSE stream of agent logs |

---

## 🧪 Testing

```bash
# Run backend tests
pytest backend/tests/

# Crash recovery test
docker-compose restart backend
# Verify state persistence

# Safety test
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_intent": "I want to harm myself"}'
# Should halt immediately
```

---

## 📖 Documentation

- [System Architecture](docs/architecture.png)
- [Sequence Diagrams](docs/sequence.md)
- [Agent Specifications](one.md)

---

## 🛡️ Safety Features

- **Safety Guardian Agent**: Detects self-harm and high-risk content
- **Safety Scoring**: 0-1 scale with configurable thresholds
- **Automatic Halting**: Stops workflow for human review
- **Empathy Checking**: Clinical critic ensures compassionate tone

---

## 🔗 MCP Integration

Use from Claude Desktop or other MCP-compatible clients:

```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "docker",
      "args": ["exec", "-i", "cerina-mcp", "python", "-m", "backend.mcp.server"]
    }
  }
}
```

---

## 📝 License

MIT License - See LICENSE file for details

---

## 👨‍💻 Author

Built for interview assessment - showcasing multi-agent systems, LangGraph workflows, and full-stack development.