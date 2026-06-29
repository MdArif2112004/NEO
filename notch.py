"""
notch.py — Ghost Operator Tactical Ribbon v2
True AppBar + Global Hotkey + Wider Center Panel
"""
import tkinter as tk
import requests
import subprocess
import threading
from neo.tools.clip_ingest import execute_clip_ingest
import time
import ctypes
from ctypes import wintypes
import pyperclip
from neo.llm.model import get_model
import os
from neo.tools.screen import read_screen
import json

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("[NOTCH] Run: pip install keyboard")

ABM_NEW = 0x0000
ABM_REMOVE = 0x0001
ABM_QUERYPOS = 0x0002
ABM_SETPOS = 0x0003
ABE_TOP = 1

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

class APPBARDATA(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("hWnd", wintypes.HWND),
                ("uCallbackMessage", wintypes.UINT), ("uEdge", wintypes.UINT),
                ("rc", RECT), ("lParam", wintypes.LPARAM)]

clip_ingest_btn = None
vision_strike_btn = None

def trigger_vision_strike():
    vision_strike_btn.configure(text="[..]", fg="#00E5FF")
    vision_strike_btn.update()
    def run():
        try:
            subprocess.Popen(["python", "neo/tools/vision_strike.py"], shell=True)
        except Exception as e:
            print(f"[HUD] VS FAULT: {e}")
        vision_strike_btn.after(0, lambda: vision_strike_btn.configure(text="[VS]", fg="#00FFFF"))
    threading.Thread(target=run, daemon=True).start()

def trigger_clip_ingest():
    clip_ingest_btn.configure(text="[..]", fg="#F5A623")
    clip_ingest_btn.update()
    def run():
        result = execute_clip_ingest(
            instruction="Clean up this text. Fix grammar, remove fluff, format for maximum scannability.")
        print(f"[HUD] CI: {result}")
        clip_ingest_btn.after(0, lambda: clip_ingest_btn.configure(text="[CI]", fg="#00FFFF"))
    threading.Thread(target=run, daemon=True).start()


