@echo off
cd /d "%~dp0"
python main.py --vfs "vfs_few" --script "commands_vfs.txt"
pause