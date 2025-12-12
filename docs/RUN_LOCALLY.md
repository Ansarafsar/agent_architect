# RUN LOCALLY (Without Docker)

This guide is for running the backend and frontend locally without Docker containers.

## Prerequisites

1. ✅ Python 3.12+ installed
2. ✅ Node.js 18+ installed  
3. ✅ Postgres container running: `docker ps | grep postgres-db`
4. ✅ `.env` file configured with your OpenRouter API key

## Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Start Backend

```bash
# Windows
start-backend.bat

# Or manually:
python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be at: **http://localhost:8000**
API docs at: **http://localhost:8000/docs**

## Step 3: Start Frontend (New Terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend will be at: **http://localhost:5173**

## Step 4: Test

Open your browser to **http://localhost:5173** and start generating protocols!

---

## Troubleshooting

### Import Error: No module named 'langgraph'
```bash
pip install -r requirements.txt
```

### Backend can't connect to database
Make sure postgres container is running:
```bash
docker ps | grep postgres-db
# Should show the container
```

### Port already in use
Change ports in:
- Backend: `start-backend.bat` (change `--port 8000`)
- Frontend: `frontend/vite.config.ts` (change `port: 5173`)

---

## Why Run Locally?

✅ Faster development (no rebuild needed)  
✅ Better debugging with IDE  
✅ Easier to test changes  
✅ No Docker memory overhead

---

## Running Tests

```bash
# Quick workflow test
python backend/tests/test_workflow.py

# Safety test (should halt immediately)
# Add test that sends: "I want to harm myself"
```
