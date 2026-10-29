@echo off
cd /d "%~dp0.."
python src\main.py --vfs "test_folder" --script "tests\commands.txt"
pause