$porta = 8000
$proc = Get-NetTCPConnection -LocalPort $porta -ErrorAction SilentlyContinue | Select-Object -First 1
if ($proc) {
    Stop-Process -Id $proc.OwningProcess -Force
    Write-Host "[OK] Servidor parado (PID $($proc.OwningProcess))" -ForegroundColor Green
} else {
    Write-Host "[!] Nada rodando na porta $porta" -ForegroundColor Yellow
}
