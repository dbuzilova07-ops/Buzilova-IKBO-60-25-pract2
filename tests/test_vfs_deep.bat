@echo off
cd /d "%~dp0.."
python src\main.py --vfs "vfs_deep" --script "tests\commands_vfs.txt"
pause