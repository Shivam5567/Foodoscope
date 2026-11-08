@echo off
REM ---------------------------------------------------------------------------
REM Mise — Windows launcher.
REM Loads .env into the environment, then runs uvicorn in THIS window so the
REM server logs stream to the console in real time.
REM ---------------------------------------------------------------------------
cd /d "%~dp0"

if exist .env (
  for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
    if not "%%A"=="" set "%%A=%%B"
  )
)

echo.
echo   Mise - computational gastronomy cooking copilot
echo   ----------------------------------------------
echo   App      : http://localhost:8000
echo   Health   : http://localhost:8000/api/health
echo   Logs     : this window (Ctrl+C to stop)
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: python was not found on PATH.
  pause
  exit /b 1
)

python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
echo.
echo Server stopped.
pause
