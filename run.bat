@echo off
cd /d "%~dp0"
python src\main.py --vfs "test_folder" --script "tests\commands_vfs.txt"
pause