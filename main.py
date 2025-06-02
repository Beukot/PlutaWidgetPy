import sys
import tkinter as tk
import threading
from idlelib.configdialog import font_sample_text

import websocket
import json
import ctypes

import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw

WS_URL = "wss://api.plutomierz.ovh"

class TransparentOverlay(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()

        # Usuń ramkę okna
        self.overrideredirect(True)

        # Zawsze na wierzchu
        self.wm_attributes("-topmost", True)

        # Przezroczyste tło (tylko czarne elementy będą ukryte)
        self.wm_attributes("-transparentcolor", "black")
        self.configure(bg="black")

        # Tekst
        self.label = tk.Label(self, text="Plutuję...", font=("Consolas", 16), fg="lime", bg="black")
        self.label.pack()

        # Przesuń do prawego górnego rogu
        self.update_idletasks()
        self.set_position()
        self.make_clickthrough()

        # Uruchom WebSocket w tle
        threading.Thread(target=self.run_ws, daemon=True).start()

        # Ikona w trayu
        threading.Thread(target=self.setup_tray_icon, daemon=True).start()

    def set_position(self):
        # Pobierz rozdzielczość ekranu
        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)

        win_width = self.winfo_reqwidth()
        win_height = self.winfo_reqheight()

        x = 0  # 10px od prawej krawędzi
        y = 0  # 10px od góry
        self.geometry(f"+{x}+{y}")

    def update_label(self, text):
        self.label.config(text=text, font=tk.font.Font(family="Consolas", size=22, weight="bold"))
        self.set_position()  # Ustaw ponownie po zmianie rozmiaru

    def make_clickthrough(self):
        hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
        styles = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
        styles |= 0x80000 | 0x20  # WS_EX_LAYERED | WS_EX_TRANSPARENT
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, styles)

    def run_ws(self):
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if data.get("type") == "pluta":
                    value = data.get("value")
                    self.after(0, self.update_label, f"{value} P")
            except Exception:
                self.after(0, self.update_label, "Błąd Pluty")

        def on_error(ws, error):
            self.after(0, self.update_label, f"Błąd: {error}")

        def on_close(ws, *_):
            self.after(0, self.update_label, "Pluta sobie poszedł!")

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
        # Stwórz ikonkę (prostokąt + P)
        icon_image = Image.new("RGB", (64, 64), (0, 0, 0))
        draw = ImageDraw.Draw(icon_image)
        draw.rectangle((0, 0, 63, 63), fill=(20, 20, 20))
        draw.text((18, 15), "P", fill="lime")

        menu = (
            item("Pokaż ustawienia", self.open_settings),
            item("Zamknij", self.exit_app)
        )

        icon = pystray.Icon("pluta_widget", icon_image, "Plutometr", menu)
        self.icon = icon
        self.after(0, self.deiconify)  # Pokaż widget
        icon.run()

    def open_settings(self):
        self.after(0, lambda: print(">> Tu można otworzyć GUI ustawień"))

    def exit_app(self, icon=None, item=None):
        if self.icon:
            self.icon.stop()
        self.after(0, self.destroy)

if __name__ == "__main__":
    try:
        app = TransparentOverlay()
        app.mainloop()
        sys.exit(0)
    except KeyboardInterrupt:
        print("Zamknięto Plutę!")
        sys.exit(0)
