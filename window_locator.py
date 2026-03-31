import ctypes
from ctypes import wintypes
import json
import re
import os
class WindowLocator:
    """通用窗口定位器 - 支持普通程序、浏览器、WSA、游戏等多种窗口类型"""
    def __init__(self):
        self.window_cache = {}
    def get_window_features(self, hwnd):
        """获取窗口的所有特征"""
        features = {
            'hwnd': hwnd,
            'title': self._get_window_title(hwnd),
            'class_name': self._get_class_name(hwnd),
            'process_name': self._get_process_name(hwnd),
            'pid': self._get_process_id(hwnd),
            'rect': self._get_window_rect(hwnd),
            'is_visible': self._is_visible(hwnd),
            'is_main_window': self._is_main_window(hwnd)
        }
        if features['rect']:
            features['width'] = features['rect'][2] - features['rect'][0]
            features['height'] = features['rect'][3] - features['rect'][1]
        else:
            features['width'] = 0
            features['height'] = 0
        features['window_type'] = self._detect_window_type(features)
        return features
    def _detect_window_type(self, features):
        """自动检测窗口类型"""
        proc = features['process_name'].lower()
        title = features['title'].lower()
        class_name = features['class_name'].lower()
        if 'wsaclient' in proc:
            return 'wsa'
        if proc in ['chrome.exe', 'firefox.exe', 'msedge.exe', 'brave.exe']:
            return 'browser'
        if any(x in proc for x in ['potplayer', 'vlc', 'mpc', 'kmplayer']):
            return 'player'
        if 'applicationframewindow' in class_name or 'windows.ui.core.corewindow' in class_name:
            return 'uwp'
        if class_name in ['unitywndclass', 'unrealwindow', 'cryengine', 'riotgameswindow']:
            return 'game'
        return 'win32'
    def save_window_profile(self, hwnd, profile_name, config_dir="."):
        """保存窗口特征到配置文件"""
        features = self.get_window_features(hwnd)
        window_type = features['window_type']
        profile = {
            'name': profile_name,
            'type': window_type,
            'process': features['process_name'],
            'title': features['title'],
            'class_name': features['class_name'],
            'width': features['width'],
            'height': features['height'],
            'title_keywords': self._extract_keywords(features['title'])
        }
        config_file = os.path.join(config_dir, f'{profile_name}_window.json')
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(profile, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存窗口配置失败: {e}")
        return profile
    def load_window_profile(self, profile_name, config_dir="."):
        """加载窗口配置文件"""
        config_file = os.path.join(config_dir, f'{profile_name}_window.json')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载窗口配置失败: {e}")
        return None
    def find_window(self, profile):
        """根据配置文件查找窗口"""
        if not profile:
            return None
        window_type = profile.get('type', 'win32')
        candidates = self._get_all_windows_by_process(profile['process'])
        if not candidates:
            return None
        matchers = {
            'wsa': self._match_wsa_window,
            'browser': self._match_browser_window,
            'player': self._match_player_window,
            'game': self._match_game_window,
            'uwp': self._match_uwp_window,
            'win32': self._match_win32_window
        }
        matcher = matchers.get(window_type, self._match_generic_window)
        return matcher(profile, candidates)
    def find_window_by_title(self, title_keyword):
        """通过标题关键字查找窗口"""
        def callback(hwnd, extra):
            if not self._is_visible(hwnd):
                return True
            title = self._get_window_title(hwnd)
            if title_keyword.lower() in title.lower():
                found.append(hwnd)
                return False
            return True
        found = []
        EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        ctypes.windll.user32.EnumWindows(EnumWindowsProc(callback), 0)
        return found[0] if found else None
    def _match_wsa_window(self, profile, candidates):
        """匹配WSA窗口"""
        for c in candidates:
            if profile['title'].lower() == c['title'].lower():
                return c['hwnd']
        for keyword in profile.get('title_keywords', []):
            for c in candidates:
                if keyword.lower() in c['title'].lower():
                    return c['hwnd']
        return self._find_largest_visible(candidates)
    def _match_browser_window(self, profile, candidates):
        """匹配浏览器窗口"""
        for keyword in profile.get('title_keywords', []):
            for c in candidates:
                if keyword.lower() in c['title'].lower():
                    return c['hwnd']
        return self._find_main_window(candidates)
    def _match_player_window(self, profile, candidates):
        """匹配播放器窗口"""
        target_w, target_h = profile['width'], profile['height']
        best_match = None
        best_score = float('inf')
        for c in candidates:
            if not c['is_visible']:
                continue
            score = abs(c['width'] - target_w) + abs(c['height'] - target_h)
            if score < best_score:
                best_score = score
                best_match = c['hwnd']
        if best_score < 100:
            return best_match
        return self._find_main_window(candidates)
    def _match_game_window(self, profile, candidates):
        """匹配游戏窗口"""
        for c in candidates:
            if c['class_name'] == profile['class_name']:
                return c['hwnd']
        return self._match_player_window(profile, candidates)
    def _match_uwp_window(self, profile, candidates):
        """匹配UWP窗口"""
        return self._match_wsa_window(profile, candidates)
    def _match_win32_window(self, profile, candidates):
        """匹配普通Win32窗口"""
        for c in candidates:
            if (c['process_name'] == profile['process'] and 
                c['class_name'] == profile['class_name']):
                return c['hwnd']
        for c in candidates:
            if c['title'] == profile['title']:
                return c['hwnd']
        return self._find_main_window(candidates)
    def _match_generic_window(self, profile, candidates):
        """通用匹配"""
        for c in candidates:
            if (c['process_name'] == profile['process'] and
                c['class_name'] == profile['class_name'] and
                c['title'] == profile['title']):
                return c['hwnd']
        for c in candidates:
            if (c['process_name'] == profile['process'] and
                c['class_name'] == profile['class_name']):
                return c['hwnd']
        for keyword in profile.get('title_keywords', []):
            for c in candidates:
                if keyword.lower() in c['title'].lower():
                    return c['hwnd']
        return self._find_main_window(candidates)
    def _get_all_windows_by_process(self, process_name):
        """获取指定进程的所有窗口"""
        windows = []
        def callback(hwnd, extra):
            if not self._is_visible(hwnd):
                return True
            pid = self._get_process_id(hwnd)
            proc = self._get_process_name(pid)
            if process_name.lower() in proc.lower():
                features = self.get_window_features(hwnd)
                windows.append(features)
            return True
        EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        ctypes.windll.user32.EnumWindows(EnumWindowsProc(callback), 0)
        return windows
    def _find_main_window(self, candidates):
        """找主窗口"""
        best = None
        max_area = 0
        for c in candidates:
            if not c['is_visible']:
                continue
            area = c['width'] * c['height']
            if area > max_area:
                max_area = area
                best = c['hwnd']
        return best
    def _find_largest_visible(self, candidates):
        """找最大的可见窗口"""
        return self._find_main_window(candidates)
    def _extract_keywords(self, title):
        """从标题中提取关键字"""
        if not title:
            return []
        patterns = [
            r'[-–—]\s*[^-]*$',
            r'\[[^\]]*\]',
            r'\([^\)]*\)',
        ]
        keywords = [title]
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                keyword = title[:match.start()].strip()
                if keyword and len(keyword) > 2:
                    keywords.append(keyword)
        return keywords
    def _get_window_title(self, hwnd):
        buffer = ctypes.create_unicode_buffer(256)
        ctypes.windll.user32.GetWindowTextW(hwnd, buffer, 256)
        return buffer.value
    def _get_class_name(self, hwnd):
        buffer = ctypes.create_unicode_buffer(256)
        ctypes.windll.user32.GetClassNameW(hwnd, buffer, 256)
        return buffer.value
    def _get_process_id(self, hwnd):
        pid = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return pid.value
    def _get_process_name(self, pid):
        """通过PID获取进程名"""
        try:
            kernel32 = ctypes.windll.kernel32
            psapi = ctypes.windll.psapi
            PROCESS_QUERY_INFORMATION = 0x0400
            PROCESS_VM_READ = 0x0010
            hProcess = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
            if not hProcess:
                return "unknown"
            try:
                filename = (ctypes.c_char * 260)()
                psapi.GetModuleBaseNameA(hProcess, None, filename, 260)
                return filename.value.decode('utf-8', errors='ignore')
            finally:
                kernel32.CloseHandle(hProcess)
        except:
            return "unknown"
    def _get_window_rect(self, hwnd):
        try:
            rect = wintypes.RECT()
            ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
            return (rect.left, rect.top, rect.right, rect.bottom)
        except:
            return None
    def _is_visible(self, hwnd):
        return ctypes.windll.user32.IsWindowVisible(hwnd)
    def _is_main_window(self, hwnd):
        if ctypes.windll.user32.GetParent(hwnd) != 0:
            return False
        if not self._get_window_title(hwnd):
            return False
        if not self._is_visible(hwnd):
            return False
        return True
