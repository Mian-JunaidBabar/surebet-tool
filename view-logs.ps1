# view-logs.ps1
# This script opens three separate PowerShell windows to show the live logs
# for the frontend, backend, and scraper services.

Write-Host "Starting log viewers for all services..." -ForegroundColor Green

# Start a new window for the frontend logs
Start-Process powershell -ArgumentList "-NoExit", "-Command", "docker-compose logs -f frontend"

# Start a new window for the backend logs
Start-Process powershell -ArgumentList "-NoExit", "-Command", "docker-compose logs -f backend"

# Start a new window for the scraper logs
Start-Process powershell -ArgumentList "-NoExit", "-Command", "docker-compose logs -f scraper"

Write-Host "All log windows have been launched." -ForegroundColor Green
