"""
游戏手柄触屏映射工具

功能说明:
- 将游戏手柄按键映射为屏幕触摸操作
- 支持点击、长按、滑动、滚动等多种操作
- 支持摇杆作为方向键、模拟摇杆或鼠标模式
- 可配置屏幕坐标或窗口相对坐标
- 支持多窗口切换和目标窗口自动激活

作者: sblyao
版本: 1.0
"""

import ctypes
import time
import tkinter as tk
from tkinter import ttk, messagebox
from inputs import get_gamepad
import json
import os
import threading
import queue
from PIL import Image, ImageDraw
import pystray


class TOUCHINPUT(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_long),
        ("y", ctypes.c_long),
        ("hSource", ctypes.c_void_p),
        ("dwID", ctypes.c_uint),
        ("dwFlags", ctypes.c_uint),
        ("dwMask", ctypes.c_uint),
        ("dwTime", ctypes.c_uint),
        ("dwExtraInfo", ctypes.c_size_t),
        ("cxContact", ctypes.c_uint),
        ("cyContact", ctypes.c_uint)
    ]


TOUCH_DOWN = 0x0002
TOUCH_MOVE = 0x0001
TOUCH_UP = 0x0004


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_uint),
        ("dwFlags", ctypes.c_uint),
        ("time", ctypes.c_uint),
        ("dwExtraInfo", ctypes.c_void_p)
    ]


class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [
            ("mi", MOUSEINPUT),
            ("ki", ctypes.c_ubyte * 28),
            ("hi", ctypes.c_ubyte * 8)
        ]
    _anonymous_ = ("u",)
    _fields_ = [
        ("type", ctypes.c_uint),
        ("u", _INPUT)
    ]


INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_WHEEL = 0x0800
WHEEL_DELTA = 120


def send_mouse_click(x, y):
    screen_width = ctypes.windll.user32.GetSystemMetrics(0)
    screen_height = ctypes.windll.user32.GetSystemMetrics(1)
    
    absolute_x = int(x * 65535 / screen_width)
    absolute_y = int(y * 65535 / screen_height)
    
    input_events = (INPUT * 3)()
    
    input_events[0].type = INPUT_MOUSE
    input_events[0].mi.dx = absolute_x
    input_events[0].mi.dy = absolute_y
    input_events[0].mi.mouseData = 0
    input_events[0].mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
    input_events[0].mi.time = 0
    input_events[0].mi.dwExtraInfo = None
    
    input_events[1].type = INPUT_MOUSE
    input_events[1].mi.dx = 0
    input_events[1].mi.dy = 0
    input_events[1].mi.mouseData = 0
    input_events[1].mi.dwFlags = MOUSEEVENTF_LEFTDOWN
    input_events[1].mi.time = 0
    input_events[1].mi.dwExtraInfo = None
    
    input_events[2].type = INPUT_MOUSE
    input_events[2].mi.dx = 0
    input_events[2].mi.dy = 0
    input_events[2].mi.mouseData = 0
    input_events[2].mi.dwFlags = MOUSEEVENTF_LEFTUP
    input_events[2].mi.time = 0
    input_events[2].mi.dwExtraInfo = None
    
    ctypes.windll.user32.SendInput(3, input_events, ctypes.sizeof(INPUT))


def touch_click(x, y):
    send_mouse_click(x, y)


def touch_long_press_start(x, y):
    screen_width = ctypes.windll.user32.GetSystemMetrics(0)
    screen_height = ctypes.windll.user32.GetSystemMetrics(1)
    
    absolute_x = int(x * 65535 / screen_width)
    absolute_y = int(y * 65535 / screen_height)
    
    input_events = (INPUT * 2)()
    
    input_events[0].type = INPUT_MOUSE
    input_events[0].mi.dx = absolute_x
    input_events[0].mi.dy = absolute_y
    input_events[0].mi.mouseData = 0
    input_events[0].mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
    input_events[0].mi.time = 0
    input_events[0].mi.dwExtraInfo = None
    
    input_events[1].type = INPUT_MOUSE
    input_events[1].mi.dx = 0
    input_events[1].mi.dy = 0
    input_events[1].mi.mouseData = 0
    input_events[1].mi.dwFlags = MOUSEEVENTF_LEFTDOWN
    input_events[1].mi.time = 0
    input_events[1].mi.dwExtraInfo = None
    
    ctypes.windll.user32.SendInput(2, input_events, ctypes.sizeof(INPUT))


def touch_long_press_end():
    release_event = INPUT()
    release_event.type = INPUT_MOUSE
    release_event.mi.dx = 0
    release_event.mi.dy = 0
    release_event.mi.mouseData = 0
    release_event.mi.dwFlags = MOUSEEVENTF_LEFTUP
    release_event.mi.time = 0
    release_event.mi.dwExtraInfo = None
    
    ctypes.windll.user32.SendInput(1, ctypes.byref(release_event), ctypes.sizeof(INPUT))


def touch_long_press(x, y, duration=0.5):
    touch_long_press_start(x, y)
    time.sleep(duration)
    touch_long_press_end()


def touch_scroll_up(x, y, steps=10):
    touch_scroll(x, y, steps, is_up=True)


def touch_scroll_down(x, y, steps=10):
    touch_scroll(x, y, steps, is_up=False)


