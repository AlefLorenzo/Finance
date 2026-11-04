param([Parameter(Mandatory=$true)][string]$Url)
Set-Location (Split-Path -Parent $PSScriptRoot)
& ".\venv\Scripts\python.exe" -m app.coletor.coletor $Url
