import tkinter as tk
import getpass
import socket
import os
import shlex
import argparse
import hashlib
from pathlib import Path

# Параметры запуска
parser = argparse.ArgumentParser(description="Эмулятор UNIX")
parser.add_argument("--vfs", help="Путь к виртуальной файловой системе")
parser.add_argument("--script", help="Путь к стартовому скрипту")
config = parser.parse_args()

print("Параметры эмулятора:")
print("VFS:", config.vfs)
print("Стартовый скрипт:", config.script)

username = getpass.getuser()
hostname = socket.gethostname()

# Данные виртуальной файловой системы
vfs_files = {}
vfs_dirs = set()
vfs_name = None
vfs_hash = None
vfs_error = None

# Флаг завершения приложения
closing = False


def update_hash(hasher, data):
    # Добавляем длину данных и сами данные
    hasher.update(len(data).to_bytes(8, "big"))
    hasher.update(data)


def load_vfs(path):
    global vfs_files, vfs_dirs, vfs_name, vfs_hash

    source = Path(path)

    if not source.exists():
        raise FileNotFoundError(f"VFS не найдена: {path}")

    if not source.is_dir():
        raise ValueError("VFS должна быть директорией")

    if source.is_symlink():
        raise ValueError("Символические ссылки не поддерживаются")

    files = {}
    directories = set()

    # Получаем все файлы и каталоги
    for item in source.rglob("*"):
        if item.is_symlink():
            raise ValueError(f"Символическая ссылка: {item}")

        relative_path = item.relative_to(source).as_posix()

        if item.is_dir():
            directories.add(relative_path)

        elif item.is_file():
            # Читаем содержимое в память
            files[relative_path] = item.read_bytes()

        else:
            raise ValueError(f"Неподдерживаемый объект: {item}")

    # Вычисляем общий хеш VFS
    hasher = hashlib.sha256()

    for directory in sorted(directories):
        hasher.update(b"D")
        update_hash(hasher, directory.encode("utf-8"))

    for filename in sorted(files):
        hasher.update(b"F")
        update_hash(hasher, filename.encode("utf-8"))
        update_hash(hasher, files[filename])

    # Сохраняем загруженные данные
    vfs_files = files
    vfs_dirs = directories
    vfs_name = source.name
    vfs_hash = hasher.hexdigest()


# Графический интерфейс
root = tk.Tk()
root.title(f"Эмулятор - [{username}@{hostname}]")
root.geometry("800x500")

terminal = tk.Text(
    root,
    bg="black",
    fg="white",
    font=("Consolas", 12),
    state="disabled"
)
terminal.pack(fill=tk.BOTH, expand=True)

command_entry = tk.Entry(
    root,
    bg="black",
    fg="white",
    insertbackground="white",
    font=("Consolas", 12)
)
command_entry.pack(fill=tk.X)
command_entry.focus_set()


def print_terminal(text):
    terminal.config(state="normal")
    terminal.insert(tk.END, text + "\n")
    terminal.see(tk.END)
    terminal.config(state="disabled")


def execute_command(command):
    global closing

    try:
        command = os.path.expandvars(command)
        parts = shlex.split(command)

        if not parts:
            return True

        name = parts[0]
        args = parts[1:]

        if name == "ls":
            print_terminal(f"ls: аргументы {args}")
            return True

        elif name == "cd":
            if len(args) > 1:
                print_terminal(
                    "Ошибка: cd принимает не более одного аргумента"
                )
                return False

            print_terminal(f"cd: аргументы {args}")
            return True

        elif name == "vfs-info":
            if args:
                print_terminal("Ошибка: vfs-info не принимает аргументы")
                return False

            if vfs_name is None:
                print_terminal("Ошибка: VFS не загружена")
                return False

            print_terminal(f"Имя VFS: {vfs_name}")
            print_terminal(f"SHA-256: {vfs_hash}")
            print_terminal(f"Количество файлов: {len(vfs_files)}")
            print_terminal(f"Количество папок: {len(vfs_dirs)}")
            return True

        elif name == "exit":
            if args:
                print_terminal("Ошибка: exit не принимает аргументы")
                return False

            closing = True
            root.after_idle(root.destroy)
            return True

        else:
            print_terminal(f"Ошибка: неизвестная команда {name}")
            return False

    except ValueError as error:
        print_terminal(f"Ошибка аргументов: {error}")
        return False


def on_enter(event):
    command = command_entry.get()
    command_entry.delete(0, tk.END)

    print_terminal("$ " + command)
    execute_command(command)


def run_startup_script():
    if not config.script:
        return

    try:
        script_path = Path(config.script)

        with script_path.open("r", encoding="utf-8-sig") as file:
            commands = file.readlines()

        print_terminal(f"Запуск скрипта: {config.script}")

        for line_number, line in enumerate(commands, start=1):
            if closing:
                break

            command = line.strip()

            if not command:
                continue

            print_terminal("$ " + command)
            success = execute_command(command)

            if not success:
                print_terminal(
                    f"Ошибка в строке {line_number}. "
                    "Продолжаем выполнение."
                )

        if not closing:
            print_terminal("Выполнение скрипта завершено.")

    except (OSError, UnicodeError) as error:
        print_terminal(f"Ошибка стартового скрипта: {error}")


def initialize():
    global vfs_error

    print_terminal("Добро пожаловать в эмулятор UNIX!")

    if config.vfs:
        try:
            load_vfs(config.vfs)
            print_terminal(f"VFS загружена: {vfs_name}")

        except (OSError, ValueError) as error:
            vfs_error = str(error)
            print_terminal(f"Ошибка загрузки VFS: {vfs_error}")

    run_startup_script()


command_entry.bind("<Return>", on_enter)

root.after(100, initialize)
root.mainloop()