@echo off
cd /d "%~dp0"
python main.py --vfs "vfs_deep" --script "commands_vfs.txt"
pause