# 开发文档

## 项目结构

```
.
├── 演示.py              # 主程序文件
├── gamepad_config.json  # 配置文件（运行时生成）
├── README.md           # 使用文档
└── DEVELOPMENT.md      # 开发文档
```

## 技术栈

- **GUI**: Tkinter + ttk
- **手柄输入**: inputs库
- **鼠标模拟**: Windows API (SendInput)
- **系统托盘**: pystray
- **图像处理**: PIL (Pillow)

## 核心架构

### 1. 输入处理层

```python
# Windows API 结构体定义
class MOUSEINPUT(ctypes.Structure)
class INPUT(ctypes.Structure)

# 鼠标操作函数
send_mouse_click(x, y)      # 发送鼠标点击
touch_long_press_start()     # 开始长按
touch_long_press_end()       # 结束长按
touch_scroll()              # 滚动操作
```

### 2. 手柄监听层

```python
def gamepad_listener()
```

独立线程监听手柄输入，使用 `inputs.get_gamepad()` 获取事件。

**事件处理流程:**
1. 获取手柄事件
2. 解析事件类型（按键/摇杆/扳机）
3. 更新UI状态（高亮显示）
4. 如果映射模式开启，执行对应操作

### 3. 摇杆处理

**摇杆鼠标模式（独立线程）:**
```python
def stick_mouse_loop()
```

- 持续读取摇杆状态
- 计算鼠标移动量（带15%死区）
- 调用 `move_mouse_relative()` 移动鼠标

**摇杆方向键模式:**
```python
def handle_stick_as_dpad()
```

- 判断主要方向（上下左右）
- 执行滚动操作

**摇杆模拟模式:**
```python
def handle_stick_as_analog()
```

- 在基准坐标周围移动
- 最大偏移30像素

### 4. 窗口管理

```python
def get_window_rect(window_title)          # 获取窗口位置
def find_window_by_partial_title(title)    # 模糊匹配窗口
def refresh_windows()                      # 刷新窗口列表
```

### 5. 坐标捕获

```python
def start_coordinate_capture(btn)   # 开始捕获
def capture_global_coordinate(x, y) # 处理捕获的坐标
```

**坐标计算:**
- 屏幕坐标: 直接获取鼠标位置
- 窗口相对坐标: 屏幕坐标 - 窗口左上角坐标

## 关键设计

### 多线程架构

```
主线程 (UI)
  ├── 游戏手柄监听线程 (gamepad_listener)
  └── 摇杆鼠标线程 (stick_mouse_loop) - 仅在鼠标模式时启动
```

### 状态共享

```python
self.last_left_stick_state   # 左摇杆状态
self.last_right_stick_state  # 右摇杆状态
self.mapping_mode            # 映射模式开关
```

### 队列通信

```python
self.highlight_queue  # UI更新队列
```

用于从监听线程向主线程传递按键状态更新。

## 配置系统

### 配置结构

```python
{
    "BTN_SOUTH": {
        "screen_x": "100",    # 屏幕X坐标
        "screen_y": "200",    # 屏幕Y坐标
        "window_x": "50",     # 窗口相对X坐标
        "window_y": "100",    # 窗口相对Y坐标
        "func": "点击"         # 功能类型
    }
}
```

### 功能类型

普通按键:
- `点击`: 单次点击
- `长按`: 持续按下，松开后释放
- `上滑`: 向上滚动
- `下滑`: 向下滚动

摇杆:
- `方向键`: 模拟方向键
- `摇杆`: 模拟摇杆移动
- `鼠标`: 控制鼠标

## 摇杆算法

### 鼠标模式算法

```python
# 1. 计算向量长度
stick_length = sqrt(x^2 + y^2)

# 2. 死区处理（15%）
if stick_length < 0.15: return

# 3. 归一化方向
x_dir = x / stick_length
y_dir = y / stick_length

# 4. 计算输入量（0-1）
input_amount = (stick_length - 0.15) / 0.85

# 5. 计算速度（最大8像素/帧）
speed = input_amount * 8

# 6. 计算移动量
move_x = x_dir * speed
move_y = y_dir * speed
```

### 方向判断算法

```python
if abs(x) > abs(y):
    # 水平方向
    direction = "右" if x > 0.5 else "左" if x < -0.5 else None
else:
    # 垂直方向
    direction = "下" if y > 0.5 else "上" if y < -0.5 else None
```

## 开发注意事项

### 1. Windows API

- 使用 `SendInput` 代替过时的 `mouse_event`
- 绝对坐标需要转换为 0-65535 范围
- 需要管理员权限才能模拟输入

### 2. 线程安全

- UI更新必须通过 `self.after()` 在主线程执行
- 共享状态使用原子操作或简单赋值（Python GIL保证）
- 异常处理避免阻塞线程

### 3. 性能优化

- 使用内存中的配置，避免频繁文件IO
- 摇杆鼠标使用独立线程，避免事件循环阻塞
- 循环中使用 `time.sleep(0.005)` 降低CPU占用

### 4. 坐标系统

- 屏幕坐标: 左上角为原点，向下Y增加
- 摇杆坐标: 向上Y为负值，需要取反

## 扩展开发

### 添加新功能类型

1. 在功能选择下拉框中添加新选项
2. 在 `execute_touch()` 中添加处理逻辑
3. 更新配置文件读取逻辑

### 添加新手柄支持

1. 在 `BUTTONS` 列表中添加新按键代码
2. 在 `BUTTON_NAMES` 中添加显示名称
3. 在 `parse_event()` 中添加事件解析

### 添加新摇杆模式

1. 在摇杆模式选择中添加选项
2. 在 `process_stick_action()` 中添加处理分支
3. 实现对应的处理函数

## 调试技巧

### 查看手柄事件

```python
# 在 gamepad_listener 中添加
print(f"Event: {event.code} = {event.state}")
```

### 测试鼠标移动

```python
# 在 handle_stick_as_mouse 中添加
print(f"Move: ({move_x}, {move_y})")
```

### 验证坐标

```python
# 在 execute_touch 中添加
print(f"Target: ({x}, {y})")
```

## 常见问题

### 手柄无法识别

- 检查手柄驱动是否正确安装
- 尝试重新插拔手柄
- 使用其他程序测试手柄是否正常

### 鼠标移动不流畅

- 检查死区设置是否合适
- 调整 `max_speed` 参数
- 确认独立线程正常运行

### 坐标偏移

- 检查窗口缩放比例（DPI设置）
- 验证窗口标题是否正确
- 确认窗口未被最小化
