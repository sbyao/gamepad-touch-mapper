"""
手柄映射子进程
功能：在独立进程中运行手柄输入检测和映射功能
通信方式：通过标准输入输出与主进程通信（JSON格式）
"""
import sys
import json
import time
import threading
import ctypes
import os
try:
    from inputs import get_gamepad
except ImportError:
    print(json.dumps({"type": "error", "message": "inputs模块未安装"}), flush=True)
    sys.exit(1)
VK_KEYS = {
    'A': 0x41, 'B': 0x42, 'C': 0x43, 'D': 0x44, 'E': 0x45, 'F': 0x46,
    'G': 0x47, 'H': 0x48, 'I': 0x49, 'J': 0x4A, 'K': 0x4B, 'L': 0x4C,
    'M': 0x4D, 'N': 0x4E, 'O': 0x4F, 'P': 0x50, 'Q': 0x51, 'R': 0x52,
    'S': 0x53, 'T': 0x54, 'U': 0x55, 'V': 0x56, 'W': 0x57, 'X': 0x58,
    'Y': 0x59, 'Z': 0x5A,
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
    'F1': 0x70, 'F2': 0x71, 'F3': 0x72, 'F4': 0x73, 'F5': 0x74,
    'F6': 0x75, 'F7': 0x76, 'F8': 0x77, 'F9': 0x78, 'F10': 0x79,
    'F11': 0x7A, 'F12': 0x7B,
    'ESC': 0x1B, 'TAB': 0x09, 'CAPS': 0x14, 'SPACE': 0x20,
    'ENTER': 0x0D, 'BACK': 0x08, 'SHIFT': 0x10, 'CTRL': 0x11,
    'ALT': 0x12, 'WIN': 0x5B, 'MENU': 0x5D,
    'UP': 0x26, 'DOWN': 0x28, 'LEFT': 0x25, 'RIGHT': 0x27,
    'INS': 0x2D, 'DEL': 0x2E, 'HOME': 0x24, 'END': 0x23,
    'PGUP': 0x21, 'PGDN': 0x22,
}
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_WHEEL = 0x0800
WHEEL_DELTA = 120
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_uint),
        ("time", ctypes.c_uint),
        ("dwExtraInfo", ctypes.c_void_p)
    ]
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_uint),
        ("dwFlags", ctypes.c_uint),
        ("time", ctypes.c_uint),
        ("dwExtraInfo", ctypes.c_void_p)
    ]
