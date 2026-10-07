# =============================================================================
# Dukaan Growth Worker — Local Runner (PowerShell)
# Launches FastAPI backend on :8000 and Next.js frontend on :3000
# =============================================================================

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "   🛒 Dukaan Growth Worker — Starting Services   " -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

$WorkspaceRoot = $PSScriptRoot

# 1. Start Backend
Write-Host "[1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Yellow
$BackendProc = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$WorkspaceRoot\backend'; uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --reload" -PassThru

# 2. Start Frontend
Write-Host "[2/2] Starting Next.js Frontend on http://localhost:3000 ..." -ForegroundColor Yellow
$FrontendProc = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$WorkspaceRoot\frontend'; npm run dev" -PassThru

Write-Host ""
Write-Host "Both services launched!" -ForegroundColor Green
Write-Host "Open your browser at: http://localhost:3000" -ForegroundColor Green
Write-Host "Backend API docs at:  http://127.0.0.1:8000/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "Press any key to stop all background processes..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Stop-Process -Id $BackendProc.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $FrontendProc.Id -Force -ErrorAction SilentlyContinue
Write-Host "All services stopped." -ForegroundColor Red