def touch_scroll(x, y, steps=3, is_up=True):
    screen_width = ctypes.windll.user32.GetSystemMetrics(0)
    screen_height = ctypes.windll.user32.GetSystemMetrics(1)
    
    absolute_x = int(x * 65535 / screen_width)
    absolute_y = int(y * 65535 / screen_height)
    
    move_event = INPUT()
    move_event.type = INPUT_MOUSE
    move_event.mi.dx = absolute_x
    move_event.mi.dy = absolute_y
    move_event.mi.mouseData = 0
    move_event.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
    move_event.mi.time = 0
    move_event.mi.dwExtraInfo = None
    
    result1 = ctypes.windll.user32.SendInput(1, ctypes.byref(move_event), ctypes.sizeof(INPUT))
    
    for i in range(steps):
        scroll_event = INPUT()
        scroll_event.type = INPUT_MOUSE
        scroll_event.mi.dx = 0
        scroll_event.mi.dy = 0
        scroll_event.mi.mouseData = WHEEL_DELTA if is_up else -WHEEL_DELTA
        scroll_event.mi.dwFlags = MOUSEEVENTF_WHEEL
        scroll_event.mi.time = 0
        scroll_event.mi.dwExtraInfo = None
        
        ctypes.windll.user32.SendInput(1, ctypes.byref(scroll_event), ctypes.sizeof(INPUT))


def touch_swipe(x1, y1, x2, y2, duration=0.2):
    pass


BUTTONS = [
    "BTN_SOUTH", "BTN_EAST", "BTN_NORTH", "BTN_WEST",
    "BTN_TL", "BTN_TR", "BTN_SELECT", "BTN_START",
    "BTN_THUMBL", "BTN_THUMBR", "ABS_HAT0U", "ABS_HAT0D",
    "ABS_HAT0L", "ABS_HAT0R", "ABS_Z", "ABS_RZ",
    "ABS_LEFT_STICK", "ABS_RIGHT_STICK"
]

BUTTON_NAMES = {
    "BTN_SOUTH": "A键", "BTN_EAST": "B键", "BTN_NORTH": "Y键", "BTN_WEST": "X键",
    "BTN_TL": "LB", "BTN_TR": "RB", "BTN_SELECT": "Back", "BTN_START": "Start",
    "BTN_THUMBL": "L3", "BTN_THUMBR": "R3", "ABS_HAT0U": "十字上", "ABS_HAT0D": "十字下",
    "ABS_HAT0L": "十字左", "ABS_HAT0R": "十字右", "ABS_Z": "LT", "ABS_RZ": "RT",
    "ABS_LEFT_STICK": "左摇杆", "ABS_RIGHT_STICK": "右摇杆"
}

CONFIG_FILE = "gamepad_config.json"


