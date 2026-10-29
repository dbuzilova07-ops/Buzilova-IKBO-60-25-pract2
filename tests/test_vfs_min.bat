@echo off
cd /d "%~dp0.."
if not exist "vfs_min" mkdir "vfs_min"
python src\main.py --vfs "vfs_min" --script "tests\commands_vfs.txt"
pause