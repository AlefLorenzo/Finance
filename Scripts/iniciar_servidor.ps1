Set-Location (Split-Path -Parent $PSScriptRoot)
Write-Host 'Iniciando servidor IA Local em http://127.0.0.1:8000' -ForegroundColor Cyan
Write-Host 'Pressione CTRL+C para parar.' -ForegroundColor Yellow
Start-Process 'http://127.0.0.1:8000'
& ".\venv\Scripts\python.exe" -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
