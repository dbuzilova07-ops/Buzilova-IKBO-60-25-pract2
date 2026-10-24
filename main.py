import tkinter as tk
import getpass
import socket
import os
import shlex

username = getpass.getuser()
hostname = socket.gethostname()

root = tk.Tk()
root.title(f"Эмулятор - [{username}@{hostname}]")
root.geometry("800x500")

# История команд
terminal = tk.Text(
    root,
    bg="black",
    fg="white",
    font=("Consolas", 12),
    state="disabled"
)
terminal.pack(fill=tk.BOTH, expand=True)

# Строка ввода
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
        command = os.path.expandvars(command)
        parts = shlex.split(command)

        if not parts:
            return

        name = parts[0]
        args = parts[1:]

        if name == "ls":
            print_terminal(f"ls: аргументы {args}")

        elif name == "cd":
            if len(args) > 1:
                print_terminal("Ошибка: cd принимает не более одного аргумента")
            else:
                print_terminal(f"cd: аргументы {args}")

        elif name == "exit":
            if args:
                print_terminal("Ошибка: exit не принимает аргументы")
            else:
                root.destroy()

        else:
            print_terminal(f"Ошибка: неизвестная команда {name}")

    except ValueError as error:
        print_terminal(f"Ошибка аргументов: {error}")


def on_enter(event):
    command = command_entry.get()
    command_entry.delete(0, tk.END)

    print_terminal("$ " + command)
    execute_command(command)


command_entry.bind("<Return>", on_enter)

print_terminal("Добро пожаловать в эмулятор UNIX!")
root.mainloop()