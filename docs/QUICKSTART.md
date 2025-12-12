# 🚀 Quick Start Guide

## Prerequisites

✅ Docker Desktop running with `agent-net` network
✅ Postgres container `postgres-db` running
✅ Python 3.12+ installed
✅ Node.js 18+ installed
✅ OpenRouter API key

---

## Step 1: Environment Setup

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` and add your OpenRouter API key:
```
OPENROUTER_API_KEY=your_actual_key_here
```

---

## Step 2: Install Dependencies

### Backend
```bash
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
cd ..
```

---

## Step 3: Verify Database

Database should already be initialized. To verify:

```bash
docker exec -it postgres-db psql -U postgres -d cerina_foundry -c "\dt"
```

You should see tables: `checkpoints`, `workflow_logs`, `protocol_drafts`, etc.

---

## Step 4: Start Backend API

```bash
uvicorn backend.api.main:app --reload
```

Backend will be available at: http://localhost:8000

API docs: http://localhost:8000/docs

---

## Step 5: Start Frontend

In a new terminal:

```bash
cd frontend
npm run dev
```

Frontend will be available at: http://localhost:5173

---

## Step 6: Test the System

### Option A: Web UI
1. Open http://localhost:5173
2. Enter a request: "Create a protocol for managing work-related stress"
3. Click "Generate Protocol"
4. Watch the agents work in real-time!

### Option B: Test Script
```bash
python backend/tests/test_workflow.py
```

### Option C: API Test
```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"user_intent": "Create a sleep hygiene protocol"}'
```

---

## Using with Claude Desktop (MCP)

See `docs/MCP_INTEGRATION.md` for setup instructions.

---

## Troubleshooting

### Backend won't start
- Check if port 8000 is available
- Verify database is accessible: `docker ps | grep postgres`
- Check `.env` file has valid credentials

### Frontend can't connect
- Ensure backend is running on port 8000
- Check browser console for CORS errors
- Verify proxy configuration in `vite.config.ts`

### Database connection failed
- Restart postgres container: `docker restart postgres-db`
- Check network: `docker network inspect agent-net`
- Verify port mapping: `docker port postgres-db`

---

## Architecture Overview

```
┌─────────────┐
│   User UI   │ (React on :5173)
└──────┬──────┘
       │ HTTP/SSE
┌──────▼──────┐
│  FastAPI    │ (Backend on :8000)
│   Server    │
└──────┬──────┘
       │
┌──────▼──────────────────────┐
│    LangGraph Workflow       │
│  ┌────────────────────┐     │
│  │  Drafting Agent    │     │
│  └─────────┬──────────┘     │
│            │                 │
│  ┌─────────▼──────────┐     │
│  │  Safety Guardian   │     │
│  └─────────┬──────────┘     │
│            │                 │
│  ┌─────────▼──────────┐     │
│  │  Clinical Critic   │     │
│  └─────────┬──────────┘     │
│            │                 │
│  ┌─────────▼──────────┐     │
│  │    Supervisor      │     │
│  └─────────┬──────────┘     │
│            │ (decision)      │
│     ┌──────┴──────┐         │
│     │             │          │
│  Revise      Human Review   │
│     │             │          │
│  └──┴─────────────┴────┐    │
│     Finalize           │    │
└────────────────────────┘    │
                               │
       ┌───────────────────────┘
       │
┌──────▼──────┐
│  Postgres   │ (Checkpointing + State)
│  Database   │
└─────────────┘
```

---

## What's Next?

- Run safety tests with harmful input
- Test crash recovery (kill backend mid-execution)
- Try the MCP integration with Claude
- Explore the API at http://localhost:8000/docs
- Review logs for agent decision-making

---

**Need Help?** Check the full documentation in `docs/` folder.
