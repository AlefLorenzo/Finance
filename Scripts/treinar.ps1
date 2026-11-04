Set-Location (Split-Path -Parent $PSScriptRoot)
& ".\venv\Scripts\python.exe" -m app.feedback.exportar_dataset
& ".\venv\Scripts\python.exe" -m app.modelo.fine_tuning
