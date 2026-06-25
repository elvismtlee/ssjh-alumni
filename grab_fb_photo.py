"""獨立執行：帶 Edge Facebook 視窗到最前，截圖，裁切照片區域"""
import time, win32gui, win32con, ctypes
from PIL import ImageGrab, Image

def find_fb_hwnd():
    wins = []
    def cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            try:
                title = win32gui.GetWindowText(hwnd)
                if 'Facebook' in title:
                    wins.append((hwnd, title))
            except: pass
    win32gui.EnumWindows(cb, None)
    return wins

time.sleep(2)

wins = find_fb_hwnd()
print(f'Facebook 視窗: {len(wins)}')
for hwnd, title in wins:
    print(f'  {hwnd}: {title[:60]}')

if not wins:
    print('找不到 Facebook 視窗')
    exit(1)

# 取第一個 Facebook 視窗
hwnd = wins[0][0]
ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
time.sleep(1)
ctypes.windll.user32.SetForegroundWindow(hwnd)
time.sleep(3)

# 截整個螢幕
screen = ImageGrab.grab()
screen.save(r'C:\Users\elvis\ssjh-alumni\images\screen_detached.png')
print(f'全螢幕截圖完成: {screen.size}')

# 抓視窗矩形做精準裁切
rect = win32gui.GetWindowRect(hwnd)
x1, y1, x2, y2 = rect
print(f'Edge 視窗位置: {rect}')

# 截視窗範圍
win_shot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
win_shot.save(r'C:\Users\elvis\ssjh-alumni\images\edge_window.png')
print('視窗截圖完成')
