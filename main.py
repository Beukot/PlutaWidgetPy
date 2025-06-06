import sys
import tkinter as tk
import threading
from platform import system

import websocket
import json
import ctypes
import pystray

from pystray import MenuItem as item
from PIL import Image, ImageDraw

from settings_window import load_settings
from screeninfo import get_monitors

WS_URL = "wss://api.plutomierz.ovh"

class TransparentOverlay:
    def __init__(self):
        self.running = True

        self.root = tk.Tk()
        self.root.withdraw()
        self.window = tk.Toplevel(self.root)
        self.settings = load_settings()

        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.wm_attributes("-topmost", True)
        self.window.wm_attributes("-transparentcolor", "black")
        self.window.configure(bg="black")

        self.label = tk.Label(
            self.window,
            text="Plutuję...",
            font=(self.settings["font_family"], self.settings["font_size"], self.settings["font_weight"]),
            fg=self.settings["font_color"],
            bg="black"
        )
        self.label.pack()

        self.window.update_idletasks()
        self.set_position()
        self.make_clickthrough()

        threading.Thread(target=self.run_ws, daemon=True).start()
        threading.Thread(target=self.setup_tray_icon, daemon=True).start()

    def set_position(self):
        monitors = get_monitors()
        if self.settings["screen_index"] < len(monitors):
            screen = monitors[self.settings["screen_index"]]
        else:
            screen = monitors[0]

        win_width = self.window.winfo_reqwidth()
        x = screen.x + 0
        y = 0
        self.window.geometry(f"+{x}+{y}")

    def update_label(self, text):
        if not self.running:
            return
        try:
            self.label.config(text=text)
            self.set_position()
        except tk.TclError:
            pass

    def make_clickthrough(self):
        hwnd = ctypes.windll.user32.GetParent(self.window.winfo_id())
        styles = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
        styles |= 0x80000 | 0x20  # WS_EX_LAYERED | WS_EX_TRANSPARENT
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, styles)

    def run_ws(self):
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if data.get("type") == "pluta":
                    value = data.get("value")
                    self.window.after(0, self.update_label, f"{value} P")
            except Exception:
                self.window.after(0, self.update_label, "Błąd Pluty")

        def on_error(ws, error):
            self.window.after(0, self.update_label, f"Błąd: {error}")

        def on_close(ws, *_):
            self.window.after(0, self.update_label, "Pluta sobie poszedł!")

        def on_open(ws):
            print("Pluta jest z nami!")

        ws = websocket.WebSocketApp(
            WS_URL,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )

        ws.run_forever()

    def setup_tray_icon(self):
        icon_image = Image.new("RGB", (64, 64), (0, 0, 0))
        draw = ImageDraw.Draw(icon_image)
        draw.rectangle((0, 0, 63, 63), fill=(20, 20, 20))
        draw.text((18, 15), "P", fill="lime")

        menu = (
            item("Ustawienia", self.open_settings),
            item("Zamknij", self.exit_app)
        )

        icon = pystray.Icon("pluta_widget", icon_image, "Plutomierz", menu)
        self.icon = icon
        self.window.after(0, self.window.deiconify)
        icon.run()

    def reload_settings(self):
        from settings_window import load_settings
        self.settings = load_settings()

        self.label.config(
            font=(self.settings["font_family"], self.settings["font_size"], self.settings["font_weight"]),
            fg=self.settings["font_color"]
        )

        self.set_position()

    def open_settings(self, *args):
        from settings_window import SettingsWindow
        SettingsWindow(self.reload_settings)

    def exit_app(self, icon=None, item=None):
        self.running = False
        if self.icon:
            self.icon.stop()
        self.window.after(0, self.window.destroy)
        print("Zamknięto Plutę!")
        self.root.destroy()

if __name__ == "__main__":
    try:
        app = TransparentOverlay()
        app.root.mainloop()
        sys.exit(0)
    except KeyboardInterrupt:
        print("Zamknięto Plutę!")
        sys.exit(0)
