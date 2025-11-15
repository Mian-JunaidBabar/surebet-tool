@echo off
TITLE Surebet Tool - Stopper
ECHO ==========================================================
ECHO SUREBET TOOL - STOPPING APPLICATION
ECHO ==========================================================
ECHO.
ECHO This will safely shut down all running services.
docker-compose down
ECHO.
ECHO All services have been successfully stopped.
ECHO.
pause