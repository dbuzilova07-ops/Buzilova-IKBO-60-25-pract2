
"""Графический эмулятор командной строки UNIX (этапы 1–3)."""

import argparse
import getpass
import hashlib
import os
from pathlib import Path
import shlex
import socket
import tkinter as tk


WINDOW_SIZE = "800x500"
FONT = ("Consolas", 12)
SCRIPT_DELAY_MS = 100
HASH_LENGTH_BYTES = 8


def parse_arguments():
    """Получить пути к VFS и стартовому скрипту из аргументов запуска."""
    parser = argparse.ArgumentParser(description="Эмулятор UNIX")
    parser.add_argument("--vfs", help="Путь к виртуальной файловой системе")
    parser.add_argument("--script", help="Путь к стартовому скрипту")
    return parser.parse_args()


def hash_item(hasher, kind, name, content=None):
    """Добавить запись с однозначным разделением полей в SHA-256."""
    hasher.update(kind)
    for data in (name.encode("utf-8"), content):
        if data is not None:
            hasher.update(len(data).to_bytes(HASH_LENGTH_BYTES, "big"))
            hasher.update(data)


def read_vfs(source):
    """Прочитать директорию в память, не изменяя файлов на диске."""
    if not source.exists():
        raise FileNotFoundError(f"VFS не найдена: {source}")
    if not source.is_dir() or source.is_symlink():
        raise ValueError("VFS должна быть обычной директорией")

    files = {}
    directories = set()
    for item in source.rglob("*"):
        if item.is_symlink():
            raise ValueError(f"Ссылки не поддерживаются: {item}")
        name = item.relative_to(source).as_posix()
        if item.is_dir():
            directories.add(name)
        elif item.is_file():
            files[name] = item.read_bytes()
        else:
            raise ValueError(f"Неподдерживаемый объект: {item}")
    return files, directories


def calculate_hash(files, directories):
    """Вычислить SHA-256 для структуры папок и содержимого файлов."""
    hasher = hashlib.sha256()
    for name in sorted(directories):
        hash_item(hasher, b"D", name)
    for name in sorted(files):
        hash_item(hasher, b"F", name, files[name])
    return hasher.hexdigest()


class ShellEmulator:
    """GUI-эмулятор с загрузкой VFS и поддержкой стартовых скриптов."""

    def __init__(self, config):
        """Подготовить окно, состояние VFS и обработчик ввода."""
        self.config = config
        self.files = {}
        self.directories = set()
        self.vfs_name = None
        self.vfs_hash = None
        self.closing = False
        self.root = tk.Tk()
        user = getpass.getuser()
        host = socket.gethostname()
        self.root.title(f"Эмулятор - [{user}@{host}]")
        self.root.geometry(WINDOW_SIZE)
        self.create_widgets()
        self.root.after(SCRIPT_DELAY_MS, self.initialize)

    def create_widgets(self):
        """Создать поле истории команд и отдельную строку ввода."""
        self.terminal = tk.Text(
            self.root, bg="black", fg="white", font=FONT, state="disabled"
        )
        self.terminal.pack(fill=tk.BOTH, expand=True)
        self.entry = tk.Entry(
            self.root, bg="black", fg="white",
            insertbackground="white", font=FONT
        )
        self.entry.pack(fill=tk.X)
        self.entry.bind("<Return>", self.on_enter)
        self.entry.focus_set()

    def output(self, message):
        """Добавить строку в историю команд, не разрешая её редактировать."""
        self.terminal.config(state="normal")
        self.terminal.insert(tk.END, message + "\n")
        self.terminal.see(tk.END)
        self.terminal.config(state="disabled")

    def initialize(self):
        """Показать параметры, загрузить VFS и запустить сценарий."""
        self.output("Добро пожаловать в эмулятор UNIX!")
        if self.config.vfs:
            try:
                source = Path(self.config.vfs)
                self.files, self.directories = read_vfs(source)
                self.vfs_name = source.name
                self.vfs_hash = calculate_hash(
                    self.files, self.directories
                )
                self.output(f"VFS загружена: {self.vfs_name}")
            except (OSError, ValueError) as error:
                self.output(f"Ошибка загрузки VFS: {error}")
        self.run_script()

    def command_info(self, args):
        """Показать сведения о VFS или сообщить об ошибке."""
        if args:
            self.output("Ошибка: vfs-info не принимает аргументы")
            return False
        if self.vfs_name is None:
            self.output("Ошибка: VFS не загружена")
            return False
        self.output(f"Имя VFS: {self.vfs_name}")
        self.output(f"SHA-256: {self.vfs_hash}")
        self.output(f"Количество файлов: {len(self.files)}")
        self.output(f"Количество папок: {len(self.directories)}")
        return True

    def command_cd(self, args):
        """Выполнить заглушку cd и проверить число аргументов."""
        if len(args) > 1:
            self.output("Ошибка: cd принимает не более одного аргумента")
            return False
        self.output(f"cd: аргументы {args}")
        return True

    def command_exit(self, args):
        """Закрыть окно, только если у exit отсутствуют аргументы."""
        if args:
            self.output("Ошибка: exit не принимает аргументы")
            return False
        self.closing = True
        self.root.after_idle(self.root.destroy)
        return True

    def dispatch(self, name, args):
        """Выбрать обработчик команды по её имени."""
        if name == "ls":
            self.output(f"ls: аргументы {args}")
            return True
        if name == "cd":
            return self.command_cd(args)
        if name == "vfs-info":
            return self.command_info(args)
        if name == "exit":
            return self.command_exit(args)
        self.output(f"Ошибка: неизвестная команда {name}")
        return False

    def execute(self, command):
        """Раскрыть переменные окружения и выполнить введённую команду."""
        try:
            expanded = os.path.expandvars(command)
            parts = shlex.split(expanded)
        except ValueError as error:
            self.output(f"Ошибка аргументов: {error}")
            return False
        if not parts:
            return True
        return self.dispatch(parts[0], parts[1:])

    def on_enter(self, event):
        """Выполнить команду из поля ввода после нажатия Enter."""
        command = self.entry.get()
        self.entry.delete(0, tk.END)
        self.output("$ " + command)
        self.execute(command)
        return "break"

    def run_script(self):
        """Выполнить стартовый скрипт, пропуская ошибочные строки."""
        if not self.config.script:
            return
        try:
            path = Path(self.config.script)
            commands = path.read_text(encoding="utf-8-sig").splitlines()
        except (OSError, UnicodeError) as error:
            self.output(f"Ошибка стартового скрипта: {error}")
            return
        self.output(f"Запуск скрипта: {self.config.script}")
        for line_number, line in enumerate(commands, start=1):
            if self.closing:
                break
            command = line.strip()
            if not command:
                continue
            self.output("$ " + command)
            if not self.execute(command):
                self.output(
                    f"Ошибка в строке {line_number}. "
                    "Продолжаем выполнение."
                )
        if not self.closing:
            self.output("Выполнение скрипта завершено.")

    def run(self):
        """Запустить цикл обработки событий графического окна."""
        self.root.mainloop()


def main():
    """Точка входа в эмулятор."""
    config = parse_arguments()
    print("Параметры эмулятора:")
    print("VFS:", config.vfs)
    print("Стартовый скрипт:", config.script)
    ShellEmulator(config).run()


if __name__ == "__main__":
    main()
