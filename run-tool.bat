@echo off
TITLE Surebet Tool - Starter

ECHO ==========================================================
ECHO  SUREBET TOOL - STARTING APPLICATION
ECHO ==========================================================
ECHO.
ECHO This script will start all the necessary services using Docker.
ECHO The first run may take a few minutes to build the application.
ECHO The dashboard will be available at http://localhost:3000
ECHO.

ECHO Starting Docker containers in the background...
docker-compose up -d --build

ECHO.
ECHO Waiting 15 seconds for services to initialize...
timeout /t 15 > nul

ECHO.
ECHO Launching the Surebet Tool in your default browser...
start http://localhost:3000/dashboard

ECHO.
ECHO ==========================================================
ECHO  APPLICATION IS RUNNING IN THE BACKGROUND!
ECHO  To stop the application, run the 'stop-surebet-tool.bat' file.
ECHO ==========================================================
ECHO.

pause