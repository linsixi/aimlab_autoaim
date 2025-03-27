import ctypes
import cv2
import numpy as np
import win32gui
from mss import mss
import tkinter as tk

# 调用驱动
driver = ctypes.CDLL(r'lib/MouseControl.dll')

# 定义全局变量
controlling_mouse = False
WINDOW_TITLE = "aimlab_tb"  # 替换为你的窗口标题
aimlab_tb_hwnd = None  # 存储aimlab_tb窗口句柄
middle_left = 0  # 中间区域坐标
middle_top = 0  # 中间区域坐标


class BoxInfo:
    def __init__(self, box, distance):
        self.box = box
        self.distance = distance


def capture_screen(window_title, region_width=415, region_height=410):
    global aimlab_tb_hwnd, middle_left, middle_top
    if aimlab_tb_hwnd is None:
        aimlab_tb_hwnd = win32gui.FindWindow(None, window_title)
        if aimlab_tb_hwnd == 0:
            print("No window found")
            return None

    # 获取窗口的客户区域大小
    left, top, right, bottom = win32gui.GetClientRect(aimlab_tb_hwnd)
    client_width = right - left
    client_height = bottom - top

    # 计算中间区域的坐标
    middle_left = client_width // 2 - region_width // 2
    middle_top = client_height // 2 - region_height // 2

    # 将客户区域的左上角坐标转换为屏幕坐标
    client_left, client_top = win32gui.ClientToScreen(aimlab_tb_hwnd, (middle_left, middle_top))

    # 使用 mss 截取指定区域
    with mss() as sct:
        monitor = {"left": client_left, "top": client_top, "width": region_width, "height": region_height}
        img = sct.grab(monitor)  # 截取屏幕区域
        frame = np.array(img)  # 转换为 numpy 数组
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)  # 转换为 BGR 格式
        return frame


def detect_ball(frame):
    # 定义小球的 HSV 范围
    lower_color = np.array([85, 210, 80])
    upper_color = np.array([95, 245, 255])

    # 转换到 HSV 空间
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # 根据颜色范围创建掩码
    mask = cv2.inRange(hsv, lower_color, upper_color)

    # 查找轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 直接在循环中计算最近的框体，避免额外的列表操作
    closest_box_info = None
    closest_distance = float('inf')
    screen_center_x = frame.shape[1] // 2
    screen_center_y = frame.shape[0] // 2

    for contour in contours:
        # 获取轮廓的边界框
        x, y, w, h = cv2.boundingRect(contour)
        center_x = (x + x + w) // 2
        center_y = (y + y + h) // 2
        distance = ((center_x - screen_center_x) ** 2 + (center_y - screen_center_y) ** 2) ** 0.5

        if distance < closest_distance:
            closest_box_info = BoxInfo((x, y, x + w, y + h), distance)
            closest_distance = distance

    # 绘制检测到的方框
    if closest_box_info:
        cv2.rectangle(frame, (closest_box_info.box[0], closest_box_info.box[1]),
                      (closest_box_info.box[2], closest_box_info.box[3]), (0, 255, 0), 1)  # 修改线宽为1

    return closest_box_info


def run_detection():
    global controlling_mouse

    while controlling_mouse:
        frame = capture_screen(WINDOW_TITLE)
        if frame is None:
            continue

        # 检测小球
        closest_box_info = detect_ball(frame)
        threshold = 0  # 初始值
        if closest_box_info:
            # 计算从屏幕中心到最近框体中心的向量
            target_x_frame = (closest_box_info.box[0] + closest_box_info.box[2]) // 2
            target_y_frame = (closest_box_info.box[1] + closest_box_info.box[3]) // 2
            vector_x = target_x_frame - frame.shape[1] // 2
            vector_y = target_y_frame - frame.shape[0] // 2

            # 设置一个阈值，当鼠标与目标的距离小于该阈值时，停止移动
            threshold = 14  # 设置阈值，越小越准，越慢

        # 绘制阈值框的范围
        if closest_box_info:
            target_x_frame = (closest_box_info.box[0] + closest_box_info.box[2]) // 2
            target_y_frame = (closest_box_info.box[1] + closest_box_info.box[3]) // 2
            threshold_box_size = threshold * 2
            cv2.rectangle(frame, (target_x_frame - threshold_box_size // 2, target_y_frame - threshold_box_size // 2),
                          (target_x_frame + threshold_box_size // 2, target_y_frame + threshold_box_size // 2),
                          (0, 0, 255), 1)  # 修改线宽为1

        # 显示图像
        cv2.imshow('Detected Frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()


def start_detection():
    global controlling_mouse
    controlling_mouse = True
    run_detection()  # 直接在主线程中运行检测逻辑


def stop_detection():
    global controlling_mouse
    controlling_mouse = False


def exit_program():
    global controlling_mouse
    controlling_mouse = False
    cv2.destroyAllWindows()
    root.quit()


if __name__ == "__main__":
    # 创建主窗口并设置窗口标题
    root = tk.Tk()
    root.title("Control Window")

    # 创建并放置开始检测按钮
    start_button = tk.Button(root, text="Start Detection", command=start_detection)
    start_button.pack(pady=10)

    # 创建并放置停止控制按钮
    stop_button = tk.Button(root, text="Stop Control", command=stop_detection)
    stop_button.pack(pady=10)

    # 创建并放置退出程序按钮
    exit_button = tk.Button(root, text="Exit Program", command=exit_program)
    exit_button.pack(pady=10)

    # 进入Tkinter事件主循环
    root.mainloop()

    # 程序退出前打印信息
    print("Exiting...")
