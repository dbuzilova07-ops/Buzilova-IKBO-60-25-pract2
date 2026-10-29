@echo off
cd /d "%~dp0.."
python src\main.py --vfs "vfs_few" --script "tests\commands_vfs.txt"
pause