import tkinter as tk
from tkinter import ttk, colorchooser, font
import os
import sys
import json
from screeninfo import get_monitors

SETTINGS_FILE = "settings.json"

default_settings = {
    "autostart": False,
    "font_size": 16,
    "font_family": "Consolas",
    "font_weight": "normal",
    "font_color": "#00FF00",
    "screen_index": 0
}


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return default_settings.copy()
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)


def save_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=4)


def add_to_startup():
    import winreg
    exe = sys.executable
    script = os.path.abspath(__file__)
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                         r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, "PlutaWidget", 0, winreg.REG_SZ, f'"{exe}" "{script}"')
    key.Close()


def remove_from_startup():
    import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
        winreg.DeleteValue(key, "PlutaWidget")
        key.Close()
    except FileNotFoundError:
        pass


class SettingsWindow:
    def __init__(self):
        self.settings = load_settings()
        self.root = tk.Tk()
        self.root.title("Ustawienia Pluta Widget")
        self.root.geometry("400x400")

        # Autostart
        self.autostart_var = tk.BooleanVar(value=self.settings["autostart"])
        tk.Checkbutton(self.root, text="Uruchamiaj z systemem", variable=self.autostart_var).pack(anchor="w", padx=10, pady=5)

        # Font family
        tk.Label(self.root, text="Czcionka:").pack(anchor="w", padx=10)
        self.font_family = ttk.Combobox(self.root, values=sorted(font.families()))
        self.font_family.set(self.settings["font_family"])
        self.font_family.pack(fill="x", padx=10)

        # Font size
        tk.Label(self.root, text="Rozmiar czcionki:").pack(anchor="w", padx=10)
        self.font_size = tk.Spinbox(self.root, from_=8, to=72)
        self.font_size.delete(0, "end")
        self.font_size.insert(0, self.settings["font_size"])
        self.font_size.pack(fill="x", padx=10)

        # Font weight
        tk.Label(self.root, text="Grubość czcionki:").pack(anchor="w", padx=10)
        self.font_weight = ttk.Combobox(self.root, values=["normal", "bold"])
        self.font_weight.set(self.settings["font_weight"])
        self.font_weight.pack(fill="x", padx=10)

        # Font color
        tk.Label(self.root, text="Kolor czcionki:").pack(anchor="w", padx=10)
        self.color_button = tk.Button(self.root, text="Wybierz kolor", bg=self.settings["font_color"], command=self.choose_color)
        self.color_button.pack(fill="x", padx=10, pady=5)

        # Screen index
        tk.Label(self.root, text="Ekran:").pack(anchor="w", padx=10)
        screens = get_monitors()
        self.screen_options = [f"{i}: {screen.width}x{screen.height}" for i, screen in enumerate(screens)]
        self.screen_index = ttk.Combobox(self.root, values=self.screen_options)
        self.screen_index.set(f"{self.settings['screen_index']}: {screens[self.settings['screen_index']].width}x{screens[self.settings['screen_index']].height}")
        self.screen_index.pack(fill="x", padx=10)

        # Save button
        tk.Button(self.root, text="Zapisz", command=self.save).pack(pady=15)

        self.root.mainloop()

    def choose_color(self):
        color = colorchooser.askcolor(title="Wybierz kolor")[1]
        if color:
            self.color_button.config(bg=color)

    def save(self):
        selected_screen = int(self.screen_index.get().split(":")[0])

        self.settings = {
            "autostart": self.autostart_var.get(),
            "font_family": self.font_family.get(),
            "font_size": int(self.font_size.get()),
            "font_weight": self.font_weight.get(),
            "font_color": self.color_button["bg"],
            "screen_index": selected_screen
        }

        save_settings(self.settings)

        if self.settings["autostart"]:
            add_to_startup()
        else:
            remove_from_startup()

        self.root.destroy()


if __name__ == "__main__":
    SettingsWindow()
