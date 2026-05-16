@echo off
title Casino Side Hustle - Local Dev Server
echo ========================================
echo  Local Dev Server Starting...
echo  http://localhost:8080
echo  Press Ctrl+C to stop.
echo ========================================
echo.

:: Open browser 2 seconds after server starts
start /b cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8080"

:: Start Python server (stays open until you press Ctrl+C)
python -m http.server 8080
