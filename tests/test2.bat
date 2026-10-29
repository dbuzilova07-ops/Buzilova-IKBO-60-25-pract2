@echo off
cd /d "%~dp0.."
python src\main.py --script "tests\commands.txt"
pause