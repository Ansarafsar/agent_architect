@echo off
echo Starting Cerina Protocol Foundry Backend...
echo.
echo Checking environment...

if not exist .env (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and configure it.
    pause
    exit /b 1
)

echo Starting FastAPI server...
echo Backend will be available at http://localhost:8000
echo API docs at http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop
echo.

python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
