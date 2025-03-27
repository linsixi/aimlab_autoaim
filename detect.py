import cv2
import numpy as np
import win32gui
from mss import mss

# 定义颜色过滤的参数
lower_color = np.array([85, 210, 80])
upper_color = np.array([95, 245, 255])

# 定义滑块回调函数
def update_lower_hue(val):
    lower_color[0] = val
    print(f"Lower Hue: {val}")

def update_lower_sat(val):
    lower_color[1] = val
    print(f"Lower Saturation: {val}")

def update_lower_val(val):
    lower_color[2] = val
    print(f"Lower Value: {val}")

def update_upper_hue(val):
    upper_color[0] = val
    print(f"Upper Hue: {val}")

def update_upper_sat(val):
    upper_color[1] = val
    print(f"Upper Saturation: {val}")

def update_upper_val(val):
    upper_color[2] = val
    print(f"Upper Value: {val}")

# 创建窗口
cv2.namedWindow('Color Filter')

# 创建滑块
cv2.createTrackbar('Lower Hue', 'Color Filter', 85, 179, update_lower_hue)
cv2.createTrackbar('Lower Saturation', 'Color Filter', 210, 255, update_lower_sat)
cv2.createTrackbar('Lower Value', 'Color Filter', 80, 255, update_lower_val)
cv2.createTrackbar('Upper Hue', 'Color Filter', 95, 179, update_upper_hue)
cv2.createTrackbar('Upper Saturation', 'Color Filter', 245, 255, update_upper_sat)
cv2.createTrackbar('Upper Value', 'Color Filter', 255, 255, update_upper_val)

# 定义截屏函数
def capture_screen(window_title, region_width=800, region_height=800):
    # 查找窗口句柄
    hwnd = win32gui.FindWindow(None, window_title)
    if hwnd == 0:
        print("No window found")
        return None  # 如果没有找到窗口，返回None

    # 获取窗口的客户区域大小
    left, top, right, bottom = win32gui.GetClientRect(hwnd)

    # 计算中间区域的坐标
    middle_left = (right - left) // 2 - region_width // 2
    middle_top = (bottom - top) // 2 - region_height // 2
    middle_right = middle_left + region_width
    middle_bottom = middle_top + region_height

    # 将客户区域的左上角坐标转换为屏幕坐标
    client_left, client_top = win32gui.ClientToScreen(hwnd, (middle_left, middle_top))

    # 将客户区域的右下角坐标转换为屏幕坐标
    client_right, client_bottom = win32gui.ClientToScreen(hwnd, (middle_right, middle_bottom))

    # 使用 mss 截取指定区域
    with mss() as sct:
        monitor = {"left": client_left, "top": client_top, "width": region_width, "height": region_height}
        img = sct.grab(monitor)  # 截取屏幕区域
        frame = np.array(img)  # 转换为 numpy 数组
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)  # 转换为 BGR 格式
        return frame

# 读取截屏区域的图像
# 假设这里已经有一个函数 get_screenshot() 来获取截屏图像
# frame = get_screenshot()
frame = capture_screen("aimlab_tb")  # 使用 capture_screen 函数获取截屏图像

# 主循环，实时截取屏幕并应用颜色过滤
while True:
    frame = capture_screen("aimlab_tb")  # 使用 capture_screen 函数获取截屏图像
    if frame is None:
        break  # 如果没有找到窗口，退出循环

    # 应用颜色过滤
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_color, upper_color)
    result = cv2.bitwise_and(frame, frame, mask=mask)

    # 显示结果
    cv2.imshow('Color Filter', result)

    # 按 'q' 键退出循环
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 释放资源
cv2.destroyAllWindows()