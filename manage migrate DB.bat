@echo off
manage makemigrations
manage migrate
echo press any key to continue
pause >nul