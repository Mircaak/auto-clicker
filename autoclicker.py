"""
Jednoduchý Auto-Clicker
------------------------
- Zapnutí/vypnutí tlačítkem NEBO klávesovou zkratkou
- Nastavení rychlosti klikání (kliknutí za sekundu)
- Vlastní klávesová zkratka (klikni do pole a stiskni klávesu)

Instalace (stačí jednou):
    pip install pynput

Spuštění:
    python autoclicker.py
"""

import tkinter as tk
from tkinter import ttk
import threading
import time

from pynput.mouse import Controller as MouseController, Button
from pynput import keyboard


class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto-Clicker")
        self.root.geometry("340x320")
        self.root.resizable(False, False)

        self.mouse = MouseController()
        self.clicking = False
        self.click_thread = None

        # Klávesová zkratka (výchozí F6)
        self.hotkey = "f6"
        self.listening_for_key = False

        self._build_ui()
        self._start_hotkey_listener()

    # ---------- UI ----------
    def _build_ui(self):
        pad = {"padx": 16, "pady": 8}

        title = tk.Label(self.root, text="Auto-Clicker", font=("Segoe UI", 16, "bold"))
        title.pack(pady=(16, 4))

        # Stav
        self.status_var = tk.StringVar(value="VYPNUTO")
        self.status_label = tk.Label(
            self.root, textvariable=self.status_var,
            font=("Segoe UI", 12, "bold"), fg="white", bg="#c0392b",
            width=18, pady=6
        )
        self.status_label.pack(pady=8)

        # Rychlost klikání
        speed_frame = tk.Frame(self.root)
        speed_frame.pack(**pad, fill="x")

        tk.Label(speed_frame, text="Rychlost (kliknutí/s):").pack(anchor="w")
        self.speed_var = tk.DoubleVar(value=5.0)
        self.speed_scale = ttk.Scale(
            speed_frame, from_=0.5, to=20.0, orient="horizontal",
            variable=self.speed_var, command=self._update_speed_label
        )
        self.speed_scale.pack(fill="x")
        self.speed_label = tk.Label(speed_frame, text="5.0 kliknutí/s")
        self.speed_label.pack(anchor="e")

        # Režim počtu kliknutí
        count_frame = tk.Frame(self.root)
        count_frame.pack(**pad, fill="x")
        tk.Label(count_frame, text="Počet kliknutí:").pack(anchor="w")

        self.mode_var = tk.StringVar(value="infinite")
        mode_row = tk.Frame(count_frame)
        mode_row.pack(fill="x", pady=2)

        tk.Radiobutton(
            mode_row, text="Donekonečna", variable=self.mode_var,
            value="infinite", command=self._update_count_state
        ).pack(side="left")
        tk.Radiobutton(
            mode_row, text="Omezeně:", variable=self.mode_var,
            value="limited", command=self._update_count_state
        ).pack(side="left")

        self.count_var = tk.StringVar(value="100")
        self.count_entry = tk.Entry(mode_row, textvariable=self.count_var, width=8, state="disabled")
        self.count_entry.pack(side="left", padx=(4, 0))

        # Klávesová zkratka
        hotkey_frame = tk.Frame(self.root)
        hotkey_frame.pack(**pad, fill="x")
        tk.Label(hotkey_frame, text="Klávesová zkratka pro Start/Stop:").pack(anchor="w")

        self.hotkey_button = tk.Button(
            hotkey_frame, text=f"Aktuální: {self.hotkey.upper()}  (klikni pro změnu)",
            command=self._begin_hotkey_capture
        )
        self.hotkey_button.pack(fill="x", pady=4)

        # Start/Stop tlačítko
        self.toggle_button = tk.Button(
            self.root, text="Start (nebo stiskni zkratku)",
            font=("Segoe UI", 11, "bold"), bg="#27ae60", fg="white",
            command=self.toggle_clicking, height=2
        )
        self.toggle_button.pack(**pad, fill="x")

        tk.Label(
            self.root, text="Tip: okno může zůstat na pozadí,\nzkratka funguje odkudkoliv.",
            font=("Segoe UI", 8), fg="gray"
        ).pack(pady=(4, 0))

    def _update_speed_label(self, _=None):
        self.speed_label.config(text=f"{self.speed_var.get():.1f} kliknutí/s")

    def _update_count_state(self):
        if self.mode_var.get() == "limited":
            self.count_entry.config(state="normal")
        else:
            self.count_entry.config(state="disabled")

    # ---------- Klikání ----------
    def toggle_clicking(self):
        if self.clicking:
            self.stop_clicking()
        else:
            self.start_clicking()

    def start_clicking(self):
        if self.clicking:
            return
        self.clicking = True
        self.status_var.set("ZAPNUTO")
        self.status_label.config(bg="#27ae60")
        self.toggle_button.config(text="Stop (nebo stiskni zkratku)", bg="#c0392b")
        self.click_thread = threading.Thread(target=self._click_loop, daemon=True)
        self.click_thread.start()

    def stop_clicking(self):
        self.clicking = False
        self.status_var.set("VYPNUTO")
        self.status_label.config(bg="#c0392b")
        self.toggle_button.config(text="Start (nebo stiskni zkratku)", bg="#27ae60")

    def _click_loop(self):
        limited = self.mode_var.get() == "limited"
        target_count = 0
        if limited:
            try:
                target_count = max(int(self.count_var.get()), 1)
            except ValueError:
                target_count = 100

        done = 0
        while self.clicking:
            self.mouse.click(Button.left, 1)
            done += 1
            if limited and done >= target_count:
                self.root.after(0, self.stop_clicking)
                break
            delay = 1.0 / max(self.speed_var.get(), 0.1)
            time.sleep(delay)

    # ---------- Klávesová zkratka ----------
    def _begin_hotkey_capture(self):
        self.listening_for_key = True
        self.hotkey_button.config(text="Stiskni novou klávesu...")

    def _start_hotkey_listener(self):
        def on_press(key):
            key_name = self._key_to_str(key)

            if self.listening_for_key:
                if key_name:
                    self.hotkey = key_name
                    self.listening_for_key = False
                    self.root.after(0, lambda: self.hotkey_button.config(
                        text=f"Aktuální: {self.hotkey.upper()}  (klikni pro změnu)"
                    ))
                return

            if key_name == self.hotkey:
                self.root.after(0, self.toggle_clicking)

        self.listener = keyboard.Listener(on_press=on_press)
        self.listener.daemon = True
        self.listener.start()

    @staticmethod
    def _key_to_str(key):
        try:
            return key.char.lower()
        except AttributeError:
            return str(key).replace("Key.", "").lower()


if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClickerApp(root)
    root.mainloop()
