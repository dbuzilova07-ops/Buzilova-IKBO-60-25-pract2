@echo off
cd /d "%~dp0"
python main.py --vfs "vfs_min" --script "commands_vfs.txt"
pause