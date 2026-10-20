"""独立进程显示成功提示；Linux 使用系统通知，无需 Tkinter。"""
import os
from pathlib import Path
import subprocess
import sys


def show_success_popup(model, count, machine_id):
    return show_notification('AutoDL 抢卡成功',
                             f'已抢到 {count} 张 {model}\n机器 ID：{machine_id}\n抢卡程序已停止。')


def show_notification(title, message):
    if sys.platform.startswith('linux') and not (
        os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')
    ):
        print('当前没有桌面显示环境，无法发送系统通知；请查看终端的购买成功信息。')
        return False
    if sys.platform.startswith('linux'):
        command = ['notify-send', '--urgency=critical', '--app-name=AutoDL',
                   title, message]
    else:
        command = [sys.executable, str(Path(__file__).resolve()), message, title]
    try:
        subprocess.Popen(command, start_new_session=True)
        return True
    except FileNotFoundError:
        print('无法发送系统通知：未安装 notify-send（Ubuntu/Debian：sudo apt install libnotify-bin）。')
        return False
    except Exception as exc:
        print(f'启动成功提示失败: {exc}')
        return False


def main():
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        try:
            root.bell()
            messagebox.showinfo(sys.argv[2], sys.argv[1], parent=root)
        finally:
            root.destroy()
    except Exception as exc:
        print(f'无法显示抢卡成功弹窗: {exc}。请确认有桌面环境并已安装 Tkinter。')


if __name__ == '__main__':
    main()
