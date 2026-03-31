import tkinter as tk
from tkinter import messagebox
import json
import os
KEY_DISPLAY_NAMES = {
    "MEDIA_PREV": "上一曲",
    "MEDIA_PLAY": "播放",
    "MEDIA_STOP": "停止",
    "MEDIA_NEXT": "下一曲",
    "VOL_MUTE": "静音",
    "VOL_UP": "音量+",
    "VOL_DOWN": "音量-",
    "ESC": "Esc",
    "F1": "F1",
    "F2": "F2",
    "F3": "F3",
    "F4": "F4",
    "F5": "F5",
    "F6": "F6",
    "F7": "F7",
    "F8": "F8",
    "F9": "F9",
    "F10": "F10",
    "F11": "F11",
    "F12": "F12",
    "GRAVE": "`",
    "1": "1",
    "2": "2",
    "3": "3",
    "4": "4",
    "5": "5",
    "6": "6",
    "7": "7",
    "8": "8",
    "9": "9",
    "0": "0",
    "MINUS": "-",
    "EQUAL": "=",
    "BACK": "Backspace",
    "TAB": "Tab",
    "Q": "Q",
    "W": "W",
    "E": "E",
    "R": "R",
    "T": "T",
    "Y": "Y",
    "U": "U",
    "I": "I",
    "O": "O",
    "P": "P",
    "LBRACKET": "[",
    "RBRACKET": "]",
    "BACKSLASH": "\\",
    "CAPS": "Caps",
    "A": "A",
    "S": "S",
    "D": "D",
    "F": "F",
    "G": "G",
    "H": "H",
    "J": "J",
    "K": "K",
    "L": "L",
    "SEMICOLON": ";",
    "QUOTE": "'",
    "ENTER": "Enter",
    "SHIFT": "Shift",
    "Z": "Z",
    "X": "X",
    "C": "C",
    "V": "V",
    "B": "B",
    "N": "N",
    "M": "M",
    "COMMA": ",",
    "PERIOD": ".",
    "SLASH": "/",
    "CTRL": "Ctrl",
    "WIN": "Win",
    "ALT": "Alt",
    "SPACE": "Space",
    "MENU": "Menu",
    "UP": "↑",
    "DOWN": "↓",
    "LEFT": "←",
    "RIGHT": "→",
    "PRTSC": "PrtSc",
    "SCRLOCK": "ScrLk",
    "PAUSE": "Pause",
    "INS": "Ins",
    "HOME": "Home",
    "PGUP": "PgUp",
    "DEL": "Del",
    "END": "End",
    "PGDN": "PgDn",
    "NUMLOCK": "Num",
    "NUM/": "/",
    "NUM*": "*",
    "NUM-": "-",
    "NUM7": "7",
    "NUM8": "8",
    "NUM9": "9",
    "NUM5": "5",
    "NUM6": "6",
    "NUM3": "3",
    "NUM+": "+",
    "NUM2": "2",
    "NUM1": "1",
    "NUM0": "0",
    "NUM.": "."
}
class VirtualKeyboard(tk.Toplevel):
    def __init__(self, parent, callback, current_key=""):
        super().__init__(parent)
        self.title("选择按键")
        self.geometry("1000x400")
        self.resizable(False, False)
        self.callback = callback
        self.selected_key = None
        self.cell_width = 35
        self.cell_height = 35
        self.gap = 2
        self.combo_mode = False
        self.combo_keys = []
        if ' + ' in current_key:
            self.combo_keys = [k.strip() for k in current_key.split(' + ')]
            self.combo_mode = True
        elif current_key:
            self.combo_keys = [current_key]
        self.create_keyboard()
        if self.combo_mode:
            self.combo_button.config(relief="sunken", text="组合键模式")
            self.update_combo_entry()
        self.transient(parent)
        self.grab_set()
        self.focus_set()
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    def create_keyboard(self):
        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.create_media_keys(main_frame)
        self.create_function_keys(main_frame)
        self.create_number_keys(main_frame)
        self.create_q_row(main_frame)
        self.create_a_row(main_frame)
        self.create_z_row(main_frame)
        self.create_ctrl_row(main_frame)
        self.create_numpad(main_frame)
        self.create_direction_keys(main_frame)
        self.create_combo_key_area(main_frame)
    def create_button(self, parent, text, code, row, col, rowspan=1, colspan=1):
        width = self.cell_width * colspan + self.gap * (colspan - 1)
        height = self.cell_height * rowspan + self.gap * (rowspan - 1)
        x = col * (self.cell_width + self.gap)
        y = row * (self.cell_height + self.gap)
        btn = tk.Button(
            parent,
            text=text,
            font=("Arial", 8),
            relief="raised",
            bd=2
        )
        btn.place(x=x, y=y, width=width, height=height)
        if code:
            btn.config(command=lambda k=code: self.on_key_click(k))
        return btn
    def create_media_keys(self, parent):
        frame = tk.Frame(parent, width=910, height=40)
        frame.place(x=0, y=0)
        frame.pack_propagate(False)
        media_keys = [
            ("上一曲", "MEDIA_PREV", 0), ("快退", "MEDIA_PLAY", 1), ("播放", "MEDIA_PLAY", 2),
            ("停止", "MEDIA_STOP", 3), ("快进", "MEDIA_NEXT", 4), ("下一曲", "MEDIA_NEXT", 5),
            ("静音", "VOL_MUTE", 6), ("音量+", "VOL_UP", 7), ("音量-", "VOL_DOWN", 8)
        ]
        for text, code, col in media_keys:
            self.create_button(frame, text, code, 0, col)
        volume_minus_x = 8 * (35 + 2)
        prtsc_x = volume_minus_x + 35 + 132
        edit_keys = [
            ("PrtSc", "PRTSC"), ("ScrLk", "SCRLOCK"), ("Pause", "PAUSE"),
            ("Ins", "INS"), ("Home", "HOME"), ("PgUp", "PGUP"),
            ("Del", "DEL"), ("End", "END"), ("PgDn", "PGDN")
        ]
        current_x = prtsc_x
        for text, code in edit_keys:
            btn = tk.Button(
                frame,
                text=text,
                font=("Arial", 8),
                relief="raised",
                bd=2,
                command=lambda k=code: self.on_key_click(k)
            )
            btn.place(x=current_x, y=0, width=35, height=35)
            current_x += 35 + 2
    def create_function_keys(self, parent):
        frame = tk.Frame(parent, width=910, height=40)
        frame.place(x=0, y=45)
        frame.pack_propagate(False)
        self.create_button(frame, "Esc", "ESC", 0, 0)
        func_keys_1 = [
            ("F1", "F1", 2), ("F2", "F2", 3), ("F3", "F3", 4), ("F4", "F4", 5)
        ]
        for text, code, col in func_keys_1:
            self.create_button(frame, text, code, 0, col)
        func_keys_2 = [
            ("F5", "F5", 7), ("F6", "F6", 8), ("F7", "F7", 9), ("F8", "F8", 10)
        ]
        for text, code, col in func_keys_2:
            self.create_button(frame, text, code, 0, col)
        func_keys_3 = [
            ("F9", "F9", 12), ("F10", "F10", 13), ("F11", "F11", 14), ("F12", "F12", 15)
        ]
        for text, code, col in func_keys_3:
            self.create_button(frame, text, code, 0, col)
    def create_number_keys(self, parent):
        frame = tk.Frame(parent, width=910, height=40)
        frame.place(x=0, y=90)
        frame.pack_propagate(False)
        num_keys = [
            ("`", "GRAVE", 0), ("1", "1", 1), ("2", "2", 2), ("3", "3", 3),
            ("4", "4", 4), ("5", "5", 5), ("6", "6", 6), ("7", "7", 7),
            ("8", "8", 8), ("9", "9", 9), ("0", "0", 10), ("-", "MINUS", 11),
            ("=", "EQUAL", 12)
        ]
        for text, code, col in num_keys:
            self.create_button(frame, text, code, 0, col)
        self.create_button(frame, "Backspace", "BACK", 0, 13, colspan=3)
    def create_q_row(self, parent):
        frame = tk.Frame(parent, width=910, height=40)
        frame.place(x=0, y=135)
        frame.pack_propagate(False)
        self.create_button(frame, "Tab", "TAB", 0, 0, colspan=3)
        q_keys = [
            ("Q", "Q", 3), ("W", "W", 4), ("E", "E", 5), ("R", "R", 6),
            ("T", "T", 7), ("Y", "Y", 8), ("U", "U", 9), ("I", "I", 10),
            ("O", "O", 11), ("P", "P", 12), ("[", "LBRACKET", 13),
            ("]", "RBRACKET", 14), ("\\", "BACKSLASH", 15)
        ]
        for text, code, col in q_keys:
            self.create_button(frame, text, code, 0, col)
    def create_a_row(self, parent):
        frame = tk.Frame(parent, width=910, height=40)
        frame.place(x=0, y=180)
        frame.pack_propagate(False)
        self.create_button(frame, "Caps", "CAPS", 0, 0, colspan=3)
        a_keys = [
            ("A", "A", 3), ("S", "S", 4), ("D", "D", 5), ("F", "F", 6),
            ("G", "G", 7), ("H", "H", 8), ("J", "J", 9), ("K", "K", 10),
            ("L", "L", 11), (";", "SEMICOLON", 12), ("'", "QUOTE", 13)
        ]
        for text, code, col in a_keys:
            self.create_button(frame, text, code, 0, col)
        self.create_button(frame, "Enter", "ENTER", 0, 14, colspan=2)
    def create_z_row(self, parent):
        frame = tk.Frame(parent, width=910, height=40)
        frame.place(x=0, y=225)
        frame.pack_propagate(False)
        self.create_button(frame, "Shift", "SHIFT", 0, 0, colspan=3)
        z_keys = [
            ("Z", "Z", 3), ("X", "X", 4), ("C", "C", 5), ("V", "V", 6),
            ("B", "B", 7), ("N", "N", 8), ("M", "M", 9), (",", "COMMA", 10),
            (".", "PERIOD", 11), ("/", "SLASH", 12)
        ]
        for text, code, col in z_keys:
            self.create_button(frame, text, code, 0, col)
        self.create_button(frame, "Shift", "SHIFT", 0, 13, colspan=3)
    def create_ctrl_row(self, parent):
        frame = tk.Frame(parent, width=910, height=40)
        frame.place(x=0, y=270)
        frame.pack_propagate(False)
        self.create_button(frame, "Ctrl", "CTRL", 0, 0, colspan=2)
        self.create_button(frame, "Win", "WIN", 0, 2)
        self.create_button(frame, "Alt", "ALT", 0, 3)
        self.create_button(frame, "Space", "SPACE", 0, 4, colspan=6)
        self.create_button(frame, "Alt", "ALT", 0, 10)
        self.create_button(frame, "Win", "WIN", 0, 11)
        self.create_button(frame, "Menu", "MENU", 0, 12, colspan=2)
        self.create_button(frame, "Ctrl", "CTRL", 0, 14, colspan=2)
    def create_numpad(self, parent):
        frame = tk.Frame(parent, width=200, height=200)
        frame.place(x=650, y=45)
        frame.pack_propagate(False)
        self.create_button(frame, "Num", "NUMLOCK", 0, 0)
        self.create_button(frame, "/", "NUM/", 0, 1)
        self.create_button(frame, "*", "NUM*", 0, 2)
        self.create_button(frame, "-", "NUM-", 0, 3)
        self.create_button(frame, "7", "NUM7", 1, 0)
        self.create_button(frame, "8", "NUM8", 1, 1)
        self.create_button(frame, "9", "NUM9", 1, 2)
        self.create_button(frame, "+", "NUM+", 1, 3, rowspan=2)
        self.create_button(frame, "4", "NUM4", 2, 0)
        self.create_button(frame, "5", "NUM5", 2, 1)
        self.create_button(frame, "6", "NUM6", 2, 2)
        self.create_button(frame, "1", "NUM1", 3, 0)
        self.create_button(frame, "2", "NUM2", 3, 1)
        self.create_button(frame, "3", "NUM3", 3, 2)
        self.create_button(frame, "Enter", "ENTER", 3, 3, rowspan=2)
        self.create_button(frame, "0", "NUM0", 4, 0, colspan=2)
        self.create_button(frame, ".", "NUM.", 4, 2)
    def create_direction_keys(self, parent):
        frame = tk.Frame(parent, width=150, height=72)
        frame.place(x=687, y=240)
        frame.pack_propagate(False)
        self.create_button(frame, "↑", "UP", 0, 1)
        self.create_button(frame, "←", "LEFT", 1, 0)
        self.create_button(frame, "↓", "DOWN", 1, 1)
        self.create_button(frame, "→", "RIGHT", 1, 2)
    def on_key_click(self, key):
        if self.combo_mode:
            self.combo_keys.append(key)
            self.update_combo_entry()
        else:
            self.selected_key = key
            if self.callback:
                self.callback(key)
            self.destroy()
    def create_combo_key_area(self, parent):
        frame = tk.Frame(parent, width=910, height=60)
        frame.place(x=0, y=320)
        frame.pack_propagate(False)
        self.combo_button = tk.Button(
            frame, 
            text="组合键", 
            font=("Arial", 10),
            relief="raised",
            bd=2,
            command=self.toggle_combo_mode
        )
        self.combo_button.place(x=10, y=15, width=80, height=30)
        self.combo_entry = tk.Entry(frame, font=("Arial", 10), width=40)
        self.combo_entry.place(x=100, y=15, height=30)
        backspace_button = tk.Button(
            frame, 
            text="回删", 
            font=("Arial", 10),
            relief="raised",
            bd=2,
            command=self.delete_last_combo_key
        )
        backspace_button.place(x=380, y=15, width=60, height=30)
        save_button = tk.Button(
            frame, 
            text="保存按键方案", 
            font=("Arial", 10),
            relief="raised",
            bd=2,
            command=self.save_key_scheme
        )
        save_button.place(x=450, y=15, width=120, height=30)
    def toggle_combo_mode(self):
        self.combo_mode = not self.combo_mode
        if self.combo_mode:
            self.combo_button.config(relief="sunken", text="组合键模式")
            self.combo_keys = []
            self.combo_entry.delete(0, tk.END)
        else:
            self.combo_button.config(relief="raised", text="组合键")
    def update_combo_entry(self):
        combo_text = " + ".join(self.combo_keys)
        self.combo_entry.delete(0, tk.END)
        self.combo_entry.insert(0, combo_text)
    def delete_last_combo_key(self):
        if self.combo_keys:
            self.combo_keys.pop()
            self.update_combo_entry()
    def save_key_scheme(self):
        combo_text = " + ".join(self.combo_keys)
        scheme = {
            "combo_keys": self.combo_keys,
            "combo_text": combo_text
        }
        scheme_file = "按键方案.json"
        with open(scheme_file, "w", encoding="utf-8") as f:
            json.dump(scheme, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("保存成功", f"按键方案已保存到 {scheme_file}")
        if self.callback:
            self.callback(combo_text)
        self.destroy()
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    def on_key_selected(key):
        root.destroy()
    keyboard = VirtualKeyboard(root, on_key_selected)
    root.mainloop()