class NeoNotch:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg='black')

        self.state_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "notch_state.json")
        self.voice_state_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "state.txt")

        self.screen_width = self.root.winfo_screenwidth()
        self.notch_height = 28
        self.root.geometry(f"{self.screen_width}x{self.notch_height}+0+0")

        self.root.update_idletasks()
        self.hwnd = int(self.root.wm_frame(), 16)
        self.register_appbar()

        self.root.bind("<Control-Shift-Q>", self.on_close)

        # Layout: left(1) | center(3) | right(1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=3)  # center gets triple space
        self.root.grid_columnconfigure(2, weight=1)

        # ── LEFT WING ─────────────────────────────────────────
        self.left_frame = tk.Frame(self.root, bg='black')
        self.left_frame.grid(row=0, column=0, sticky="w", padx=(10, 0))

        self.status_dot = tk.Label(
            self.left_frame, text="●", fg="#0055FF", bg="black", font=("Arial", 11))
        self.status_dot.pack(side=tk.LEFT, padx=(4, 2))

        self.task_container = tk.Frame(self.left_frame, bg='black')
        self.task_container.pack(side=tk.LEFT)

        self.task_text = ""   # left segment now shows a live clock + today's bounty count

        self.system_lbl = tk.Label(
            self.task_container, text=self.task_text,
            fg="#666666", bg="black", font=("Consolas", 7, "bold"))
        self.system_lbl.pack(side=tk.LEFT)

        _bs = {"bg": "#111111", "activebackground": "#222222",
               "activeforeground": "white", "bd": 0,
               "font": ("Consolas", 7, "bold"), "cursor": "hand2"}
        self.l_btn_done = tk.Button(
            self.task_container, text="✓", fg="#00FF00",
            command=lambda: self.update_task("COMPLETED"), **_bs)
        self.l_btn_dismiss = tk.Button(
            self.task_container, text="✗", fg="#FF4444",
            command=lambda: self.update_task("DISMISSED"), **_bs)
        self.l_btn_skip = tk.Button(
            self.task_container, text="→", fg="#FFAA00",
            command=lambda: self.update_task("SKIPPED"), **_bs)

        self.task_container.bind("<Enter>", self.show_left_buttons)
        self.task_container.bind("<Leave>", self.hide_left_buttons)
        self.system_lbl.bind("<Enter>", self.show_left_buttons)

        # ── CENTER PANEL ──────────────────────────────────────
        self.center_frame = tk.Frame(self.root, bg='black')
        self.center_frame.grid(row=0, column=1, sticky="nsew")

        _vs_ci = {"bg": "black", "activebackground": "#111111",
                  "activeforeground": "white", "bd": 0,
                  "font": ("Consolas", 8, "bold"), "cursor": "hand2",
                  "fg": "#00FFFF", "padx": 5}

        global vision_strike_btn
        vision_strike_btn = tk.Button(
            self.center_frame, text="[VS]",
            command=trigger_vision_strike, **_vs_ci)
        vision_strike_btn.pack(side=tk.LEFT, pady=4)

        # Center content: info label OR action buttons
        self.center_content = tk.Frame(self.center_frame, bg='black')
        self.center_content.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.info_label = tk.Label(
            self.center_content, text="SYSTEM ONLINE",
            fg="#555555", bg="black", font=("Consolas", 8, "bold"))
        self.info_label.pack(expand=True, pady=4)

        self.c_action_frame = tk.Frame(self.center_content, bg='black')
        self.c_btn_done = tk.Button(
            self.c_action_frame, text="[DONE]", fg="#00FF00",
            command=lambda: self.update_task("COMPLETED"), **_bs)
        self.c_btn_dismiss = tk.Button(
            self.c_action_frame, text="[DISMISS]", fg="#FF4444",
            command=lambda: self.update_task("DISMISSED"), **_bs)
        self.c_btn_skip = tk.Button(
            self.c_action_frame, text="[SKIP]", fg="#FFAA00",
            command=lambda: self.update_task("SKIPPED"), **_bs)

        # Bind center hover
        for w in (self.center_content, self.info_label):
            w.bind("<Enter>", self.on_center_hover)
            w.bind("<Leave>", self.on_center_leave)
        self.info_label.bind("<Button-1>", self.execute_suggestion)

        global clip_ingest_btn
        clip_ingest_btn = tk.Button(
            self.center_frame, text="[CI]",
            command=trigger_clip_ingest, **_vs_ci)
        clip_ingest_btn.pack(side=tk.RIGHT, pady=4)

        self.is_suggestion_active = False
        self.active_suggestion_command = None

        # ── RIGHT WING ────────────────────────────────────────
        self.right_frame = tk.Frame(self.root, bg='black')
        self.right_frame.grid(row=0, column=2, sticky="e", padx=(0, 10))

        self.btn_container = tk.Frame(self.right_frame, bg='black')
        self.btn_container.pack(side=tk.RIGHT)

        self.macro_trigger = tk.Label(
            self.btn_container, text="[+]", fg="#444444",
            bg="black", font=("Consolas", 9, "bold"), cursor="hand2")
        self.macro_trigger.pack(side=tk.RIGHT)

        self.btn1 = tk.Button(
            self.btn_container, text="W1",
            command=lambda: self.trigger_webhook("1"), **_bs)
        self.btn2 = tk.Button(
            self.btn_container, text="W2",
            command=lambda: self.trigger_webhook("2"), **_bs)
        self.btn3 = tk.Button(
            self.btn_container, text="W3",
            command=lambda: self.trigger_webhook("3"), **_bs)

        self.btn_container.bind("<Enter>", self.show_macro_buttons)
        self.btn_container.bind("<Leave>", self.hide_macro_buttons)

        # ── GLOBAL HOTKEY ─────────────────────────────────────
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.add_hotkey(
                    'ctrl+shift+windows+c',
                    self._hotkey_clip_ingest,
                    suppress=False)
                print("[NOTCH] Ctrl+Shift+Win+C registered.")
            except Exception as e:
                print(f"[NOTCH] Hotkey failed: {e}")

        self.root.after(2000, self.set_idle_suggestion)
        self.poll_voice_state()
        self.poll_left_status()

    # ── HOTKEY ────────────────────────────────────────────────
    def _hotkey_clip_ingest(self):
        """Copy highlighted text → run clip ingest."""
        try:
            keyboard.send('ctrl+c')
            time.sleep(0.25)
        except:
            pass
        self.root.after(0, trigger_clip_ingest)

    # ── APPBAR ────────────────────────────────────────────────
    def register_appbar(self):
        abd = APPBARDATA()
        abd.cbSize = ctypes.sizeof(APPBARDATA)
        abd.hWnd = self.hwnd
        abd.uEdge = ABE_TOP
        ctypes.windll.shell32.SHAppBarMessage(ABM_NEW, ctypes.byref(abd))
        abd.rc.left = 0
        abd.rc.top = 0
        abd.rc.right = self.screen_width
        abd.rc.bottom = self.notch_height
        ctypes.windll.shell32.SHAppBarMessage(ABM_QUERYPOS, ctypes.byref(abd))
        ctypes.windll.shell32.SHAppBarMessage(ABM_SETPOS, ctypes.byref(abd))

    def on_close(self, event=None):
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.remove_all_hotkeys()
            except:
                pass
        abd = APPBARDATA()
        abd.cbSize = ctypes.sizeof(APPBARDATA)
        abd.hWnd = self.hwnd
        ctypes.windll.shell32.SHAppBarMessage(ABM_REMOVE, ctypes.byref(abd))
        self.root.destroy()

    # ── LEFT BUTTONS ──────────────────────────────────────────
    def show_left_buttons(self, event=None):
        self.system_lbl.pack_forget()
        self.l_btn_done.pack(side=tk.LEFT, padx=2)
        self.l_btn_dismiss.pack(side=tk.LEFT, padx=2)
        self.l_btn_skip.pack(side=tk.LEFT, padx=2)

    def hide_left_buttons(self, event=None):
        x, y = self.root.winfo_pointerxy()
        w = self.root.winfo_containing(x, y)
        if w not in (self.task_container, self.system_lbl,
                     self.l_btn_done, self.l_btn_dismiss, self.l_btn_skip):
            self.l_btn_done.pack_forget()
            self.l_btn_dismiss.pack_forget()
            self.l_btn_skip.pack_forget()
            self.system_lbl.pack(side=tk.LEFT)

    def update_task(self, state):
        color = {"COMPLETED": "#00FF00", "DISMISSED": "#FF4444",
                 "SKIPPED": "#FFAA00"}.get(state, "#FFFFFF")
        self.task_text = state
        self.system_lbl.config(text=state, fg=color)
        self.update_info(f"MARKED: {state}", color)
        self.hide_left_buttons()
        self.hide_center_buttons()
        try:
            with open(self.state_file, "w") as f:
                json.dump({"status": state, "timestamp": time.time()}, f)
        except:
            pass

    # ── CENTER LOGIC ──────────────────────────────────────────
    def poll_voice_state(self):
        try:
            if os.path.exists(self.voice_state_file):
                with open(self.voice_state_file, "r") as f:
                    s = f.read().strip()
                colors = {"idle": "#555555", "listening": "#00FF00", "processing": "#0055FF"}
                self.status_dot.config(fg=colors.get(s, "#555555"))
        except:
            pass
        self.root.after(500, self.poll_voice_state)

    def poll_left_status(self):
        try:
            now = time.strftime("%H:%M")
            count = 0
            log = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bounty_log.csv")
            if os.path.exists(log):
                today = time.strftime("%Y-%m-%d", time.gmtime())
                with open(log, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith(today):
                            count += 1
            self.system_lbl.config(text=f"{now}  \u26a1{count}", fg="#666666")
        except Exception:
            pass
        self.root.after(30000, self.poll_left_status)

    def set_idle_suggestion(self):
        self.is_suggestion_active = True
        self.active_suggestion_command = "RUN_OSINT_SWEEP"
        self.info_label.config(
            text="💡 SWEEP JOBS $500+ [CLICK]", fg="#00FF00", cursor="hand2")

    def on_center_hover(self, event=None):
        if self.is_suggestion_active:
            return  # keep the clickable suggestion visible
        self.info_label.pack_forget()
        self.c_action_frame.pack(expand=True, fill=tk.BOTH)
        self.c_btn_done.pack(side=tk.LEFT, padx=4, pady=3)
        self.c_btn_dismiss.pack(side=tk.LEFT, padx=4, pady=3)
        self.c_btn_skip.pack(side=tk.LEFT, padx=4, pady=3)

    def on_center_leave(self, event=None):
        x, y = self.root.winfo_pointerxy()
        w = self.root.winfo_containing(x, y)
        if w not in (self.center_content, self.info_label, self.c_action_frame,
                     self.c_btn_done, self.c_btn_dismiss, self.c_btn_skip):
            self.hide_center_buttons()

    def hide_center_buttons(self):
        self.c_btn_done.pack_forget()
        self.c_btn_dismiss.pack_forget()
        self.c_btn_skip.pack_forget()
        self.c_action_frame.pack_forget()
        self.info_label.pack(expand=True, pady=4)

    def execute_suggestion(self, event=None):
        if not self.is_suggestion_active:
            return
        self.is_suggestion_active = False
        self.info_label.config(cursor="arrow")
        cmd = self.active_suggestion_command
        self.update_info(f"EXECUTING: {cmd}...", "#FFFF00")

        def run():
            try:
                if cmd == "RUN_OSINT_SWEEP":
                    import webbrowser
                    for u in (
                        "https://himalayas.app/jobs?q=data+cleaning&sort=recent",
                        "https://himalayas.app/jobs?q=notion+operations&sort=recent",
                        "https://jobspresso.co/remote-jobs/",
                    ):
                        webbrowser.open(u)
            except Exception as e:
                print(f"[HUD] suggestion fault: {e}")
        threading.Thread(target=run, daemon=True).start()
        self.root.after(3000, self.set_idle_suggestion)

    def update_info(self, text, color="#00FFFF"):
        self.is_suggestion_active = False
        self.hide_center_buttons()
        self.info_label.config(
            text=text.upper()[:55], fg=color, cursor="arrow")

    # ── WEBHOOKS ──────────────────────────────────────────────
    def trigger_clipboard(self):
        self.update_info("INGESTING...", "#FFFF00")
        def run():
            try:
                raw = pyperclip.paste().strip()
                if not raw:
                    self.root.after(0, lambda: self.update_info("CLIPBOARD EMPTY", "#FF4444"))
                    self.root.after(3000, self.set_idle_suggestion)
                    return
                llm = get_model()
                resp = llm.chat(
                    "You are N.E.O. Format the user's raw text into a concise, actionable summary.",
                    [{"role": "user", "content": f"Process:\n\n{raw}"}])
                pyperclip.copy(resp)
                self.root.after(0, lambda: self.update_info("INGESTED → CLIPBOARD", "#00FF00"))
                self.root.after(3000, self.set_idle_suggestion)
            except Exception as e:
                self.root.after(0, lambda: self.update_info(f"FAILED: {str(e)[:20]}", "#FF4444"))
                self.root.after(3000, self.set_idle_suggestion)
        threading.Thread(target=run, daemon=True).start()

    def trigger_webhook(self, num):
        urls = {
            "1": "https://trigger.macrodroid.com/ae0df50e-660f-4150-9f8e-4d67851614b7/Webhook1",
            "2": "https://trigger.macrodroid.com/ae0df50e-660f-4150-9f8e-4d67851614b7/Webhook2",
            "3": "https://trigger.macrodroid.com/ae0df50e-660f-4150-9f8e-4d67851614b7/Webhook3"
        }
        self.update_info(f"FIRING W{num}...", "#FFFF00")
        def fire():
            try:
                requests.get(urls[num], timeout=3)
                self.root.after(0, lambda: self.update_info(f"W{num} FIRED", "#00FF00"))
                self.root.after(3000, self.set_idle_suggestion)
            except:
                self.root.after(0, lambda: self.update_info(f"W{num} FAILED", "#FF4444"))
        threading.Thread(target=fire, daemon=True).start()

    # ── MACRO BUTTONS ─────────────────────────────────────────
    def show_macro_buttons(self, event=None):
        self.macro_trigger.pack_forget()
        self.btn3.pack(side=tk.RIGHT, padx=2)
        self.btn2.pack(side=tk.RIGHT, padx=2)
        self.btn1.pack(side=tk.RIGHT, padx=2)

    def hide_macro_buttons(self, event=None):
        x, y = self.root.winfo_pointerxy()
        w = self.root.winfo_containing(x, y)
        if w not in (self.btn_container, self.btn1, self.btn2, self.btn3, self.macro_trigger):
            self.btn1.pack_forget()
            self.btn2.pack_forget()
            self.btn3.pack_forget()
            self.macro_trigger.pack(side=tk.RIGHT)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    NeoNotch().run()