def load_config():
    default_config = {btn: {"screen_x": "", "screen_y": "", "window_x": "", "window_y": "", "func": "点击"} for btn in BUTTONS}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            saved_config = json.load(f)
            for btn in BUTTONS:
                if btn not in saved_config:
                    saved_config[btn] = default_config[btn]
                elif "x" in saved_config[btn]:
                    saved_config[btn]["screen_x"] = saved_config[btn]["x"]
                    saved_config[btn]["screen_y"] = saved_config[btn]["y"]
                    saved_config[btn]["window_x"] = saved_config[btn]["x"]
                    saved_config[btn]["window_y"] = saved_config[btn]["y"]
            return saved_config
    return default_config


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    messagebox.showinfo("保存", "配置已保存！")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("手柄触屏映射工具")
        self.geometry("1100x700")
        self.minsize(1000, 650)
        self.gamepad_config = load_config()
        
        self.highlight_queue = queue.Queue()
        self.processing_highlights = False
        self.button_states = {}
        self.current_capture_btn = None
        self.mapping_mode = False
        self.stick_mouse_thread = None
        self.stick_mouse_running = False
        self.last_left_stick_state = {"x": 0, "y": 0, "active": False}
        self.last_right_stick_state = {"x": 0, "y": 0, "active": False}

        ttk.Label(self, text="手柄按键 → 触屏映射", font=("黑体", 16, "bold")).pack(pady=10)

        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)

        left_frame = ttk.LabelFrame(main_frame, text="控制中心")
        left_frame.pack(side="left", fill="x", padx=5)

        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        profile_frame = ttk.LabelFrame(control_frame, text="方案管理")
        profile_frame.pack(side="left", padx=5, fill="x", expand=True)
        
        ttk.Label(profile_frame, text="当前:").pack(side="left", padx=3)
        self.profile_var = tk.StringVar(value="默认方案")
        self.profile_combo = ttk.Combobox(profile_frame, values=["默认方案"], width=12, textvariable=self.profile_var, state="readonly")
        self.profile_combo.pack(side="left", padx=3)
        ttk.Button(profile_frame, text="新建", width=5, command=self.new_profile).pack(side="left", padx=2)
        ttk.Button(profile_frame, text="删除", width=5, command=self.delete_profile).pack(side="left", padx=2)
        
        window_frame = ttk.LabelFrame(control_frame, text="目标窗口")
        window_frame.pack(side="left", padx=5, fill="x", expand=True)
        
        self.window_var = tk.StringVar(value="整个屏幕")
        self.window_combo = ttk.Combobox(window_frame, values=["整个屏幕"], width=20, textvariable=self.window_var, state="readonly")
        self.window_combo.pack(side="left", padx=3)
        ttk.Button(window_frame, text="刷新", width=5, command=self.refresh_windows).pack(side="left", padx=2)

        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(button_frame, text="检测手柄", width=10, command=self.test_gamepad).pack(side="left", padx=5)
        ttk.Button(button_frame, text="保存配置", width=10, command=self.save).pack(side="left", padx=5)
        
        self.start_mapping_btn = tk.Button(button_frame, text="▶ 启动映射", width=10, command=self.start_mapping, 
                                   bg="#4CAF50", fg="white", font=("Arial", 9, "bold"),
                                   activebackground="#45a049", activeforeground="white")
        self.start_mapping_btn.pack(side="left", padx=5)
        
        self.stop_mapping_btn = tk.Button(button_frame, text="⏹ 停止映射", width=10, command=self.stop_mapping, 
                                   bg="#f44336", fg="white", font=("Arial", 9, "bold"),
                                   activebackground="#da190b", activeforeground="white",
                                   state="disabled")
        self.stop_mapping_btn.pack(side="left", padx=5)

        gamepad_frame = ttk.LabelFrame(left_frame, text="手柄布局")
        gamepad_frame.pack(fill="x", padx=5, pady=5)

        self.gamepad_canvas = tk.Canvas(gamepad_frame, width=280, height=220, bg="#f0f0f0")
        self.gamepad_canvas.pack(fill="x", expand=False, padx=5, pady=5)

        self.draw_gamepad_background()

        status_frame = ttk.LabelFrame(left_frame, text="状态信息")
        status_frame.pack(fill="x", padx=5, pady=5)
        
        self.gamepad_status_label = ttk.Label(status_frame, text="手柄: 未连接", foreground="gray")
        self.gamepad_status_label.pack(anchor="w", padx=10, pady=2)
        
        self.mapping_status_label = ttk.Label(status_frame, text="映射: 未启动", foreground="gray")
        self.mapping_status_label.pack(anchor="w", padx=10, pady=2)
        
        self.config_info_label = ttk.Label(status_frame, text="配置: 默认", foreground="gray")
        self.config_info_label.pack(anchor="w", padx=10, pady=2)

        right_frame = ttk.LabelFrame(main_frame, text="按键配置")
        right_frame.pack(side="right", fill="both", expand=True, padx=5)

        canvas = tk.Canvas(right_frame)
        scroll = ttk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        ttk.Label(scroll_frame, text="按键", width=8, font=("黑体", 9, "bold")).grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(scroll_frame, text="屏幕坐标", width=10, font=("黑体", 9, "bold")).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(scroll_frame, text="窗口坐标", width=10, font=("黑体", 9, "bold")).grid(row=0, column=2, padx=5, pady=5)
        ttk.Label(scroll_frame, text="功能", width=6, font=("黑体", 9, "bold")).grid(row=0, column=3, padx=5, pady=5)

        self.entries = {}
        self.labels = {}
        self.button_widgets = {}

        for i, btn in enumerate(BUTTONS, 1):
            display_name = BUTTON_NAMES.get(btn, btn)
            label = tk.Label(scroll_frame, text=display_name, width=8, bg="white", cursor="hand2", font=("Arial", 8))
            label.grid(row=i, column=0, padx=5, pady=2)
            label.bind("<Button-1>", lambda e, b=btn: self.start_coordinate_capture(b))
            self.labels[btn] = label

            screen_entry = ttk.Entry(scroll_frame, width=12)
            screen_entry.grid(row=i, column=1, padx=5, pady=2)
            screen_x = self.gamepad_config[btn].get("screen_x", self.gamepad_config[btn].get("x", ""))
            screen_y = self.gamepad_config[btn].get("screen_y", self.gamepad_config[btn].get("y", ""))
            screen_entry.insert(0, f"{screen_x},{screen_y}")

            window_entry = ttk.Entry(scroll_frame, width=12)
            window_entry.grid(row=i, column=2, padx=5, pady=2)
            window_x = self.gamepad_config[btn].get("window_x", self.gamepad_config[btn].get("x", ""))
            window_y = self.gamepad_config[btn].get("window_y", self.gamepad_config[btn].get("y", ""))
            window_entry.insert(0, f"{window_x},{window_y}")

            if btn in ["ABS_LEFT_STICK", "ABS_RIGHT_STICK"]:
                func_var = tk.StringVar(value=self.gamepad_config[btn].get("func", "方向键"))
                func_combo = ttk.Combobox(scroll_frame, values=["方向键", "摇杆", "鼠标"], width=8, textvariable=func_var, state="readonly")
            else:
                func_var = tk.StringVar(value=self.gamepad_config[btn]["func"])
                func_combo = ttk.Combobox(scroll_frame, values=["点击", "长按", "上滑", "下滑"], width=8, textvariable=func_var, state="readonly")
            func_combo.grid(row=i, column=3, padx=5, pady=2)

            self.entries[btn] = (screen_entry, window_entry, func_var)

        self.create_gamepad_buttons()

        self.status_label = ttk.Label(self, text="状态: 正在监听手柄按键...", foreground="green")
        self.status_label.pack(pady=5)
        
        self.refresh_windows()
        self.after(100, self.start_gamepad_listener)

    def draw_gamepad_background(self):
        c = self.gamepad_canvas
        body_color = "#e8e8e8"
        grip_color = "#dcdcdc"
        outline_color = "#b0b0b0"
        
        scale = 0.45
        
        c.create_polygon(60*scale, 180*scale, 30*scale, 280*scale, 50*scale, 450*scale, 
                        100*scale, 480*scale, 140*scale, 450*scale, 150*scale, 350*scale, 
                        140*scale, 250*scale, 120*scale, 180*scale,
                        fill=grip_color, outline=outline_color, width=1, smooth=True)
        c.create_polygon(420*scale, 180*scale, 450*scale, 280*scale, 430*scale, 450*scale, 
                        380*scale, 480*scale, 340*scale, 450*scale, 330*scale, 350*scale, 
                        340*scale, 250*scale, 360*scale, 180*scale,
                        fill=grip_color, outline=outline_color, width=1, smooth=True)
        c.create_polygon(80*scale, 100*scale, 400*scale, 100*scale, 420*scale, 150*scale, 
                        420*scale, 300*scale, 400*scale, 380*scale, 240*scale, 400*scale, 
                        80*scale, 380*scale, 60*scale, 300*scale, 60*scale, 150*scale,
                        fill=body_color, outline=outline_color, width=1, smooth=True)
        
        c.create_oval(135, 65, 165, 95, fill="#ffffff", outline="#107c10", width=1)
        c.create_text(150, 80, text="X", font=("Arial", 10, "bold"), fill="#107c10")

    def create_gamepad_buttons(self):
        c = self.gamepad_canvas
        scale = 0.45
        
        button_configs = {
            "ABS_HAT0U": (130*scale, 140*scale, "▲"), "ABS_HAT0D": (130*scale, 200*scale, "▼"),
            "ABS_HAT0L": (100*scale, 170*scale, "◀"), "ABS_HAT0R": (160*scale, 170*scale, "▶"),
            "BTN_THUMBL": (160*scale, 280*scale, "L3"), "ABS_LEFT_STICK": (160*scale, 280*scale, ""),
            "BTN_NORTH": (350*scale, 130*scale, "Y"), "BTN_SOUTH": (350*scale, 190*scale, "A"),
            "BTN_WEST": (320*scale, 160*scale, "X"), "BTN_EAST": (380*scale, 160*scale, "B"),
            "BTN_THUMBR": (340*scale, 280*scale, "R3"), "ABS_RIGHT_STICK": (340*scale, 280*scale, ""),
            "BTN_TL": (90*scale, 70*scale, "LB"), "BTN_TR": (390*scale, 70*scale, "RB"),
            "ABS_Z": (130*scale, 50*scale, "LT"), "ABS_RZ": (350*scale, 50*scale, "RT"),
            "BTN_START": (190*scale, 240*scale, "Back"), "BTN_SELECT": (310*scale, 240*scale, "Start"),
        }
        
        xbox_colors = {"Y": "#FFD700", "A": "#32CD32", "X": "#4169E1", "B": "#DC143C"}
        
        for btn, (x, y, text) in button_configs.items():
            if btn in ["ABS_HAT0U", "ABS_HAT0D", "ABS_HAT0L", "ABS_HAT0R"]:
                widget = c.create_rectangle(x-8, y-8, x+8, y+8, fill="#505050", outline="#303030", width=1, tags=btn)
            elif btn in ["BTN_SOUTH", "BTN_EAST", "BTN_WEST", "BTN_NORTH"]:
                color = xbox_colors[text]
                c.create_oval(x-10, y-10, x+10, y+10, fill="#404040", outline="", tags=f"{btn}_shadow")
                widget = c.create_oval(x-8, y-8, x+8, y+8, fill=color, outline="#202020", width=1, tags=btn)
            elif "THUMB" in btn:
                c.create_oval(x-15, y-15, x+15, y+15, fill="#404040", outline="#202020", width=1, tags=f"{btn}_base")
                widget = c.create_oval(x-12, y-12, x+12, y+12, fill="#606060", outline="#404040", width=1, tags=btn)
            elif btn in ["ABS_LEFT_STICK", "ABS_RIGHT_STICK"]:
                widget = c.create_oval(x-18, y-18, x+18, y+18, fill="", outline="#FFA500", width=2, tags=btn, state="hidden")
                self.button_widgets[btn] = (widget, None)
                continue
            else:
                widget = c.create_oval(x-10, y-10, x+10, y+10, fill="#b0b0b0", outline="#808080", width=1, tags=btn)
            
            if text:
                text_color = "#ffffff" if btn in ["ABS_HAT0U", "ABS_HAT0D", "ABS_HAT0L", "ABS_HAT0R", "BTN_SOUTH", "BTN_EAST", "BTN_WEST", "BTN_NORTH"] else "#333333"
                text_widget = c.create_text(x, y, text=text, font=("Arial", 5, "bold"), fill=text_color, tags=f"{btn}_text")
                self.button_widgets[btn] = (widget, text_widget)
            else:
                self.button_widgets[btn] = (widget, None)

    def test_gamepad(self):
        self.status_label.config(text="状态: 正在检测手柄...", foreground="blue")
        try:
            events = get_gamepad()
            self.status_label.config(text="状态: 手柄已连接", foreground="green")
            messagebox.showinfo("手柄检测", "手柄检测成功！请按下手柄按键测试")
        except Exception as e:
            self.status_label.config(text="状态: 未检测到手柄", foreground="red")
            messagebox.showerror("手柄检测失败", f"无法检测到手柄错误信息: {e}")

    def save(self):
        new_config = {}
        for btn, (screen_entry, window_entry, func) in self.entries.items():
            screen_coords = screen_entry.get().split(',')
            if len(screen_coords) == 2:
                screen_x = screen_coords[0].strip()
                screen_y = screen_coords[1].strip()
            else:
                screen_x = "0"
                screen_y = "0"
            
            window_coords = window_entry.get().split(',')
            if len(window_coords) == 2:
                window_x = window_coords[0].strip()
                window_y = window_coords[1].strip()
            else:
                window_x = "0"
                window_y = "0"
            
            new_config[btn] = {
                "screen_x": screen_x, 
                "screen_y": screen_y, 
                "window_x": window_x, 
                "window_y": window_y, 
                "func": func.get()
            }
        save_config(new_config)
        self.gamepad_config = new_config
        self.config_info_label.config(text="配置: 已保存", foreground="green")

    def start_gamepad_listener(self):
        self.listening = True
        self.listener_thread = threading.Thread(target=self.gamepad_listener, daemon=True)
        self.listener_thread.start()
        self.process_highlight_queue()

    def gamepad_listener(self):
        try:
            get_gamepad()
            self.gamepad_status_label.config(text="手柄: 已连接", foreground="green")
        except:
            self.gamepad_status_label.config(text="手柄: 未连接", foreground="red")
            return
        
        long_press_buttons = {}
        left_stick = {"x": 0, "y": 0, "active": False}
        right_stick = {"x": 0, "y": 0, "active": False}
        last_left_stick = {"x": 0, "y": 0, "active": False}
        last_right_stick = {"x": 0, "y": 0, "active": False}
        
        while self.listening:
            try:
                events = get_gamepad()
                for event in events:
                    if event.code in ["ABS_X", "ABS_Y", "ABS_RX", "ABS_RY"]:
                        self.process_stick_event(event, left_stick, right_stick)
                        continue
                    
                    btn, pressed = self.parse_event(event)
                    if btn:
                        self.highlight_queue.put((btn, pressed))
                        
                        if self.mapping_mode:
                            if btn in self.gamepad_config:
                                cfg = self.gamepad_config[btn]
                                func = cfg.get("func", "点击")
                                
                                if btn in ["ABS_LEFT_STICK", "ABS_RIGHT_STICK"]:
                                    continue
                                
                                if pressed:
                                    if func == "长按":
                                        long_press_buttons[btn] = True
                                        self.execute_touch_start(cfg)
                                    else:
                                        self.execute_touch(cfg)
                                else:
                                    if func == "长按" and btn in long_press_buttons:
                                        del long_press_buttons[btn]
                                        touch_long_press_end()
                
                if self.mapping_mode:
                    left_active = abs(left_stick["x"]) > 5000 or abs(left_stick["y"]) > 5000
                    right_active = abs(right_stick["x"]) > 5000 or abs(right_stick["y"]) > 5000
                    
                    if left_active != left_stick.get("active", False):
                        left_stick["active"] = left_active
                        self.highlight_queue.put(("ABS_LEFT_STICK", left_active))
                    
                    if right_active != right_stick.get("active", False):
                        right_stick["active"] = right_active
                        self.highlight_queue.put(("ABS_RIGHT_STICK", right_active))
                    
                    left_changed = abs(left_stick["x"] - last_left_stick["x"]) > 1000 or abs(left_stick["y"] - last_left_stick["y"]) > 1000
                    right_changed = abs(right_stick["x"] - last_right_stick["x"]) > 1000 or abs(right_stick["y"] - last_right_stick["y"]) > 1000
                    
                    if events or left_changed or right_changed:
                        last_left_stick["x"] = left_stick["x"]
                        last_left_stick["y"] = left_stick["y"]
                        last_left_stick["active"] = left_active
                        
                        last_right_stick["x"] = right_stick["x"]
                        last_right_stick["y"] = right_stick["y"]
                        last_right_stick["active"] = right_active
                    
                    self.last_left_stick_state["x"] = last_left_stick["x"]
                    self.last_left_stick_state["y"] = last_left_stick["y"]
                    self.last_left_stick_state["active"] = last_left_stick["active"]
                    
                    self.last_right_stick_state["x"] = last_right_stick["x"]
                    self.last_right_stick_state["y"] = last_right_stick["y"]
                    self.last_right_stick_state["active"] = last_right_stick["active"]
                    
                    if last_left_stick.get("active", False) and (last_left_stick["x"] != 0 or last_left_stick["y"] != 0):
                        if "ABS_LEFT_STICK" in self.gamepad_config:
                            cfg = self.gamepad_config["ABS_LEFT_STICK"]
                            mode = cfg.get("func", "方向键")
                            if mode != "鼠标":
                                self.process_stick_action("ABS_LEFT_STICK", last_left_stick["x"], last_left_stick["y"])
                    
                    if last_right_stick.get("active", False) and (last_right_stick["x"] != 0 or last_right_stick["y"] != 0):
                        if "ABS_RIGHT_STICK" in self.gamepad_config:
                            cfg = self.gamepad_config["ABS_RIGHT_STICK"]
                            mode = cfg.get("func", "方向键")
                            if mode != "鼠标":
                                self.process_stick_action("ABS_RIGHT_STICK", last_right_stick["x"], last_right_stick["y"])
                
                time.sleep(0.005)
            except:
                time.sleep(0.005)

    def parse_event(self, event):
        if event.ev_type == "Key":
            return (event.code, event.state == 1)
        
        if event.code == "ABS_HAT0Y":
            if event.state == -1: return ("ABS_HAT0U", True)
            elif event.state == 1: return ("ABS_HAT0D", True)
            else:
                for key in ["ABS_HAT0U", "ABS_HAT0D"]:
                    if key in self.button_states and self.button_states[key]:
                        self.highlight_queue.put((key, False))
                return (None, False)
        
        if event.code == "ABS_HAT0X":
            if event.state == -1: return ("ABS_HAT0L", True)
            elif event.state == 1: return ("ABS_HAT0R", True)
            else:
                for key in ["ABS_HAT0L", "ABS_HAT0R"]:
                    if key in self.button_states and self.button_states[key]:
                        self.highlight_queue.put((key, False))
                return (None, False)
        
        if event.code in ["ABS_Z", "ABS_RZ"]:
            return (event.code, event.state > 100)
        
        if event.code in ["ABS_X", "ABS_Y"]:
            is_active = abs(event.state) > 20000
            other_code = "ABS_Y" if event.code == "ABS_X" else "ABS_X"
            other_active = other_code in self.button_states and self.button_states[other_code]
            pressed = is_active or other_active
            return ("ABS_LEFT_STICK", pressed)
        
        if event.code in ["ABS_RX", "ABS_RY"]:
            is_active = abs(event.state) > 20000
            other_code = "ABS_RY" if event.code == "ABS_RX" else "ABS_RX"
            other_active = other_code in self.button_states and self.button_states[other_code]
            pressed = is_active or other_active
            return ("ABS_RIGHT_STICK", pressed)
        
        return (None, False)

    def process_stick_event(self, event, left_stick, right_stick):
        if event.code == "ABS_X":
            left_stick["x"] = event.state
        elif event.code == "ABS_Y":
            left_stick["y"] = event.state
        elif event.code == "ABS_RX":
            right_stick["x"] = event.state
        elif event.code == "ABS_RY":
            right_stick["y"] = event.state
        
        left_active = abs(left_stick["x"]) > 5000 or abs(left_stick["y"]) > 5000
        right_active = abs(right_stick["x"]) > 5000 or abs(right_stick["y"]) > 5000
        
        if left_active != left_stick.get("active", False):
            left_stick["active"] = left_active
            self.highlight_queue.put(("ABS_LEFT_STICK", left_active))
        
        if right_active != right_stick.get("active", False):
            right_stick["active"] = right_active
            self.highlight_queue.put(("ABS_RIGHT_STICK", right_active))

    def process_stick_action(self, stick_name, x_value, y_value):
        if stick_name not in self.gamepad_config:
            return
        
        cfg = self.gamepad_config[stick_name]
        mode = cfg.get("func", "方向键")
        
        x_norm = x_value / 32768.0
        y_norm = -y_value / 32768.0
        
        if mode == "方向键":
            self.handle_stick_as_dpad(stick_name, x_norm, y_norm)
        elif mode == "摇杆":
            self.handle_stick_as_analog(stick_name, x_norm, y_norm, cfg)
        elif mode == "鼠标":
            self.handle_stick_as_mouse(stick_name, x_norm, y_norm)

    def handle_stick_as_dpad(self, stick_name, x_norm, y_norm):
        threshold = 0.5
        
        if abs(x_norm) > abs(y_norm):
            if x_norm > threshold:
                direction = "右"
            elif x_norm < -threshold:
                direction = "左"
            else:
                return
        else:
            if y_norm > threshold:
                direction = "下"
            elif y_norm < -threshold:
                direction = "上"
            else:
                return
        
        if stick_name not in self.gamepad_config:
            return
        
        cfg = self.gamepad_config[stick_name]
        target_window = self.window_var.get()
        
        if target_window != "整个屏幕":
            x, y = cfg.get("window_x", "0"), cfg.get("window_y", "0")
            if not x or not y: 
                return
            try:
                x, y = int(x), int(y)
                window_rect = self.get_window_rect(target_window)
                if window_rect:
                    left, top, _, _ = window_rect
                    x = left + x
                    y = top + y
            except:
                return
        else:
            x, y = cfg.get("screen_x", "0"), cfg.get("screen_y", "0")
            if not x or not y: 
                return
            try:
                x, y = int(x), int(y)
            except:
                return
        
        try:
            if direction == "上":
                touch_scroll_up(x, y, steps=1)
            elif direction == "下":
                touch_scroll_down(x, y, steps=1)
            elif direction == "左":
                self.scroll_horizontal(x, y, -1)
            elif direction == "右":
                self.scroll_horizontal(x, y, 1)
        except:
            pass

    def handle_stick_as_analog(self, stick_name, x_norm, y_norm, cfg):
        screen_x = cfg.get("screen_x", "0")
        screen_y = cfg.get("screen_y", "0")
        
        if not screen_x or not screen_y:
            return
        
        try:
            base_x = int(screen_x)
            base_y = int(screen_y)
            
            offset_x = int(x_norm * 30)
            offset_y = int(y_norm * 30)
            
            target_x = base_x + offset_x
            target_y = base_y + offset_y
            
            self.move_mouse_to(target_x, target_y)
        except:
            pass

    def handle_stick_as_mouse(self, stick_name, x_norm, y_norm):
        deadzone = 0.15
        
        stick_length = (x_norm ** 2 + y_norm ** 2) ** 0.5
        
        if stick_length < deadzone:
            return
        
        if stick_length > 0:
            x_dir = x_norm / stick_length
            y_dir = y_norm / stick_length
        else:
            return
        
        input_amount = (stick_length - deadzone) / (1 - deadzone)
        input_amount = max(0, min(1, input_amount))
        
        max_speed = 8
        speed_multiplier = input_amount * max_speed
        
        move_x = int(x_dir * speed_multiplier)
        move_y = int(y_dir * speed_multiplier)
        
        self.move_mouse_relative(move_x, move_y)

    def stick_mouse_loop(self):
        while self.stick_mouse_running:
            try:
                if self.last_left_stick_state.get("active", False):
                    x_norm = self.last_left_stick_state["x"] / 32768.0
                    y_norm = -self.last_left_stick_state["y"] / 32768.0
                    if "ABS_LEFT_STICK" in self.gamepad_config:
                        cfg = self.gamepad_config["ABS_LEFT_STICK"]
                        if cfg.get("func", "方向键") == "鼠标":
                            self.handle_stick_as_mouse("ABS_LEFT_STICK", x_norm, y_norm)
                
                if self.last_right_stick_state.get("active", False):
                    x_norm = self.last_right_stick_state["x"] / 32768.0
                    y_norm = -self.last_right_stick_state["y"] / 32768.0
                    if "ABS_RIGHT_STICK" in self.gamepad_config:
                        cfg = self.gamepad_config["ABS_RIGHT_STICK"]
                        if cfg.get("func", "方向键") == "鼠标":
                            self.handle_stick_as_mouse("ABS_RIGHT_STICK", x_norm, y_norm)
                
                time.sleep(0.005)
            except:
                time.sleep(0.01)

    def start_stick_mouse_loop(self):
        if not self.stick_mouse_running:
            self.stick_mouse_running = True
            self.stick_mouse_thread = threading.Thread(target=self.stick_mouse_loop, daemon=True)
            self.stick_mouse_thread.start()

    def stop_stick_mouse_loop(self):
        self.stick_mouse_running = False
        if self.stick_mouse_thread:
            self.stick_mouse_thread.join(timeout=0.1)

    def scroll_horizontal(self, x, y, steps):
        try:
            self.move_mouse_to(x, y)
            
            for i in range(abs(steps)):
                scroll_event = INPUT()
                scroll_event.type = INPUT_MOUSE
                scroll_event.mi.dx = 0
                scroll_event.mi.dy = 0
                scroll_event.mi.mouseData = 120 if steps > 0 else -120
                scroll_event.mi.dwFlags = 0x1000
                scroll_event.mi.time = 0
                scroll_event.mi.dwExtraInfo = None
                
                ctypes.windll.user32.SendInput(1, ctypes.byref(scroll_event), ctypes.sizeof(INPUT))
        except:
            pass

    def move_mouse_to(self, x, y):
        try:
            screen_width = ctypes.windll.user32.GetSystemMetrics(0)
            screen_height = ctypes.windll.user32.GetSystemMetrics(1)
            
            absolute_x = int(x * 65535 / screen_width)
            absolute_y = int(y * 65535 / screen_height)
            
            move_event = INPUT()
            move_event.type = INPUT_MOUSE
            move_event.mi.dx = absolute_x
            move_event.mi.dy = absolute_y
            move_event.mi.mouseData = 0
            move_event.mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
            move_event.mi.time = 0
            move_event.mi.dwExtraInfo = None
            
            ctypes.windll.user32.SendInput(1, ctypes.byref(move_event), ctypes.sizeof(INPUT))
        except:
            pass

    def move_mouse_relative(self, dx, dy):
        try:
            move_event = INPUT()
            move_event.type = INPUT_MOUSE
            move_event.mi.dx = dx
            move_event.mi.dy = dy
            move_event.mi.mouseData = 0
            move_event.mi.dwFlags = MOUSEEVENTF_MOVE
            move_event.mi.time = 0
            move_event.mi.dwExtraInfo = None
            
            ctypes.windll.user32.SendInput(1, ctypes.byref(move_event), ctypes.sizeof(INPUT))
        except:
            pass

    def process_highlight_queue(self):
        if self.processing_highlights: return
        self.processing_highlights = True
        while not self.highlight_queue.empty():
            btn, pressed = self.highlight_queue.get()
            self.button_states[btn] = pressed
            self.highlight_button(btn, pressed)
        self.processing_highlights = False
        self.after(50, self.process_highlight_queue)

    def highlight_button(self, btn, pressed):
        default_colors = {
            "BTN_SOUTH": "#32CD32", "BTN_EAST": "#DC143C", 
            "BTN_WEST": "#4169E1", "BTN_NORTH": "#FFD700",
            "ABS_HAT0U": "#505050", "ABS_HAT0D": "#505050",
            "ABS_HAT0L": "#505050", "ABS_HAT0R": "#505050",
            "BTN_THUMBL": "#606060", "BTN_THUMBR": "#606060",
            "BTN_TL": "#b0b0b0", "BTN_TR": "#b0b0b0",
            "ABS_Z": "#b0b0b0", "ABS_RZ": "#b0b0b0",
            "BTN_START": "#b0b0b0", "BTN_SELECT": "#b0b0b0"
        }
        
        highlight_color = "#FFA500"
        
        if btn in self.labels:
            self.labels[btn].config(bg=highlight_color if pressed else "white")
        
        if btn in self.button_widgets:
            widget, _ = self.button_widgets[btn]
            if widget:
                if btn in ["ABS_LEFT_STICK", "ABS_RIGHT_STICK"]:
                    self.gamepad_canvas.itemconfig(widget, state="normal" if pressed else "hidden")
                else:
                    default_color = default_colors.get(btn, "#b0b0b0")
                    self.gamepad_canvas.itemconfig(widget, fill=highlight_color if pressed else default_color)

    def execute_touch(self, cfg):
        target_window = self.window_var.get()
        
        if target_window != "整个屏幕":
            x, y = cfg.get("window_x", "0"), cfg.get("window_y", "0")
            if not x or not y: return
            try:
                x, y = int(x), int(y)
                
                import ctypes
                hwnd = ctypes.windll.user32.FindWindowW(None, target_window)
                if not hwnd: hwnd = self.find_window_by_partial_title(target_window)
                if hwnd:
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
                    time.sleep(0.1)
                    
                    window_rect = self.get_window_rect(target_window)
                    if window_rect:
                        left, top, _, _ = window_rect
                        x = left + x
                        y = top + y
            except:
                return
        else:
            x, y = cfg.get("screen_x", "0"), cfg.get("screen_y", "0")
            if not x or not y: return
            try:
                x, y = int(x), int(y)
            except:
                return
        
        try:
            func = cfg.get("func", "点击")
            if func == "点击": 
                touch_click(x, y)
            elif func == "长按": 
                touch_long_press(x, y)
            elif func == "上滑": 
                touch_scroll_up(x, y)
            elif func == "下滑": 
                touch_scroll_down(x, y)
            elif func == "滑动": 
                touch_swipe(x, y, x+50, y+50)
        except:
            pass

    def execute_touch_start(self, cfg):
        target_window = self.window_var.get()
        
        if target_window != "整个屏幕":
            x, y = cfg.get("window_x", "0"), cfg.get("window_y", "0")
            if not x or not y: return
            try:
                x, y = int(x), int(y)
                
                import ctypes
                hwnd = ctypes.windll.user32.FindWindowW(None, target_window)
                if not hwnd: hwnd = self.find_window_by_partial_title(target_window)
                if hwnd:
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
                    time.sleep(0.1)
                    
                    window_rect = self.get_window_rect(target_window)
                    if window_rect:
                        left, top, _, _ = window_rect
                        x = left + x
                        y = top + y
            except:
                return
        else:
            x, y = cfg.get("screen_x", "0"), cfg.get("screen_y", "0")
            if not x or not y: return
            try:
                x, y = int(x), int(y)
            except:
                return
        
        try:
            touch_long_press_start(x, y)
        except:
            pass

    def get_window_rect(self, window_title):
        try:
            import ctypes
            from ctypes import wintypes
            hwnd = ctypes.windll.user32.FindWindowW(None, window_title)
            if not hwnd: hwnd = self.find_window_by_partial_title(window_title)
            if hwnd:
                rect = wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                return (rect.left, rect.top, rect.right, rect.bottom)
        except:
            pass
        return None

    def find_window_by_partial_title(self, partial_title):
        import ctypes
        from ctypes import wintypes
        found_hwnd = None
        def callback(hwnd, extra):
            nonlocal found_hwnd
            buffer = ctypes.create_unicode_buffer(256)
            ctypes.windll.user32.GetWindowTextW(hwnd, buffer, 256)
            if buffer.value and partial_title.lower() in buffer.value.lower():
                found_hwnd = hwnd
                return False
            return True
        EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        ctypes.windll.user32.EnumWindows(EnumWindowsProc(callback), 0)
        return found_hwnd

    def refresh_windows(self):
        import ctypes
        from ctypes import wintypes
        windows = ["整个屏幕"]
        def callback(hwnd, extra):
            buffer = ctypes.create_unicode_buffer(256)
            ctypes.windll.user32.GetWindowTextW(hwnd, buffer, 256)
            if buffer.value and buffer.value not in ["", "Program Manager"]:
                if ctypes.windll.user32.IsWindowVisible(hwnd):
                    windows.append(buffer.value)
            return True
        EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        ctypes.windll.user32.EnumWindows(EnumWindowsProc(callback), 0)
        self.window_combo['values'] = windows

    def new_profile(self):
        name = f"方案{len(self.profile_combo['values'])}"
        self.profile_combo['values'] = list(self.profile_combo['values']) + [name]
        self.profile_var.set(name)

    def delete_profile(self):
        if len(self.profile_combo['values']) > 1:
            messagebox.showinfo("删除方案", "方案删除功能待实现")
        else:
            messagebox.showwarning("删除方案", "至少保留一个方案")

    def start_coordinate_capture(self, btn):
        try:
            self.current_capture_btn = btn
            self.status_label.config(text=f"状态: 请点击目标位置 ({BUTTON_NAMES.get(btn, btn)})", foreground="blue")
            
            target_window = self.window_var.get()
            
            self.update_idletasks()
            self.update()
            
            if target_window != "整个屏幕":
                hwnd = ctypes.windll.user32.FindWindowW(None, target_window)
                if not hwnd: hwnd = self.find_window_by_partial_title(target_window)
                
                if hwnd:
                    window_style = ctypes.windll.user32.GetWindowLongW(hwnd, -16)
                    is_minimized = (window_style & 0x20000000) != 0
                    
                    if is_minimized:
                        ctypes.windll.user32.ShowWindow(hwnd, 9)
                    else:
                        ctypes.windll.user32.ShowWindow(hwnd, 5)
                    
                    window_thread = ctypes.windll.user32.GetWindowThreadProcessId(hwnd, None)
                    current_thread = ctypes.windll.kernel32.GetCurrentThreadId()
                    ctypes.windll.user32.AttachThreadInput(window_thread, current_thread, True)
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
                    ctypes.windll.user32.AttachThreadInput(window_thread, current_thread, False)
                    time.sleep(0.5)
                else:
                    messagebox.showwarning("窗口未找到", f"目标窗口 '{target_window}' 未运行或标题不正确！")
                    self.status_label.config(text="状态: 正在监听手柄按键...", foreground="green")
                    return
            
            def mouse_listener_thread():
                import ctypes
                from ctypes import wintypes
                while True:
                    if ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000:
                        point = wintypes.POINT()
                        ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
                        x, y = point.x, point.y
                        self.after(0, lambda: self.capture_global_coordinate(x, y))
                        break
                    time.sleep(0.01)
            
            import threading
            self.mouse_thread = threading.Thread(target=mouse_listener_thread, daemon=True)
            self.mouse_thread.start()
            
        except:
            self.update()

    def capture_global_coordinate(self, x, y):
        try:
            target_window = self.window_var.get()
            
            window_x, window_y = x, y
            if target_window != "整个屏幕":
                window_rect = self.get_window_rect(target_window)
                if window_rect:
                    left, top, right, bottom = window_rect
                    
                    window_x = x - left
                    window_y = y - top
                    window_x = max(0, window_x)
                    window_y = max(0, window_y)
            
            if self.current_capture_btn in self.entries:
                screen_entry, window_entry, _ = self.entries[self.current_capture_btn]
                screen_entry.delete(0, 'end')
                screen_entry.insert(0, f"{x},{y}")
                window_entry.delete(0, 'end')
                window_entry.insert(0, f"{window_x},{window_y}")
            
            self.status_label.config(text=f"状态: 已保存坐标 屏幕({x},{y}) 窗口({window_x},{window_y})", foreground="green")
            self.update_idletasks()
            self.update()
            
            try:
                if self.state() == 'iconic':
                    self.deiconify()
                
                self.lift()
                self.attributes('-topmost', True)
                self.focus_force()
                self.update_idletasks()
                
                self.after(100, lambda: self.attributes('-topmost', False))
            except:
                pass
            
            self.after(3000, lambda: self.status_label.config(text="状态: 正在监听手柄按键...", foreground="green"))
        except:
            self.update()

    def capture_coordinate(self, event):
        self.capture_global_coordinate(event.x_root, event.y_root)
        return "break"

    def start_mapping(self):
        self.save()
        self.mapping_mode = True
        self.start_stick_mouse_loop()
        self.start_mapping_btn.config(state="disabled")
        self.stop_mapping_btn.config(state="normal")
        self.status_label.config(text="状态: 映射已启动", foreground="green")
        self.mapping_status_label.config(text="映射: 已启动", foreground="green")

    def stop_mapping(self):
        self.mapping_mode = False
        self.stop_stick_mouse_loop()
        if hasattr(self, 'tray_icon'):
            self.tray_icon.stop()
        self.deiconify()
        self.start_mapping_btn.config(state="normal")
        self.stop_mapping_btn.config(state="disabled")
        self.status_label.config(text="状态: 映射已停止", foreground="blue")
        self.mapping_status_label.config(text="映射: 未启动", foreground="gray")

    def create_tray_icon(self):
        image = Image.new('RGB', (64, 64), color='blue')
        draw = ImageDraw.Draw(image)
        draw.rectangle([16, 16, 48, 48], fill='white')
        menu = pystray.Menu(
            pystray.MenuItem("显示窗口", self.show_window),
            pystray.MenuItem("退出", self.exit_app)
        )
        self.tray_icon = pystray.Icon("gamepad_mapper", image, "手柄触屏映射", menu)
        self.tray_icon.run()

    def show_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def exit_app(self):
        self.listening = False
        if hasattr(self, 'tray_icon'): self.tray_icon.stop()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.config_info_label.config(text="配置: 已加载", foreground="blue")
    app.mainloop()
