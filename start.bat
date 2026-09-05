@echo off
title AuraCraft AI — Unified Studio & Web App
echo =======================================================
echo   🎨 AuraCraft AI — Unified Studio & Web App
echo =======================================================
echo.
echo Starting Studio Engine on http://localhost:7860...
start /b python dashboard.py
echo.
echo Starting Web App Frontend on http://localhost:3001...
cd frontend
npm run dev
