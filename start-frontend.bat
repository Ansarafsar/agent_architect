@echo off
echo Starting Cerina Protocol Foundry Frontend...
echo.
cd frontend
echo Installing dependencies if needed...
call npm install
echo.
echo Starting Vite dev server...
echo Frontend will be available at http://localhost:5173
echo.
echo Press Ctrl+C to stop
echo.
call npm run dev
