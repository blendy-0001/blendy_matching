@echo off
REM クイック共有スクリプト - このファイルをダブルクリックするだけで外部共有できます
cd /d "%~dp0"
python deploy.py
pause
