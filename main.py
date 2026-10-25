import tkinter as tk
import getpass
import socket
import os
import shlex
import argparse
from pathlib import Path

# Получаем параметры запуска
parser = argparse.ArgumentParser(description="Эмулятор UNIX")
parser.add_argument("--vfs", help="Путь к виртуальной файловой системе")
parser.add_argument("--script", help="Путь к стартовому скрипту")
config = parser.parse_args()

# Отладочный вывод параметров
print("Параметры эмулятора:")
print("VFS:", config.vfs)
print("Стартовый скрипт:", config.script)

# Получаем данные операционной системы
username = getpass.getuser()
hostname = socket.gethostname()

# Создаём графическое окно
root = tk.Tk()
root.title(f"Эмулятор - [{username}@{hostname}]")
root.geometry("800x500")

# История терминала
terminal = tk.Text(
    root,
    bg="black",
    fg="white",
    font=("Consolas", 12),
    state="disabled"
)
terminal.pack(fill=tk.BOTH, expand=True)

# Поле ввода команд
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
    try:
        # Подставляем переменные окружения
        command = os.path.expandvars(command)

        # Разделяем команду на части
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
                print_terminal("Ошибка: cd принимает не более одного аргумента")
                return False

            print_terminal(f"cd: аргументы {args}")
            return True

        elif name == "exit":
            if args:
                print_terminal("Ошибка: exit не принимает аргументы")
                return False

            root.destroy()
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
            if not root.winfo_exists():
                break

            command = line.strip()

            if not command:
                continue

            print_terminal("$ " + command)

            success = execute_command(command)

            if not success:
                print_terminal(
                    f"Ошибка в строке {line_number}. Продолжаем выполнение."
                )

        if root.winfo_exists():
            print_terminal("Выполнение скрипта завершено.")

    except (OSError, UnicodeError) as error:
        print_terminal(f"Ошибка выполнения стартового скрипта: {error}")


command_entry.bind("<Return>", on_enter)

print_terminal("Добро пожаловать в эмулятор UNIX!")

# Автоматически выполняем скрипт после открытия окна
root.after(100, run_startup_script)

root.mainloop()