class INPUT_I(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", ctypes.c_ubyte * 8)]
class INPUT(ctypes.Structure):
    _anonymous_ = ("i",)
    _fields_ = [("type", ctypes.c_uint), ("i", INPUT_I)]
def send_key_press(key_code):
    try:
        input_down = INPUT()
        input_down.type = INPUT_KEYBOARD
        input_down.ki.wVk = key_code
        input_down.ki.wScan = 0
        input_down.ki.dwFlags = 0
        input_down.ki.time = 0
        input_down.ki.dwExtraInfo = None
        input_up = INPUT()
        input_up.type = INPUT_KEYBOARD
        input_up.ki.wVk = key_code
        input_up.ki.wScan = 0
        input_up.ki.dwFlags = KEYEVENTF_KEYUP
        input_up.ki.time = 0
        input_up.ki.dwExtraInfo = None
        inputs = (INPUT * 2)(input_down, input_up)
        ctypes.windll.user32.SendInput(2, ctypes.byref(inputs), ctypes.sizeof(INPUT))
    except Exception as e:
        pass
def simulate_key(key_name):
    try:
        if ' + ' in key_name:
            keys = [k.strip().upper() for k in key_name.split(' + ')]
            valid_keys = [key for key in keys if key in VK_KEYS]
            if not valid_keys:
                return
            for key in valid_keys:
                input_down = INPUT()
                input_down.type = INPUT_KEYBOARD
                input_down.ki.wVk = VK_KEYS[key]
                input_down.ki.wScan = 0
                input_down.ki.dwFlags = 0
                input_down.ki.time = 0
                input_down.ki.dwExtraInfo = None
                ctypes.windll.user32.SendInput(1, ctypes.byref(input_down), ctypes.sizeof(INPUT))
            time.sleep(0.05)
            for key in reversed(valid_keys):
                input_up = INPUT()
                input_up.type = INPUT_KEYBOARD
                input_up.ki.wVk = VK_KEYS[key]
                input_up.ki.wScan = 0
                input_up.ki.dwFlags = KEYEVENTF_KEYUP
                input_up.ki.time = 0
                input_up.ki.dwExtraInfo = None
                ctypes.windll.user32.SendInput(1, ctypes.byref(input_up), ctypes.sizeof(INPUT))
        else:
            key_upper = key_name.upper()
            if key_upper in VK_KEYS:
                send_key_press(VK_KEYS[key_upper])
    except Exception as e:
        pass
def send_mouse_click(x, y):
    try:
        screen_width = ctypes.windll.user32.GetSystemMetrics(0)
        screen_height = ctypes.windll.user32.GetSystemMetrics(1)
        if x < 0 or y < 0 or x > screen_width or y > screen_height:
            return
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
    except Exception as e:
        pass
def touch_long_press_start(x, y):
    try:
        screen_width = ctypes.windll.user32.GetSystemMetrics(0)
        screen_height = ctypes.windll.user32.GetSystemMetrics(1)
        if x < 0 or y < 0 or x > screen_width or y > screen_height:
            return
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
    except Exception as e:
        pass
def touch_long_press_end():
    try:
        release_event = INPUT()
        release_event.type = INPUT_MOUSE
        release_event.mi.dx = 0
        release_event.mi.dy = 0
        release_event.mi.mouseData = 0
        release_event.mi.dwFlags = MOUSEEVENTF_LEFTUP
        release_event.mi.time = 0
        release_event.mi.dwExtraInfo = None
        ctypes.windll.user32.SendInput(1, ctypes.byref(release_event), ctypes.sizeof(INPUT))
    except Exception as e:
        pass
def touch_scroll(x, y, steps=3, is_up=True):
    try:
        screen_width = ctypes.windll.user32.GetSystemMetrics(0)
        screen_height = ctypes.windll.user32.GetSystemMetrics(1)
        if x < 0 or y < 0 or x > screen_width or y > screen_height:
            return
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
    except Exception as e:
        pass
def move_mouse_relative(dx, dy):
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
    except Exception as e:
        pass
BUTTON_NAMES = {
    "BTN_SOUTH": "A键", "BTN_EAST": "B键", "BTN_NORTH": "Y键", "BTN_WEST": "X键",
    "BTN_TL": "LB", "BTN_TR": "RB", "BTN_SELECT": "Back", "BTN_START": "Start",
    "BTN_THUMBL": "L3", "BTN_THUMBR": "R3", "ABS_HAT0U": "十字上", "ABS_HAT0D": "十字下",
    "ABS_HAT0L": "十字左", "ABS_HAT0R": "十字右", "ABS_Z": "LT", "ABS_RZ": "RT",
    "ABS_LEFT_STICK": "左摇杆", "ABS_RIGHT_STICK": "右摇杆"
}
class MapperSubprocess:
    def __init__(self):
        self.running = False
        self.mapping_mode = False
        self.config = {}
        self.target_window = "整个屏幕"
        self.window_rect = None
        self.long_press_buttons = {}
        self.left_stick = {"x": 0, "y": 0, "active": False}
        self.right_stick = {"x": 0, "y": 0, "active": False}
        self.last_left_stick = {"x": 0, "y": 0, "active": False}
        self.last_right_stick = {"x": 0, "y": 0, "active": False}
        self.stick_mouse_running = False
        self.stick_mouse_thread = None
    def log(self, message, msg_type="info"):
        """向主进程发送日志消息"""
        print(json.dumps({"type": msg_type, "message": message}), flush=True)
    def send_event(self, btn, pressed):
        """向主进程发送按钮事件"""
        print(json.dumps({"type": "event", "button": btn, "pressed": pressed}), flush=True)
    def run(self):
        """主循环"""
        self.running = True
        self.log("子进程已启动", "started")
        cmd_thread = threading.Thread(target=self.command_listener, daemon=True)
        cmd_thread.start()
        self.gamepad_listener()
    def command_listener(self):
        """监听主进程的命令"""
        while self.running:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                data = json.loads(line.strip())
                cmd = data.get("cmd")
                if cmd == "start_mapping":
                    self.config = data.get("config", {})
                    self.target_window = data.get("target_window", "整个屏幕")
                    self.window_rect = data.get("window_rect")
                    self.mapping_mode = True
                    self.start_stick_mouse_loop()
                    self.log("映射已启动", "mapping_started")
                elif cmd == "stop_mapping":
                    self.mapping_mode = False
                    self.stop_stick_mouse_loop()
                    self.log("映射已停止", "mapping_stopped")
                elif cmd == "update_config":
                    self.config = data.get("config", {})
                    self.target_window = data.get("target_window", "整个屏幕")
                    self.window_rect = data.get("window_rect")
                    self.log("配置已更新", "config_updated")
                elif cmd == "exit":
                    self.running = False
                    self.mapping_mode = False
                    self.log("子进程即将退出", "exiting")
                    break
            except json.JSONDecodeError:
                pass
            except Exception as e:
                self.log(f"命令处理错误: {e}", "error")
    def gamepad_listener(self):
        """手柄监听循环"""
        connected = False
        while self.running:
            try:
                if not connected:
                    try:
                        from inputs import devices
                        gamepads = devices.gamepads
                        if gamepads:
                            get_gamepad()
                            connected = True
                            self.log("手柄已连接", "connected")
                        else:
                            time.sleep(1)
                            continue
                    except:
                        time.sleep(1)
                        continue
                events = get_gamepad()
                for event in events:
                    if event.code in ["ABS_X", "ABS_Y", "ABS_RX", "ABS_RY"]:
                        self.process_stick_event(event)
                        continue
                    btn, pressed = self.parse_event(event)
                    if btn:
                        self.send_event(btn, pressed)
                        if self.mapping_mode:
                            self.execute_button_action(btn, pressed)
                if self.mapping_mode:
                    self.process_stick_actions()
                time.sleep(0.005)
            except Exception as e:
                if connected:
                    connected = False
                    self.log("手柄断开连接", "disconnected")
                time.sleep(1)
    def parse_event(self, event):
        """解析手柄事件"""
        if event.ev_type == "Key":
            return (event.code, event.state == 1)
        if event.code == "ABS_HAT0Y":
            if event.state == -1: return ("ABS_HAT0U", True)
            elif event.state == 1: return ("ABS_HAT0D", True)
            else: return (None, False)
        if event.code == "ABS_HAT0X":
            if event.state == -1: return ("ABS_HAT0L", True)
            elif event.state == 1: return ("ABS_HAT0R", True)
            else: return (None, False)
        if event.code in ["ABS_Z", "ABS_RZ"]:
            return (event.code, event.state > 100)
        if event.code in ["ABS_X", "ABS_Y"]:
            is_active = abs(event.state) > 20000
            return ("ABS_LEFT_STICK", is_active)
        if event.code in ["ABS_RX", "ABS_RY"]:
            is_active = abs(event.state) > 20000
            return ("ABS_RIGHT_STICK", is_active)
        return (None, False)
    def process_stick_event(self, event):
        """处理摇杆事件"""
        if event.code == "ABS_X":
            self.left_stick["x"] = event.state
        elif event.code == "ABS_Y":
            self.left_stick["y"] = event.state
        elif event.code == "ABS_RX":
            self.right_stick["x"] = event.state
        elif event.code == "ABS_RY":
            self.right_stick["y"] = event.state
        self.left_stick["active"] = abs(self.left_stick["x"]) > 5000 or abs(self.left_stick["y"]) > 5000
        self.right_stick["active"] = abs(self.right_stick["x"]) > 5000 or abs(self.right_stick["y"]) > 5000
    def execute_button_action(self, btn, pressed):
        """执行按钮动作"""
        if btn not in self.config:
            return
        cfg = self.config[btn]
        func = cfg.get("func", "点击")
        if btn in ["ABS_LEFT_STICK", "ABS_RIGHT_STICK"]:
            return
        if pressed:
            if func == "长按":
                self.long_press_buttons[btn] = True
                self.execute_touch_start(cfg)
            elif func == "按键":
                key = cfg.get("key", "")
                if key:
                    simulate_key(key)
            else:
                self.execute_touch(cfg)
        else:
            if func == "长按" and btn in self.long_press_buttons:
                del self.long_press_buttons[btn]
                touch_long_press_end()
    def execute_touch(self, cfg):
        """执行触摸/点击操作"""
        func = cfg.get("func", "点击")
        if func == "按键":
            return
        x, y = self.get_coordinates(cfg)
        if x is None or y is None:
            return
        try:
            if func == "点击":
                send_mouse_click(x, y)
            elif func == "长按":
                touch_long_press_start(x, y)
                time.sleep(0.5)
                touch_long_press_end()
            elif func == "上滑":
                touch_scroll(x, y, steps=3, is_up=True)
            elif func == "下滑":
                touch_scroll(x, y, steps=3, is_up=False)
        except:
            pass
    def execute_touch_start(self, cfg):
        """开始长按"""
        x, y = self.get_coordinates(cfg)
        if x is None or y is None:
            return
        try:
            touch_long_press_start(x, y)
        except:
            pass
    def get_coordinates(self, cfg):
        """获取坐标"""
        if self.target_window != "整个屏幕" and self.window_rect:
            x = cfg.get("window_x", "")
            y = cfg.get("window_y", "")
            if x and y and x != "0" and y != "0":
                try:
                    x = int(x) + self.window_rect[0]
                    y = int(y) + self.window_rect[1]
                    return x, y
                except:
                    pass
        x = cfg.get("screen_x", "")
        y = cfg.get("screen_y", "")
        if x and y and x != "0" and y != "0":
            try:
                return int(x), int(y)
            except:
                pass
        return None, None
    def process_stick_actions(self):
        """处理摇杆动作"""
        if self.left_stick["active"] != self.last_left_stick.get("active", False):
            self.last_left_stick["active"] = self.left_stick["active"]
            self.send_event("ABS_LEFT_STICK", self.left_stick["active"])
        if self.right_stick["active"] != self.last_right_stick.get("active", False):
            self.last_right_stick["active"] = self.right_stick["active"]
            self.send_event("ABS_RIGHT_STICK", self.right_stick["active"])
        self.last_left_stick["x"] = self.left_stick["x"]
        self.last_left_stick["y"] = self.left_stick["y"]
        self.last_right_stick["x"] = self.right_stick["x"]
        self.last_right_stick["y"] = self.right_stick["y"]
    def start_stick_mouse_loop(self):
        """启动摇杆鼠标循环"""
        if not self.stick_mouse_running:
            self.stick_mouse_running = True
            self.stick_mouse_thread = threading.Thread(target=self.stick_mouse_loop, daemon=True)
            self.stick_mouse_thread.start()
    def stop_stick_mouse_loop(self):
        """停止摇杆鼠标循环"""
        self.stick_mouse_running = False
        if self.stick_mouse_thread:
            self.stick_mouse_thread.join(timeout=0.1)
    def stick_mouse_loop(self):
        """摇杆鼠标移动循环"""
        while self.stick_mouse_running:
            try:
                if "ABS_LEFT_STICK" in self.config:
                    cfg = self.config["ABS_LEFT_STICK"]
                    if cfg.get("func") == "鼠标" and self.left_stick.get("active", False):
                        x_norm = self.left_stick["x"] / 32768.0
                        y_norm = -self.left_stick["y"] / 32768.0
                        self.handle_stick_as_mouse(x_norm, y_norm)
                if "ABS_RIGHT_STICK" in self.config:
                    cfg = self.config["ABS_RIGHT_STICK"]
                    if cfg.get("func") == "鼠标" and self.right_stick.get("active", False):
                        x_norm = self.right_stick["x"] / 32768.0
                        y_norm = -self.right_stick["y"] / 32768.0
                        self.handle_stick_as_mouse(x_norm, y_norm)
                time.sleep(0.005)
            except:
                time.sleep(0.01)
    def handle_stick_as_mouse(self, x_norm, y_norm):
        """处理摇杆作为鼠标"""
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
        move_mouse_relative(move_x, move_y)
if __name__ == "__main__":
    mapper = MapperSubprocess()
    mapper.run()
